#!/usr/bin/env python3
"""Convert words.csv into words.js for the browser game (index.html).

Run this after editing words.csv:  python build_words.py
Standard library only.
"""

import csv
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "words.csv")
JS_PATH = os.path.join(BASE_DIR, "words.js")


def main() -> None:
    pairs = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            secret = row["secret"].strip()
            variation = row["variation"].strip()
            if not secret or not variation:
                continue
            aliases = [a.strip() for a in (row.get("aliases") or "").split("|") if a.strip()]
            pairs.append({"secret": secret, "variation": variation, "aliases": aliases})

    with open(JS_PATH, "w", encoding="utf-8") as f:
        f.write("// Generated from words.csv by build_words.py -- do not edit by hand.\n")
        f.write("window.WORD_PAIRS = ")
        f.write(json.dumps(pairs, ensure_ascii=False, indent=1))
        f.write(";\n")
    print(f"Wrote {len(pairs)} pairs to {os.path.basename(JS_PATH)}")


if __name__ == "__main__":
    main()
