<<<<<<< HEAD
#!/usr/bin/env python3
"""
Extract aligned translation units from paired TEI XML files.

Expected filenames:
    Aeneid 1.xml ... Aeneid 13.xml
    Eneados 1.xml ... Eneados 13.xml

Output:
    aligned.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI_NS}


def localname(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def clean_text(text: str) -> str:
    text = " ".join(text.split())
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\s+([)\]])", r"\1", text)
    text = re.sub(r"([([¿¡])\s+", r"\1", text)
    return text.strip()


def word_attrs(elem: ET.Element) -> Dict[str, str]:
    """Return all non-namespace attributes on a <w> element."""
    attrs: Dict[str, str] = {}
    for k, v in elem.attrib.items():
        # Keep xml:id if it exists, though most <w> elements won't have one.
        attrs[k] = v
    return attrs


def text_of_word(elem: ET.Element) -> str:
    """Extract readable text from a <w> element."""
    return clean_text("".join(elem.itertext()))


def build_parent_map(root: ET.Element) -> Dict[ET.Element, ET.Element]:
    parent_map: Dict[ET.Element, ET.Element] = {}
    for parent in root.iter():
        for child in list(parent):
            parent_map[child] = parent
    return parent_map


def ancestor_div_chain(elem: ET.Element, parent_map: Dict[ET.Element, ET.Element]) -> List[dict]:
    chain: List[dict] = []
    current = parent_map.get(elem)
    while current is not None:
        if localname(current.tag) == "div":
            chain.append(
                {
                    "type": current.get("type"),
                    "n": current.get("n"),
                    "xml_id": current.get(f"{{{XML_NS}}}id"),
                }
            )
        current = parent_map.get(current)
    chain.reverse()
    return chain


def extract_line(line_elem: ET.Element) -> dict:
    line_id = line_elem.get(f"{{{XML_NS}}}id")
    words = []
    for i, w in enumerate(line_elem.findall(".//tei:w", NS), start=1):
        words.append(
            {
                "id": f"{line_id}::w{i}" if line_id else f"w{i}",
                "text": text_of_word(w),
                "attrs": word_attrs(w),
            }
        )

    line_text = clean_text(" ".join(w["text"] for w in words))

    return {
        "xml_id": line_id,
        "display": line_id,   # for visible line-number display
        "words": words,
        "text": line_text,    # for search/display
    }


def extract_unit(ab: ET.Element, source_file: Path, parent_map: Dict[ET.Element, ET.Element]) -> dict:
    n = ab.get("n")
    unit_xml_id = ab.get(f"{{{XML_NS}}}id")
    div_chain = ancestor_div_chain(ab, parent_map)

    lines = []
    for line_elem in ab.findall("./tei:l", NS):
        lines.append(extract_line(line_elem))

    unit_text = clean_text(" ".join(line["text"] for line in lines))

    return {
        "n": n,
        "unit_id": unit_xml_id or f"{source_file.stem}::ab::{n}",
        "source_file": source_file.name,
        "div_chain": div_chain,
        "lines": lines,
        "text": unit_text,
    }


def extract_units(xml_path: Path) -> Dict[str, dict]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    parent_map = build_parent_map(root)

    units: Dict[str, dict] = {}

    for ab in root.findall(".//tei:ab", NS):
        if ab.get("type") != "translation_unit":
            continue
        n = ab.get("n")
        if not n:
            continue

        unit = extract_unit(ab, xml_path, parent_map)
        if n in units:
            print(f"Warning: duplicate translation unit n={n} in {xml_path.name}", file=sys.stderr)
        units[n] = unit

    return units


def sort_key(n: str):
    try:
        return (0, int(n))
    except ValueError:
        return (1, n)


def extract_pair(input_dir: Path, chapter: int, latin_prefix: str, english_prefix: str) -> List[dict]:
    latin_path = input_dir / f"{latin_prefix} {chapter}.xml"
    english_path = input_dir / f"{english_prefix} {chapter}.xml"

    if not latin_path.exists():
        raise FileNotFoundError(f"Missing file: {latin_path}")
    if not english_path.exists():
        raise FileNotFoundError(f"Missing file: {english_path}")

    latin_units = extract_units(latin_path)
    english_units = extract_units(english_path)

    common_ns = sorted(set(latin_units) & set(english_units), key=sort_key)

    aligned_records = []
    for n in common_ns:
        aligned_records.append(
            {
                "chapter": chapter,
                "n": n,
                "A": latin_units[n],
                "B": english_units[n],
                "links": [],  # reserved for word-to-word alignment later
            }
        )

    return aligned_records


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract aligned TEI corpus data.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("."),
        help="Folder containing the XML files",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("aligned.json"),
        help="Output JSON file",
    )
    parser.add_argument(
        "--latin-prefix",
        default="Aeneid",
        help='Latin filename prefix (default: "Aeneid")',
    )
    parser.add_argument(
        "--english-prefix",
        default="Eneados",
        help='English filename prefix (default: "Eneados")',
    )
    parser.add_argument(
        "--chapters",
        type=int,
        default=13,
        help="Number of chapter pairs to process (default: 13)",
    )
    args = parser.parse_args()

    all_records = []
    for chapter in range(1, args.chapters + 1):
        print(f"Processing chapter {chapter}...", file=sys.stderr)
        all_records.extend(
            extract_pair(
                args.input_dir,
                chapter,
                args.latin_prefix,
                args.english_prefix,
            )
        )

    payload = {
        "pair_id": f"{args.latin_prefix.lower()}_{args.english_prefix.lower()}",
        "source_a_prefix": args.latin_prefix,
        "source_b_prefix": args.english_prefix,
        "chapters": args.chapters,
        "count": len(all_records),
        "records": all_records,
    }

    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(all_records)} aligned units to {args.out}")


if __name__ == "__main__":
=======
#!/usr/bin/env python3
"""
Extract aligned translation units from paired TEI XML files.

