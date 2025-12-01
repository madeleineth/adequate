#!/usr/bin/env python3

"""Generate regular forms of verbs and patch with irregular forms."""

from enum import Enum

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


class VerbClass(Enum):
    ARE = 0
    ERE = 1
    IRE = 2
    ISC = 3
    RRE = 4


ARE, ERE, IRE, ISC, RRE = VerbClass.ARE, VerbClass.ERE, VerbClass.IRE, VerbClass.ISC, VerbClass.RRE


class SimpleTense(Enum):
    """Tracks Java net.mdln.engita.Term.SimpleTense."""

    PRESENT = 0
    IMPERFECT = 1
    PASSATO_REMOTO = 2
    FUTURE = 3
    CONDITIONAL = 4
    GERUND = 5
    PARTICIPLE = 6


def _get_present_stem(infinitive: str) -> str:
    """Get the stem of a verb by removing the -Xre/-rre/-Xrsi ending."""
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
    raise ValueError(f"Can't find stem of '{infinitive}'.")


def _apply_are_suffix(stem: str, suffix: str) -> str:
    if suffix.startswith(("i", "e")):
        if stem.endswith(("c", "g")):
            return stem + "h" + suffix
        if stem.endswith(("ci", "gi", "gli")):
            return stem[:-1] + suffix
    return stem + suffix


def _get_verb_class(infinitive: str) -> VerbClass:
    """Determine the verb class: 'are', 'ere', 'ire', 'ire-isc', 'rre'."""
    if infinitive.endswith(("porsi", "dursi")):
        return RRE
    if infinitive.endswith("arsi"):
        return ARE
    if infinitive.endswith("ersi"):
        return ERE
    if infinitive.endswith("irsi"):
        base = infinitive[:-2] + "e"
        return IRE if base in NON_ISC_IRE_VERBS else ISC
    if infinitive.endswith("are"):
        return ARE
    if infinitive.endswith("ere"):
        return ERE
    if infinitive.endswith("ire"):
        return IRE if infinitive in NON_ISC_IRE_VERBS else ISC
    if infinitive.endswith("rre"):
        return RRE
    raise ValueError(f"Can't find verb class of '{infinitive}'.")


def _is_reflexive(infinitive: str) -> bool:
    return infinitive.endswith(("arsi", "ersi", "irsi", "porsi", "dursi"))


def _conjugate_present(infinitive: str) -> list[str]:
    """Generate regular present tense conjugation."""
    verb_class = _get_verb_class(infinitive)
    stem = _get_present_stem(infinitive)
    if verb_class == ARE:
        forms = [
            _apply_are_suffix(stem, "o"),
            _apply_are_suffix(stem, "i"),
            _apply_are_suffix(stem, "a"),
            _apply_are_suffix(stem, "iamo"),
            _apply_are_suffix(stem, "ate"),
            _apply_are_suffix(stem, "ano"),
        ]
    elif verb_class in (ERE, RRE):
        forms = [f"{stem}o", f"{stem}i", f"{stem}e", f"{stem}iamo", f"{stem}ete", f"{stem}ono"]
    elif verb_class == IRE:
        forms = [f"{stem}o", f"{stem}i", f"{stem}e", f"{stem}iamo", f"{stem}ite", f"{stem}ono"]
    elif verb_class == ISC:
        forms = [
            f"{stem}isco",
            f"{stem}isci",
            f"{stem}isce",
            f"{stem}iamo",
            f"{stem}ite",
            f"{stem}iscono",
        ]
    else:
        raise AssertionError(f"Impossible verb class '{verb_class}'.")
    return forms


def _conjugate_imperfect(infinitive: str) -> list[str]:
    verb_class = _get_verb_class(infinitive)
    stem = _get_present_stem(infinitive)
    if verb_class == ARE:
        forms = [
            f"{stem}avo",
            f"{stem}avi",
            f"{stem}ava",
            f"{stem}avamo",
            f"{stem}avate",
            f"{stem}avano",
        ]
    elif verb_class in (ERE, RRE):
        forms = [
            f"{stem}evo",
            f"{stem}evi",
            f"{stem}eva",
            f"{stem}evamo",
            f"{stem}evate",
            f"{stem}evano",
        ]
    elif verb_class in (IRE, ISC):
        forms = [
            f"{stem}ivo",
            f"{stem}ivi",
            f"{stem}iva",
            f"{stem}ivamo",
            f"{stem}ivate",
            f"{stem}ivano",
        ]
    else:
        raise AssertionError(f"Impossible verb class '{verb_class}'.")
    return forms


