<<<<<<< HEAD
#!/usr/bin/env python3

from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

TEI_NS = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI_NS}


def clean_text(text: str) -> str:
    text = " ".join(text.split())
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip()


def text_of_word(elem: ET.Element) -> str:
    return clean_text("".join(elem.itertext()))


def compact_dict(data: dict) -> dict:
    return {k: v for k, v in data.items() if v not in (None, "", [], {})}


def extract_word(word_elem: ET.Element, line_id: str | None, part_index: int, word_index: int) -> dict:
    attrs = word_elem.attrib

    word = {
        "id": f"{line_id}::p{part_index}::w{word_index}" if line_id else f"p{part_index}::w{word_index}",
        "t": text_of_word(word_elem),
        "o": attrs.get("orig"),
        "n": attrs.get("norm"),
        "m": attrs.get("mod"),
        "p": attrs.get("pos"),
        "s": attrs.get("sem"),
    }
    return compact_dict(word)


def extract_line(line_elem: ET.Element, part_index: int) -> dict:
    line_id = line_elem.get("{http://www.w3.org/XML/1998/namespace}id")
    words = []

    for i, w in enumerate(line_elem.findall(".//tei:w", NS), start=1):
        words.append(extract_word(w, line_id, part_index, i))

    line_text = clean_text(" ".join(word["t"] for word in words))

    line = {
        "id": line_id,
        "p": part_index,
        "w": words,
        "t": line_text,
    }
    return compact_dict(line)


def extract_unit_fragment(ab: ET.Element, xml_path: Path, fragment_index: int) -> dict:
    n = ab.get("n")
    lines = [extract_line(line, fragment_index) for line in ab.findall(".//tei:l", NS)]

    return {
        "n": n,
        "uid": ab.get("{http://www.w3.org/XML/1998/namespace}id") or f"{xml_path.stem}::ab::{n}::p{fragment_index}",
        "file": xml_path.name,
        "p": fragment_index,
        "l": lines,
        "t": clean_text(" ".join(line["t"] for line in lines)),
    }


def combine_fragments(fragments: list) -> dict:
    fragments = sorted(fragments, key=lambda x: x["p"])

    all_lines = []
    frag_ids = []
    text_parts = []

    for frag in fragments:
        frag_ids.append(frag["uid"])
        all_lines.extend(frag.get("l", []))
        if frag.get("t"):
            text_parts.append(frag["t"])

    first = fragments[0]

    unit = {
        "n": first["n"],
        "uid": first["uid"],
        "f": frag_ids,
        "file": first["file"],
        "l": all_lines,
        "t": clean_text(" ".join(text_parts)),
        "parts": fragments,
    }
    return compact_dict(unit)


def extract_units(xml_path: Path) -> dict:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    grouped = {}
    fragment_index = 0

    for ab in root.findall(".//tei:ab", NS):
        if ab.get("type") != "translation_unit":
            continue

        n = ab.get("n")
        if not n:
            continue

        fragment_index += 1
        fragment = extract_unit_fragment(ab, xml_path, fragment_index)
        grouped.setdefault(n, []).append(fragment)

    combined = {}
    for n, fragments in grouped.items():
        combined[n] = combine_fragments(fragments)

    return combined