Expected filenames:
    Aeneid 1.xml ... Aeneid 13.xml
    Eneados 1.xml ... Eneados 13.xml

Output:
    aligned.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI_NS}


def localname(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def clean_text(text: str) -> str:
    text = " ".join(text.split())
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\s+([)\]])", r"\1", text)
    text = re.sub(r"([([¿¡])\s+", r"\1", text)
    return text.strip()


def word_attrs(elem: ET.Element) -> Dict[str, str]:
    """Return all non-namespace attributes on a <w> element."""
    attrs: Dict[str, str] = {}
    for k, v in elem.attrib.items():
        # Keep xml:id if it exists, though most <w> elements won't have one.
        attrs[k] = v
    return attrs


def text_of_word(elem: ET.Element) -> str:
    """Extract readable text from a <w> element."""
    return clean_text("".join(elem.itertext()))


def build_parent_map(root: ET.Element) -> Dict[ET.Element, ET.Element]:
    parent_map: Dict[ET.Element, ET.Element] = {}
    for parent in root.iter():
        for child in list(parent):
            parent_map[child] = parent
    return parent_map


def ancestor_div_chain(elem: ET.Element, parent_map: Dict[ET.Element, ET.Element]) -> List[dict]:
    chain: List[dict] = []
    current = parent_map.get(elem)
    while current is not None:
        if localname(current.tag) == "div":
            chain.append(
                {
                    "type": current.get("type"),
                    "n": current.get("n"),
                    "xml_id": current.get(f"{{{XML_NS}}}id"),
                }
            )
        current = parent_map.get(current)
    chain.reverse()
    return chain


