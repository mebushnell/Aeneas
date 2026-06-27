<<<<<<< HEAD
#!/usr/bin/env python3

from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET

TEI_NS = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI_NS}

def clean_text(text: str) -> str:
    text = " ".join(text.split())
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip()

def text_of_word(elem: ET.Element) -> str:
    return clean_text("".join(elem.itertext()))

def extract_line(line_elem: ET.Element) -> dict:
    line_id = line_elem.get("{http://www.w3.org/XML/1998/namespace}id")
    words = []
    for i, w in enumerate(line_elem.findall(".//tei:w", NS), start=1):
        words.append(
            {
                "id": f"{line_id}::w{i}" if line_id else f"w{i}",
                "text": text_of_word(w),
                "attrs": dict(w.attrib),
            }
        )
    return {
        "xml_id": line_id,
        "display": line_id,
        "words": words,
        "text": clean_text(" ".join(word["text"] for word in words)),
    }

def extract_units(xml_path: Path) -> dict:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    units = {}

    for ab in root.findall(".//tei:ab", NS):
        if ab.get("type") != "translation_unit":
            continue
        n = ab.get("n")
        if not n:
            continue

        lines = [extract_line(line) for line in ab.findall("./tei:l", NS)]
        units[n] = {
            "n": n,
            "unit_id": ab.get("{http://www.w3.org/XML/1998/namespace}id") or f"{xml_path.stem}::ab::{n}",
            "source_file": xml_path.name,
            "lines": lines,
            "text": clean_text(" ".join(line["text"] for line in lines)),
        }

    return units

def main():
    chapter = 1
    base = Path(".")

    latin_file = base / f"Aeneid {chapter}.xml"
    english_file = base / f"Eneados {chapter}.xml"

    if not latin_file.exists():
        raise FileNotFoundError(latin_file)
    if not english_file.exists():
        raise FileNotFoundError(english_file)

    latin_units = extract_units(latin_file)
    english_units = extract_units(english_file)

    common_ns = sorted(set(latin_units) & set(english_units), key=lambda x: int(x) if x.isdigit() else x)

    records = []
    for n in common_ns:
        records.append(
            {
                "chapter": chapter,
                "n": n,
                "A": latin_units[n],
                "B": english_units[n],
                "links": [],
            }
        )

    out = {
        "chapter": chapter,
        "count": len(records),
        "records": records,
    }

    out_path = base / f"chapter_{chapter}.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {len(records)} aligned units to {out_path}")

if __name__ == "__main__":
=======
#!/usr/bin/env python3

from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET

TEI_NS = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI_NS}

def clean_text(text: str) -> str:
    text = " ".join(text.split())
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip()

def text_of_word(elem: ET.Element) -> str:
    return clean_text("".join(elem.itertext()))

def extract_line(line_elem: ET.Element) -> dict:
    line_id = line_elem.get("{http://www.w3.org/XML/1998/namespace}id")
    words = []
    for i, w in enumerate(line_elem.findall(".//tei:w", NS), start=1):
        words.append(
            {
                "id": f"{line_id}::w{i}" if line_id else f"w{i}",
                "text": text_of_word(w),
                "attrs": dict(w.attrib),
            }
        )
    return {
        "xml_id": line_id,
        "display": line_id,
        "words": words,
        "text": clean_text(" ".join(word["text"] for word in words)),
    }

def extract_units(xml_path: Path) -> dict:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    units = {}

    for ab in root.findall(".//tei:ab", NS):
        if ab.get("type") != "translation_unit":
            continue
        n = ab.get("n")
        if not n:
            continue

        lines = [extract_line(line) for line in ab.findall("./tei:l", NS)]
        units[n] = {
            "n": n,
            "unit_id": ab.get("{http://www.w3.org/XML/1998/namespace}id") or f"{xml_path.stem}::ab::{n}",
            "source_file": xml_path.name,
            "lines": lines,
            "text": clean_text(" ".join(line["text"] for line in lines)),
        }

    return units

def main():
    chapter = 1
    base = Path(".")

    latin_file = base / f"Aeneid {chapter}.xml"
    english_file = base / f"Eneados {chapter}.xml"

    if not latin_file.exists():
        raise FileNotFoundError(latin_file)
    if not english_file.exists():
        raise FileNotFoundError(english_file)

    latin_units = extract_units(latin_file)
    english_units = extract_units(english_file)

    common_ns = sorted(set(latin_units) & set(english_units), key=lambda x: int(x) if x.isdigit() else x)

    records = []
    for n in common_ns:
        records.append(
            {
                "chapter": chapter,
                "n": n,
                "A": latin_units[n],
                "B": english_units[n],
                "links": [],
            }
        )

    out = {
        "chapter": chapter,
        "count": len(records),
        "records": records,
    }

    out_path = base / f"chapter_{chapter}.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {len(records)} aligned units to {out_path}")

if __name__ == "__main__":
>>>>>>> 118a21e7f4e082dbad786e6a81853d03ec3be22f
    main()