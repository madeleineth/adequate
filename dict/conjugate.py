#!/usr/bin/env python3
"""
Conjugation module for Italian verbs.

Provides a function to generate present and imperfect conjugations for a list of verbs,
using irregular forms from dict/conjugation.csv where available, and generating
regular conjugations otherwise.
"""

import csv
from collections import defaultdict
from pathlib import Path

# -ire verbs that do NOT use the -isc- infix in present tense
NON_ISC_IRE_VERBS = {
    "aprire",
    "avvertire",
    "bollire",
    "coprire",
    "cucire",
    "divertire",
    "dormire",
    "fuggire",
    "offrire",
    "partire",
    "scoprire",
    "seguire",
    "sentire",
    "servire",
    "soffrire",
    "vestire",
    "acconsentire",
    "assentire",
    "convertire",
    "investire",
    "pervertire",
    "rivestire",
    "sovvertire",
}

REFLEXIVE_PRONOUNS = ["mi", "ti", "si", "ci", "vi", "si"]


def _get_stem(infinitive):
    """Get the stem of a verb by removing the -are/-ere/-ire ending."""
    if infinitive.endswith("porsi"):
        return infinitive[:-5] + "pong"
    if infinitive.endswith("dursi"):
        return infinitive[:-5] + "duc"
    if infinitive.endswith("arsi"):
        return infinitive[:-4]
    if infinitive.endswith("ersi"):
        return infinitive[:-4]
    if infinitive.endswith("irsi"):
        return infinitive[:-4]
    if infinitive.endswith(("are", "ere", "ire")):
        return infinitive[:-3]
    if infinitive.endswith("rre"):
        return infinitive[:-3]
    return None


def _apply_are_suffix(stem, suffix):
    """Apply suffix to -are verb stem with orthographic rules."""
    if suffix.startswith(("i", "e")):
        if stem.endswith(("c", "g")):
            return stem + "h" + suffix
        if stem.endswith(("ci", "gi", "gli")):
            return stem[:-1] + suffix
    return stem + suffix


def _get_verb_class(infinitive):
    """Determine the verb class: 'are', 'ere', 'ire', 'ire-isc', 'rre', or None."""
    if infinitive.endswith(("porsi", "dursi")):
        return "rre"
    if infinitive.endswith("arsi"):
        return "are"
    if infinitive.endswith("ersi"):
        return "ere"
    if infinitive.endswith("irsi"):
        base = infinitive[:-2] + "e"
        return "ire" if base in NON_ISC_IRE_VERBS else "ire-isc"
    if infinitive.endswith("are"):
        return "are"
    if infinitive.endswith("ere"):
        return "ere"
    if infinitive.endswith("ire"):
        return "ire" if infinitive in NON_ISC_IRE_VERBS else "ire-isc"
    if infinitive.endswith("rre"):
        return "rre"
    return None


def _is_reflexive(infinitive):
    """Check if verb is reflexive."""
    return infinitive.endswith(("arsi", "ersi", "irsi", "porsi", "dursi"))


def _conjugate_present(infinitive):
    """Generate regular present tense conjugation."""
    verb_class = _get_verb_class(infinitive)
    stem = _get_stem(infinitive)

    if not verb_class or not stem:
        return None

    reflexive = _is_reflexive(infinitive)

    if verb_class == "are":
        s = _apply_are_suffix
        forms = [
            s(stem, "o"),
            s(stem, "i"),
            s(stem, "a"),
            s(stem, "iamo"),
            s(stem, "ate"),
            s(stem, "ano"),
        ]
    elif verb_class == "ere":
        forms = [f"{stem}o", f"{stem}i", f"{stem}e", f"{stem}iamo", f"{stem}ete", f"{stem}ono"]
    elif verb_class == "ire":
        forms = [f"{stem}o", f"{stem}i", f"{stem}e", f"{stem}iamo", f"{stem}ite", f"{stem}ono"]
    elif verb_class == "ire-isc":
        forms = [
            f"{stem}isco",
            f"{stem}isci",
            f"{stem}isce",
            f"{stem}iamo",
            f"{stem}ite",
            f"{stem}iscono",
        ]
    elif verb_class == "rre":
        forms = [f"{stem}o", f"{stem}i", f"{stem}e", f"{stem}iamo", f"{stem}ete", f"{stem}ono"]
    else:
        return None

    if reflexive:
        forms = [f"{pron} {form}" for pron, form in zip(REFLEXIVE_PRONOUNS, forms)]

    return "/".join(forms)