def _conjugate_gerund(infinitive: str) -> str:
    verb_class = _get_verb_class(infinitive)
    stem = _get_present_stem(infinitive)
    reflexive = _is_reflexive(infinitive)
    if verb_class == ARE:
        form = f"{stem}ando"
    elif verb_class in (ERE, RRE, IRE, ISC):
        form = f"{stem}endo"
    else:
        raise AssertionError(f"Impossible verb class '{verb_class}'.")
    if reflexive:
        form = f"{form}si"
    return form


def _conjugate_participle(infinitive: str) -> list[str]:
    """Generate the four forms of the regular past participle."""
    verb_class = _get_verb_class(infinitive)
    stem = _get_present_stem(infinitive)
    if verb_class == ARE:
        base = f"{stem}at"
    elif verb_class in (ERE, RRE):
        base = f"{stem}ut"
    elif verb_class in (IRE, ISC):
        base = f"{stem}it"
    else:
        raise AssertionError(f"Impossible verb class '{verb_class}'.")
    return [f"{base}o", f"{base}a", f"{base}i", f"{base}e"]


def _get_future_stem(infinitive: str) -> str:
    base = _ensure_non_reflexive(infinitive)
    if _get_verb_class(infinitive) == ARE:
        return base[:-3] + "er"
    else:
        return base[:-1]


def _conjugate_future(infinitive: str) -> list[str]:
    stem = _get_future_stem(infinitive)
    return [f"{stem}ò", f"{stem}ai", f"{stem}à", f"{stem}emo", f"{stem}ete", f"{stem}anno"]


def _conjugate_conditional(infinitive: str) -> list[str]:
    stem = _get_future_stem(infinitive)
    return [
        f"{stem}ei",
        f"{stem}esti",
        f"{stem}ebbe",
        f"{stem}emmo",
        f"{stem}este",
        f"{stem}ebbero",
    ]


def _conjugate_passato_remoto(infinitive: str) -> list[str]:
    verb_class = _get_verb_class(infinitive)
    stem = _get_present_stem(infinitive)
    if verb_class == ARE:
        return [
            f"{stem}ai",
            f"{stem}asti",
            f"{stem}ò",
            f"{stem}ammo",
            f"{stem}aste",
            f"{stem}arono",
        ]
    elif verb_class in (ERE, RRE):
        # TODO: Generate: -ei forms.
        return [
            f"{stem}etti",
            f"{stem}esti",
            f"{stem}ette",
            f"{stem}emmo",
            f"{stem}este",
            f"{stem}ettero",
        ]
    elif verb_class in (IRE, ISC):
        return [
            f"{stem}ii",
            f"{stem}isti",
            f"{stem}ì",
            f"{stem}immo",
            f"{stem}iste",
            f"{stem}irono",
        ]
    else:
        raise AssertionError(f"Impossible verb class '{verb_class}'.")


def _ensure_non_reflexive(infinitive: str) -> str:
    """Get the non-reflexive base verb for a reflexive infinitive."""
    if infinitive.endswith("porsi"):
        return infinitive[:-5] + "porre"
    elif infinitive.endswith("dursi"):
        return infinitive[:-5] + "durre"
    elif infinitive.endswith(("arsi", "ersi", "irsi")):
        return infinitive[:-2] + "e"
    else:
        return infinitive


def _reflex(forms: list[str], reflexive: bool) -> list[str]:
    assert len(forms) == 6, f"{forms=}"
    if reflexive:
        return [f"{pron} {form}" for pron, form in zip(REFLEXIVE_PRONOUNS, forms, strict=True)]
    else:
        return forms


def conjugate_as_regular(verb: str) -> dict[SimpleTense, list[str]]:
    """Returns a map from simple tense to list of forms (6, except gerund and participle)."""
    reflexive = _is_reflexive(verb)
    return {
        SimpleTense.PRESENT: _reflex(_conjugate_present(verb), reflexive),
        SimpleTense.IMPERFECT: _reflex(_conjugate_imperfect(verb), reflexive),
        SimpleTense.PASSATO_REMOTO: _reflex(_conjugate_passato_remoto(verb), reflexive),
        SimpleTense.FUTURE: _reflex(_conjugate_future(verb), reflexive),
        SimpleTense.CONDITIONAL: _reflex(_conjugate_conditional(verb), reflexive),
        SimpleTense.GERUND: [_conjugate_gerund(verb)],
        SimpleTense.PARTICIPLE: _conjugate_participle(verb),
    }