def main():
    base = Path(".")
    out_dir = base / "output"
    out_dir.mkdir(exist_ok=True)

    index = {
        "pair_id": "aeneid_eneados",
        "books": [],
        "count": 0,
    }

    for book in range(1, 14):
        latin_file = base / f"Aeneid {book}.xml"
        target_file = base / f"Eneados {book}.xml"

        if not latin_file.exists():
            raise FileNotFoundError(latin_file)
        if not target_file.exists():
            raise FileNotFoundError(target_file)

        latin_units = extract_units(latin_file)
        target_units = extract_units(target_file)

        common_ns = sorted(
            set(latin_units) & set(target_units),
            key=lambda x: int(x) if x.isdigit() else x,
        )

        records = []
        for n in common_ns:
            records.append(
                {
                    "book": book,
                    "n": n,
                    "source": latin_units[n],
                    "target": target_units[n],
                    "links": [],
                }
            )

        book_payload = {
            "pair_id": "aeneid_eneados",
            "book": book,
            "count": len(records),
            "records": records,
        }

        book_path = out_dir / f"book_{book}.json"
        book_path.write_text(
            json.dumps(book_payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

        index["books"].append(
            {
                "book": book,
                "file": book_path.name,
                "count": len(records),
            }
        )
        index["count"] += len(records)

        print(f"Book {book}: {len(records)} aligned units")

    index_path = out_dir / "index.json"
    index_path.write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    print(f"Wrote {index['count']} aligned units across 13 books")
    print(f"Index written to {index_path}")


if __name__ == "__main__":
=======
#!/usr/bin/env python3

from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

TEI_NS = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI_NS}


def clean_text(text: str) -> str:
    text = " ".join(text.split())
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip()


def text_of_word(elem: ET.Element) -> str:
    return clean_text("".join(elem.itertext()))


def extract_word(word_elem: ET.Element, line_id: str | None, part_index: int, word_index: int) -> dict:
    attrs = dict(word_elem.attrib)

    return {
        "id": f"{line_id}::part{part_index}::w{word_index}" if line_id else f"part{part_index}::w{word_index}",
        "text": text_of_word(word_elem),
        "display": text_of_word(word_elem),
        "orig": attrs.get("orig"),
        "norm": attrs.get("norm"),
        "mod": attrs.get("mod"),
        "pos": attrs.get("pos"),
        "sem": attrs.get("sem"),
        "attrs": attrs,
    }


def extract_line(line_elem: ET.Element, part_index: int) -> dict:
    line_id = line_elem.get("{http://www.w3.org/XML/1998/namespace}id")
    words = []

    for i, w in enumerate(line_elem.findall(".//tei:w", NS), start=1):
        words.append(extract_word(w, line_id, part_index, i))

    return {
        "xml_id": line_id,
        "display": line_id,
        "part_index": part_index,
        "words": words,
        "text": clean_text(" ".join(word["text"] for word in words)),
    }


def extract_unit_fragment(ab: ET.Element, xml_path: Path, fragment_index: int) -> dict:
    n = ab.get("n")
    lines = [extract_line(line, fragment_index) for line in ab.findall("./tei:l", NS)]

    return {
        "n": n,
        "fragment_index": fragment_index,
        "unit_id": ab.get("{http://www.w3.org/XML/1998/namespace}id")
        or f"{xml_path.stem}::ab::{n}::part{fragment_index}",
        "source_file": xml_path.name,
        "lines": lines,
        "text": clean_text(" ".join(line["text"] for line in lines)),
    }


def combine_fragments(fragments: list) -> dict:
    fragments = sorted(fragments, key=lambda x: x["fragment_index"])

    all_lines = []
    all_unit_ids = []
    all_text_parts = []

    for frag in fragments:
        all_unit_ids.append(frag["unit_id"])
        all_lines.extend(frag["lines"])
        if frag["text"]:
            all_text_parts.append(frag["text"])

    first = fragments[0]

    return {
        "n": first["n"],
        "unit_id": first["unit_id"],
        "fragment_ids": all_unit_ids,
        "source_file": first["source_file"],
        "lines": all_lines,
        "text": clean_text(" ".join(all_text_parts)),
        "parts": fragments,
    }


def extract_units(xml_path: Path) -> dict:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    grouped = {}
    fragment_index = 0

    for ab in root.findall(".//tei:ab", NS):
        if ab.get("type") != "translation_unit":
            continue

        n = ab.get("n")
        if not n:
            continue

        fragment_index += 1
        fragment = extract_unit_fragment(ab, xml_path, fragment_index)

        if n not in grouped:
            grouped[n] = []

        grouped[n].append(fragment)

    combined = {}
    for n, fragments in grouped.items():
        combined[n] = combine_fragments(fragments)

    return combined


def main():
    base = Path(".")
    out_dir = base / "output"
    out_dir.mkdir(exist_ok=True)

    index = {
        "pair_id": "aeneid_eneados",
        "books": [],
        "count": 0,
    }

    for book in range(1, 14):
        latin_file = base / f"Aeneid {book}.xml"
        english_file = base / f"Eneados {book}.xml"

        if not latin_file.exists():
            raise FileNotFoundError(latin_file)
        if not english_file.exists():
            raise FileNotFoundError(english_file)

        latin_units = extract_units(latin_file)
        english_units = extract_units(english_file)

        common_ns = sorted(
            set(latin_units) & set(english_units),
            key=lambda x: int(x) if x.isdigit() else x,
        )

        records = []
        for n in common_ns:
            records.append(
                {
                    "book": book,
                    "n": n,
                    "A": latin_units[n],
                    "B": english_units[n],
                    "links": [],
                }
            )

        book_payload = {
            "pair_id": "aeneid_eneados",
            "book": book,
            "count": len(records),
            "records": records,
        }

        book_path = out_dir / f"book_{book}.json"
        book_path.write_text(json.dumps(book_payload, ensure_ascii=False, indent=2), encoding="utf-8")

        index["books"].append(
            {
                "book": book,
                "file": book_path.name,
                "count": len(records),
            }
        )
        index["count"] += len(records)

        print(f"Book {book}: {len(records)} aligned units")

    index_path = out_dir / "index.json"
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {index['count']} aligned units across 13 books")
    print(f"Index written to {index_path}")


if __name__ == "__main__":
>>>>>>> 118a21e7f4e082dbad786e6a81853d03ec3be22f
    main()