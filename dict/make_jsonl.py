#!/usr/bin/env python3
"""Create dictionary .jsonl from annotated word entries and exception data."""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from typing import cast

from conjugate import SimpleTense, conjugate_as_regular

VALID_POS = {
    "adj",
    "adv",
    "art",
    "conj",
    "int",
    "n",
    "other",
    "particle",
    "prep",
    "prep art",
    "pron",
    "unknown",
    "v",
}

# maps (root, pos) -> (forms, translations)
EntryDict = dict[tuple[str, str], tuple[str, str]]

OutputRecord = dict[str, str | dict[str, str]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("annotated", nargs="+", help="outputs from annotate_wiki_json.py")
    parser.add_argument(
        "--modifications",
        required=True,
        help="modifications in same format output by annotate_wiki_json.py",
    )
    parser.add_argument("--deletions", required=True, help="deletions as csv with columns root,pos")
    parser.add_argument(
        "--irregular-verbs",
        required=True,
        help="irregular verbs csv with columns infinitive,simple_tense,form/form/...",
    )
    parser.add_argument("--output")
    parser.add_argument(
        "--min-count",
        type=int,
        default=2,
        help="minimum occurrences in annotations for a (root, pos) to be included",
    )
    return parser.parse_args()


def load_annotated_files(paths: list[str], min_count: int) -> EntryDict:
    """
    See `annotate_wiki_json.py` for input format. The output list is of (root,
    forms, pos, translations), the same as the modifications file.
    """
    entries: Counter[str] = Counter()
    for path in paths:
        with open(path, "rt") as f:
            entries.update([line.strip() for line in f])
    # Drop infrequent entries and old header lines.
    keep = [k for k, v in entries.items() if v >= min_count and not k.startswith("word,root,")]
    forms: dict[tuple[str, str], set[tuple[str, str, str]]] = defaultdict(set)
    translations: dict[tuple[str, str], set[str]] = defaultdict(set)
    for entry in keep:
        columns = entry.split(",")
        word, root, pos, gender, number, tense, person, translation = columns
        forms[(root, pos)].add((gender, number, word))
        translations[(root, pos)].add(translation)
    canonical_forms = {}
    canonical_translations = {}
    for root_pos, form_set in forms.items():
        canonical_forms[root_pos] = "/".join(x[2] for x in sorted(form_set, key=form_key))
        canonical_translations[root_pos] = "/".join(sorted(translations[root_pos]))
    return {
        root_pos: (f, canonical_translations[root_pos]) for root_pos, f in canonical_forms.items()
    }


def load_modifications(path: str) -> EntryDict:
    """Returns a map of (root, pos) -> (forms, translations)."""
    with open(path, "rt") as f:
        rows = [line.strip().split(",") for line in f]
    r: EntryDict = {}
    for row in rows:
        if len(row) != 5 or row[2] not in VALID_POS:
            raise RuntimeError(f"Invalid modifications row: {row}.")
        k, v = (row[0], row[2]), (row[1], row[3])
        if k in r:
            raise RuntimeError(f"Duplicate modifications for (root, pos) {k}: {v} and {r[k]}.")
        r[k] = v
    return r


def load_deletions(path: str) -> list[tuple[str, str]]:
    """Returns tuples of (root, pos)."""
    with open(path, "rt") as f:
        rows = [cast(tuple[str, str], tuple(line.strip().split(","))) for line in f]
    for row in rows:
        if len(row) != 2 or row[1] not in VALID_POS:
            raise RuntimeError(f"Invalid deletions row of length {len(row)}: {row}.")
    return rows


def should_exclude(root: str, pos: str) -> bool:
    if pos in ("other", "unknown", "num", "part"):
        return True
    if pos not in VALID_POS:
        raise RuntimeError(f"Invalid POS '{pos}' found with '{root}'.")
    if not re.match("^[a-zàèìòùé']+", root):
        return True
    return False


def conjugate_verbs(
    entries: EntryDict, irregular_verbs_path: str
) -> dict[str, dict[SimpleTense, list[str]]]:
    verbs = [root for (root, pos) in entries.keys() if pos == "v"]
    print(f"Generating conjugations for {len(verbs)} verbs...", file=sys.stderr)
    conjugations = {v: conjugate_as_regular(v) for v in verbs}
    with open(irregular_verbs_path, "rt") as irr:
        for line in irr:
            inf, tense_str, forms_str = line.strip().split(",")
            tense = SimpleTense[tense_str.upper()]
            forms = forms_str.split("/")
            if (inf, "v") not in entries:
                print(f"WARNING: Irregular forms found for missing verb {inf}.", file=sys.stderr)
            if inf not in conjugations:
                conjugations[inf] = {}
            conjugations[inf][tense] = forms
    for v in conjugations:
        for t in conjugations[v]:
            n = len(conjugations[v][t])
            e = 1 if t == SimpleTense.GERUND else 4 if t == SimpleTense.PARTICIPLE else 6
            if n != e:
                raise RuntimeError(f"Expected {e} forms for {t} of {v} but got {n}.")
    return conjugations


def form_key(x: tuple[str, str, str]) -> int:
    """Sort key for nouns and adjectives, [m. sg., f. sg., m. pl., f. pl., everything else]."""
    gender, number, _ = x
    return -((number == "sg") * 10 + (gender == "m"))


def main() -> None:
    args = parse_args()

    # Load data.
    entries = load_annotated_files(args.annotated, args.min_count)
    print(f"Loaded {len(entries)} unique (root, pos) entries.", file=sys.stderr)
    modifications = load_modifications(args.modifications)
    print(f"Loaded {len(modifications)} modifications.", file=sys.stderr)
    deletions = load_deletions(args.deletions)
    print(f"Loaded {len(deletions)} deletions.", file=sys.stderr)

    # Merge data sources.
    entries.update(modifications)
    for k in deletions:
        entries.pop(k, None)
    entries = {k: v for k, v in entries.items() if not should_exclude(k[0], k[1])}
    conjugations = conjugate_verbs(entries, args.irregular_verbs)
    print(f"After filtering and modifications, {len(entries)} entries remain.", file=sys.stderr)

    # Generate and write output records.
    records: list[OutputRecord] = []
    for (root, pos), data in entries.items():
        record: OutputRecord = {"r": root, "f": data[0], "p": pos, "t": data[1]}
        if pos == "v":
            record["c"] = {t.name.lower(): "/".join(f) for t, f in conjugations[root].items()}
        records.append(record)
    records.sort(key=lambda r: (r["r"], r["p"]))
    with open(args.output, "wt") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Wrote {args.output}.", file=sys.stderr)


if __name__ == "__main__":
    main()