def extract_line(line_elem: ET.Element) -> dict:
    line_id = line_elem.get(f"{{{XML_NS}}}id")
    words = []
    for i, w in enumerate(line_elem.findall(".//tei:w", NS), start=1):
        words.append(
            {
                "id": f"{line_id}::w{i}" if line_id else f"w{i}",
                "text": text_of_word(w),
                "attrs": word_attrs(w),
            }
        )

    line_text = clean_text(" ".join(w["text"] for w in words))

    return {
        "xml_id": line_id,
        "display": line_id,   # for visible line-number display
        "words": words,
        "text": line_text,    # for search/display
    }


def extract_unit(ab: ET.Element, source_file: Path, parent_map: Dict[ET.Element, ET.Element]) -> dict:
    n = ab.get("n")
    unit_xml_id = ab.get(f"{{{XML_NS}}}id")
    div_chain = ancestor_div_chain(ab, parent_map)

    lines = []
    for line_elem in ab.findall("./tei:l", NS):
        lines.append(extract_line(line_elem))

    unit_text = clean_text(" ".join(line["text"] for line in lines))

    return {
        "n": n,
        "unit_id": unit_xml_id or f"{source_file.stem}::ab::{n}",
        "source_file": source_file.name,
        "div_chain": div_chain,
        "lines": lines,
        "text": unit_text,
    }


def extract_units(xml_path: Path) -> Dict[str, dict]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    parent_map = build_parent_map(root)

    units: Dict[str, dict] = {}

    for ab in root.findall(".//tei:ab", NS):
        if ab.get("type") != "translation_unit":
            continue
        n = ab.get("n")
        if not n:
            continue

        unit = extract_unit(ab, xml_path, parent_map)
        if n in units:
            print(f"Warning: duplicate translation unit n={n} in {xml_path.name}", file=sys.stderr)
        units[n] = unit

    return units


def sort_key(n: str):
    try:
        return (0, int(n))
    except ValueError:
        return (1, n)


def extract_pair(input_dir: Path, chapter: int, latin_prefix: str, english_prefix: str) -> List[dict]:
    latin_path = input_dir / f"{latin_prefix} {chapter}.xml"
    english_path = input_dir / f"{english_prefix} {chapter}.xml"

    if not latin_path.exists():
        raise FileNotFoundError(f"Missing file: {latin_path}")
    if not english_path.exists():
        raise FileNotFoundError(f"Missing file: {english_path}")

    latin_units = extract_units(latin_path)
    english_units = extract_units(english_path)

    common_ns = sorted(set(latin_units) & set(english_units), key=sort_key)

    aligned_records = []
    for n in common_ns:
        aligned_records.append(
            {
                "chapter": chapter,
                "n": n,
                "A": latin_units[n],
                "B": english_units[n],
                "links": [],  # reserved for word-to-word alignment later
            }
        )

    return aligned_records


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract aligned TEI corpus data.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("."),
        help="Folder containing the XML files",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("aligned.json"),
        help="Output JSON file",
    )
    parser.add_argument(
        "--latin-prefix",
        default="Aeneid",
        help='Latin filename prefix (default: "Aeneid")',
    )
    parser.add_argument(
        "--english-prefix",
        default="Eneados",
        help='English filename prefix (default: "Eneados")',
    )
    parser.add_argument(
        "--chapters",
        type=int,
        default=13,
        help="Number of chapter pairs to process (default: 13)",
    )
    args = parser.parse_args()

    all_records = []
    for chapter in range(1, args.chapters + 1):
        print(f"Processing chapter {chapter}...", file=sys.stderr)
        all_records.extend(
            extract_pair(
                args.input_dir,
                chapter,
                args.latin_prefix,
                args.english_prefix,
            )
        )

    payload = {
        "pair_id": f"{args.latin_prefix.lower()}_{args.english_prefix.lower()}",
        "source_a_prefix": args.latin_prefix,
        "source_b_prefix": args.english_prefix,
        "chapters": args.chapters,
        "count": len(all_records),
        "records": all_records,
    }

    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(all_records)} aligned units to {args.out}")


if __name__ == "__main__":
>>>>>>> 118a21e7f4e082dbad786e6a81853d03ec3be22f
    main()