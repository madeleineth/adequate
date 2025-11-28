#!/usr/bin/env python3
"""
Create dictionary JSONL from annotated word entries.

Reads annotated CSV files, applies edits from dictionary-modify.csv and
dictionary-delete.csv, generates conjugations for verbs, and outputs JSONL.
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from conjugate import conjugate_verbs

VALID_POS = {
    "n",
    "v",
    "adj",
    "adv",
    "art",
    "prep",
    "conj",
    "prep art",
    "pron",
    "particle",
    "int",
    "other",
    "unknown",
}


def load_annotated_files(paths, min_count=1):
    """
    Load annotated CSV files and group by (root, pos).

    Args:
        paths: List of paths to annotated CSV files
        min_count: Minimum occurrences for a (root, pos) to be included

    Returns:
        dict mapping (root, pos) -> {"forms": set, "translations": set}
    """
    entries = defaultdict(lambda: {"forms": set(), "translations": set(), "count": 0})

    for path in paths:
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                root_raw = row["root"].strip()
                word_raw = row["word"].strip()
                pos = row["pos"].strip()
                translation = row["translation"].strip()

                # Skip invalid entries
                if not root_raw or pos not in VALID_POS:
                    continue
                # Skip proper nouns (entries with capital letters)
                if any(c.isupper() for c in root_raw) or any(c.isupper() for c in word_raw):
                    continue

                root = root_raw.lower()
                word = word_raw.lower()

                key = (root, pos)
                entries[key]["count"] += 1

                # Collect forms (skip for verbs)
                if pos != "v" and word:
                    entries[key]["forms"].add(word)

                # Collect translations
                if translation and translation != "unknown":
                    entries[key]["translations"].add(translation)

    # Filter by min_count
    if min_count > 1:
        entries = {k: v for k, v in entries.items() if v["count"] >= min_count}

    return entries


def load_modifications(path):
    """Load dictionary-modify.csv."""
    modifications = {}
    if not path.exists():
        return modifications

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, fieldnames=["root", "forms", "pos", "definition", "count"])
        for row in reader:
            key = (row["root"].strip(), row["pos"].strip())
            modifications[key] = {
                "forms": set(row["forms"].split("/")) if row["forms"] else set(),
                "translations": set(row["definition"].split("/")) if row["definition"] else set(),
            }
    return modifications


def load_deletions(path):
    """Load dictionary-delete.csv."""
    deletions = set()
    if not path.exists():
        return deletions

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, fieldnames=["root", "pos"])
        for row in reader:
            deletions.add((row["root"].strip(), row["pos"].strip()))
    return deletions


def sort_forms(forms):
    """Sort forms: masculine before feminine, singular before plural, then alphabetically."""
    # Simple alphabetical sort for now - proper gender/number sorting would require
    # tracking that metadata through the pipeline
    return sorted(forms)


def should_exclude(root, pos):
    """Check if entry should be excluded from output."""
    if root.isdigit():
        return True
    if pos in ("other", "unknown"):
        return True
    return False


def make_jsonl(annotated_paths, modify_path, delete_path, output_path, min_count=1):
    """Main function to create JSONL dictionary."""
    print(f"Loading {len(annotated_paths)} annotated file(s)...", file=sys.stderr)
    entries = load_annotated_files(annotated_paths, min_count)
    print(
        f"  Found {len(entries)} unique (root, pos) entries (min_count={min_count})",
        file=sys.stderr,
    )

    print("Loading modifications...", file=sys.stderr)
    modifications = load_modifications(modify_path)
    print(f"  Found {len(modifications)} modifications", file=sys.stderr)

    print("Loading deletions...", file=sys.stderr)
    deletions = load_deletions(delete_path)
    print(f"  Found {len(deletions)} deletions", file=sys.stderr)

    # Apply modifications (update existing or add new)
    for key, mod in modifications.items():
        if key in entries:
            # Update existing: replace forms and translations entirely
            entries[key] = mod
        else:
            # Add new entry
            entries[key] = mod

    # Apply deletions
    for key in deletions:
        entries.pop(key, None)

    # Filter excluded entries
    filtered = {k: v for k, v in entries.items() if not should_exclude(k[0], k[1])}
    print(f"After filtering: {len(filtered)} entries", file=sys.stderr)

    # Collect all verbs for conjugation
    verbs = [root for (root, pos) in filtered.keys() if pos == "v"]
    print(f"Generating conjugations for {len(verbs)} verbs...", file=sys.stderr)
    conjugations = conjugate_verbs(verbs)

    # Build output records
    records = []
    for (root, pos), data in filtered.items():
        record = {
            "r": root,
            "f": "/".join(sort_forms(data["forms"])),
            "p": pos,
            "t": "/".join(sorted(data["translations"])),
        }

        # Add conjugations for verbs
        if pos == "v" and root in conjugations:
            record["c"] = conjugations[root]

        records.append(record)

    # Sort by root, then pos
    records.sort(key=lambda r: (r["r"], r["p"]))

    # Write JSONL
    print(f"Writing {len(records)} entries to {output_path}...", file=sys.stderr)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("Done!", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Create dictionary JSONL from annotated entries")
    parser.add_argument(
        "annotated_files",
        nargs="+",
        help="Input annotated CSV file(s)",
    )
    parser.add_argument(
        "--modify",
        default="dict/dictionary-modify.csv",
        help="Path to modifications CSV (default: dict/dictionary-modify.csv)",
    )
    parser.add_argument(
        "--delete",
        default="dict/dictionary-delete.csv",
        help="Path to deletions CSV (default: dict/dictionary-delete.csv)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="dict/dictionary.jsonl",
        help="Output JSONL file (default: dict/dictionary.jsonl)",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=2,
        help="Minimum occurrences for a (root, pos) to be included (default: 2)",
    )

    args = parser.parse_args()

    # Validate input files exist
    annotated_paths = []
    for path in args.annotated_files:
        p = Path(path)
        if not p.exists():
            print(f"Error: Input file '{p}' not found", file=sys.stderr)
            return 1
        annotated_paths.append(p)

    modify_path = Path(args.modify)
    delete_path = Path(args.delete)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    make_jsonl(annotated_paths, modify_path, delete_path, output_path, args.min_count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
