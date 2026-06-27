<<<<<<< HEAD
#!/usr/bin/env python3

from pathlib import Path
import xml.etree.ElementTree as ET

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}

def count_units(xml_path: Path) -> int:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    count = 0
    for ab in root.findall(".//tei:ab", TEI_NS):
        if ab.get("type") == "translation_unit" and ab.get("n"):
            count += 1
    return count

def main():
    base = Path(".")
    latin_total = 0
    english_total = 0

    for chapter in range(1, 14):
        latin_file = base / f"Aeneid {chapter}.xml"
        english_file = base / f"Eneados {chapter}.xml"

        latin_count = count_units(latin_file)
        english_count = count_units(english_file)

        latin_total += latin_count
        english_total += english_count

        print(f"Chapter {chapter}: Aeneid={latin_count} Eneados={english_count}")

    print(f"Total: Aeneid={latin_total} Eneados={english_total}")

if __name__ == "__main__":
=======
#!/usr/bin/env python3

from pathlib import Path
import xml.etree.ElementTree as ET

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}

def count_units(xml_path: Path) -> int:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    count = 0
    for ab in root.findall(".//tei:ab", TEI_NS):
        if ab.get("type") == "translation_unit" and ab.get("n"):
            count += 1
    return count

def main():
    base = Path(".")
    latin_total = 0
    english_total = 0

    for chapter in range(1, 14):
        latin_file = base / f"Aeneid {chapter}.xml"
        english_file = base / f"Eneados {chapter}.xml"

        latin_count = count_units(latin_file)
        english_count = count_units(english_file)

        latin_total += latin_count
        english_total += english_count

        print(f"Chapter {chapter}: Aeneid={latin_count} Eneados={english_count}")

    print(f"Total: Aeneid={latin_total} Eneados={english_total}")

if __name__ == "__main__":
>>>>>>> 118a21e7f4e082dbad786e6a81853d03ec3be22f
    main()