def _conjugate_imperfect(infinitive):
    """Generate regular imperfect tense conjugation."""
    verb_class = _get_verb_class(infinitive)
    stem = _get_stem(infinitive)

    if not verb_class or not stem:
        return None

    reflexive = _is_reflexive(infinitive)

    if verb_class == "are":
        forms = [
            f"{stem}avo",
            f"{stem}avi",
            f"{stem}ava",
            f"{stem}avamo",
            f"{stem}avate",
            f"{stem}avano",
        ]
    elif verb_class in ("ere", "rre"):
        forms = [
            f"{stem}evo",
            f"{stem}evi",
            f"{stem}eva",
            f"{stem}evamo",
            f"{stem}evate",
            f"{stem}evano",
        ]
    elif verb_class in ("ire", "ire-isc"):
        forms = [
            f"{stem}ivo",
            f"{stem}ivi",
            f"{stem}iva",
            f"{stem}ivamo",
            f"{stem}ivate",
            f"{stem}ivano",
        ]
    else:
        return None

    if reflexive:
        forms = [f"{pron} {form}" for pron, form in zip(REFLEXIVE_PRONOUNS, forms)]

    return "/".join(forms)


def _get_base_verb(infinitive):
    """Get the non-reflexive base verb for a reflexive infinitive."""
    if infinitive.endswith("porsi"):
        return infinitive[:-5] + "porre"
    if infinitive.endswith("dursi"):
        return infinitive[:-5] + "durre"
    if infinitive.endswith("arsi"):
        return infinitive[:-2] + "e"
    if infinitive.endswith("ersi"):
        return infinitive[:-2] + "e"
    if infinitive.endswith("irsi"):
        return infinitive[:-2] + "e"
    return infinitive


def _add_reflexive_pronouns(forms):
    """Add reflexive pronouns to conjugated forms."""
    form_list = forms.split("/")
    return "/".join(f"{pron} {form}" for pron, form in zip(REFLEXIVE_PRONOUNS, form_list))


def _load_irregulars(path):
    """Load irregular conjugations from CSV file."""
    conjugations = defaultdict(dict)
    try:
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                conjugations[row["infinitive"]][row["tense"]] = row["forms"]
    except FileNotFoundError:
        pass
    return conjugations


def conjugate_verbs(verbs, irregulars_path=None):
    """
    Generate present and imperfect conjugations for a list of verbs.

    Args:
        verbs: Iterable of verb infinitives
        irregulars_path: Path to irregular conjugations CSV (default: dict/conjugation.csv)

    Returns:
        Dict mapping verb -> {"present": "...", "imperfect": "..."}
    """
    if irregulars_path is None:
        irregulars_path = Path(__file__).parent / "conjugation.csv"

    irregulars = _load_irregulars(irregulars_path)
    result = {}

    for verb in verbs:
        conj = {}
        irr = irregulars.get(verb, {})
        reflexive = _is_reflexive(verb)

        # For reflexive verbs, also check base verb irregulars
        base_irr = {}
        if reflexive:
            base_verb = _get_base_verb(verb)
            base_irr = irregulars.get(base_verb, {})

        # Present tense
        if "present" in irr:
            conj["present"] = irr["present"]
        elif reflexive and "present" in base_irr:
            conj["present"] = _add_reflexive_pronouns(base_irr["present"])
        else:
            forms = _conjugate_present(verb)
            if forms:
                conj["present"] = forms

        # Imperfect tense
        if "imperfect" in irr:
            conj["imperfect"] = irr["imperfect"]
        elif reflexive and "imperfect" in base_irr:
            conj["imperfect"] = _add_reflexive_pronouns(base_irr["imperfect"])
        else:
            forms = _conjugate_imperfect(verb)
            if forms:
                conj["imperfect"] = forms

        if conj:
            result[verb] = conj

    return result
