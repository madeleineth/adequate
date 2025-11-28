#!/usr/bin/env python3

import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

PATH = Path(__file__).parent / "divina-commedia.txt"


def words_exist(words: list[str]) -> set[str]:
    java_home = os.environ.get("JAVA_HOME")
    if java_home is None:
        raise RuntimeError("JAVA_HOME is unset.")
    java = Path(java_home) / "bin/java"
    r = subprocess.run(
        [str(java), "-cp", "cli/build/engita.jar:bin/json.jar", "net.mdln.engita.Main", *words],
        check=True,
        capture_output=True,
        text=True,
    )
    exists: set[str] = set()
    for line in r.stdout.split("\n"):
        if m := re.match(r"^\[(.+)\] (\d+) results$", line):
            word, n = m.group(1), int(m.group(2))
            if n > 0:
                exists.add(word)
    return exists


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(f"Usage: {sys.argv[0]} MIN_N")
    min_n = int(sys.argv[1])
    counts: Counter[str] = Counter()
    with open(PATH, "rt") as f:
        for line in f:
            for m in re.findall(r"\b([a-zàèìòùé']+)\b", line.lower()):
                counts[m] += 1
    maybe = [
        (word, cnt) for word, cnt in sorted(counts.items(), key=lambda x: -x[1]) if cnt >= min_n
    ]
    exists = words_exist([x[0] for x in maybe])
    for word, cnt in maybe:
        if word not in exists:
            print(word, cnt)


if __name__ == "__main__":
    main()
