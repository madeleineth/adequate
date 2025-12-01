import os
import json


def _load_entry(root: str, part: str) -> dict[str, str | dict[str, str]]:
    path = os.environ["DICT_RES"]
    with open(path, "rt") as f:
        for line in f:
            j = json.loads(line)
            if j["r"] == root and j["p"] == part:
                return j  # type: ignore
    raise RuntimeError(f"Could not find entry for {root=} {part=} in '{path}'.")


def test_irregular_condurre_participle() -> None:
    entry = _load_entry("condurre", "v")
    # TODO: Make this a regular JSON list.
    assert entry["c"]["participle"] == "condotto/condotta/condotti/condotte"  # type: ignore
