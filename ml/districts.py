"""Reconciling district names across sources that do not agree on them.

Three files in this project name Karnataka districts, and no two of them agree:

* the IMD daily rainfall file uses a mixture of pre-rename and misspelled forms
  ("TUMKUR", "MANDHYA", "BIJAAPUR", "BANGLORE URBAN");
* the district yield file uses another mixture, sometimes carrying both names
  in one cell ("BIJAPUR / VIJAYAPURA", "KODAGU / COORG", "SHIMOGE");
* farms recorded in the application use whatever the farmer typed, which is
  usually the current official name ("Tumakuru").

Joining these by string equality silently loses most of the overlap. Joining
them by fuzzy string distance is worse: "Bijapur" and "Vijayanagara" are close
enough to match on several common metrics and are different districts, and a
wrong join here would attribute one district's yields to another's rainfall
without anything visibly failing.

So the mapping is an explicit table. Every alias below was resolved by name,
not by similarity, and anything that could not be resolved is listed as
unresolved rather than guessed.

THE BANGALORE PROBLEM
---------------------
Bangalore district was split into Bangalore Urban and Bangalore Rural in 1986,
and Ramanagara was carved out of the rural district in 2007. The yield file
reports a single "BANGALORE"; the IMD file reports "BANGLORE URBAN",
"BANGALORE RURAL" and "RAMNAGAR" separately. These are not aliases of each
other and this module does not pretend otherwise: rainfall for the three parts
cannot be attributed to the yield record for the whole, so the pairing is
refused and reported. Splitting the yield by area would be inventing data.
"""

from __future__ import annotations

import re
from typing import Final

#: Aliases to the current official district name.
#:
#: Keys are normalised (upper case, punctuation stripped) before lookup, so a
#: single entry covers several spellings. Each group is one district under its
#: historical, misspelled and renamed forms.
_ALIASES: Final[dict[str, str]] = {
    # -- renamed in 2014 ------------------------------------------------
    "BANGALORE URBAN": "BENGALURU URBAN",
    "BANGLORE URBAN": "BENGALURU URBAN",     # misspelled in the IMD file
    "BENGALURU URBAN": "BENGALURU URBAN",
    "BANGALORE RURAL": "BENGALURU RURAL",
    "BENGALURU RURAL": "BENGALURU RURAL",
    "BELGAUM": "BELAGAVI",
    "BELAGAVI": "BELAGAVI",
    "BELLARY": "BALLARI",
    "BALLARI": "BALLARI",
    "BIJAPUR": "VIJAYAPURA",
    "BIJAAPUR": "VIJAYAPURA",                # misspelled in the IMD file
    "VIJAYAPURA": "VIJAYAPURA",
    "CHIKMAGALUR": "CHIKKAMAGALURU",
    "CHICKMAGALUR": "CHIKKAMAGALURU",
    "CHIKKAMAGALURU": "CHIKKAMAGALURU",
    "GULBARGA": "KALABURAGI",
    "KALABURAGI": "KALABURAGI",
    "MYSORE": "MYSURU",
    "MYSURU": "MYSURU",
    "SHIMOGA": "SHIVAMOGGA",
    "SHIMOGE": "SHIVAMOGGA",                 # variant in the yield file
    "SHIVAMOGGA": "SHIVAMOGGA",
    "TUMKUR": "TUMAKURU",
    "TUMAKURU": "TUMAKURU",
    "CHIKBALLAPUR": "CHIKKABALLAPURA",
    "CHIKKABALLAPUR": "CHIKKABALLAPURA",
    "CHIKKABALLAPURA": "CHIKKABALLAPURA",
    "RAMNAGAR": "RAMANAGARA",
    "RAMANAGARA": "RAMANAGARA",
    # -- spelling only ---------------------------------------------------
    "DAKSHIN KANNADA": "DAKSHINA KANNADA",
    "DAKSHINA KANNADA": "DAKSHINA KANNADA",
    "UTTAR KANNADA": "UTTARA KANNADA",
    "UTTARA KANNADA": "UTTARA KANNADA",
    "MANDHYA": "MANDYA",
    "MANDYA": "MANDYA",
    "COORG": "KODAGU",
    "KODAGU": "KODAGU",
    "DAVANGERE": "DAVANAGERE",
    "DAVANAGERE": "DAVANAGERE",
}

#: Districts whose records cannot be paired across sources, and why.
#:
#: These are reported to the caller rather than silently dropped, because "no
#: data for your district" and "the sources disagree about your district" are
#: different answers and only the second one is this project's fault.
UNRESOLVED: Final[dict[str, str]] = {
    "BENGALURU URBAN": (
        "The yield record predates the 1986 split and reports a single "
        "'Bangalore' district. Rainfall is reported for the urban and rural "
        "parts separately. The two cannot be paired without apportioning "
        "yields between districts, which the sources do not support."
    ),
    "BENGALURU RURAL": (
        "See Bengaluru Urban: the yield record predates the split, and "
        "Ramanagara was later carved out of this district as well."
    ),
    "RAMANAGARA": (
        "Created in 2007 from Bangalore Rural. No yield record exists under "
        "this name for 2010-2017 in the supplied file."
    ),
}


def normalise(name: str | None) -> str:
    """Reduce a district name to its canonical current form.

    Handles the three shapes these files actually contain: a plain name, a
    misspelling, and a cell carrying both the old and new name separated by a
    slash ("BIJAPUR / VIJAYAPURA"). For the slash form each side is resolved
    and the first recognised one wins, which is correct because both sides
    denote the same district.

    An unrecognised name is returned upper-cased and stripped rather than
    rejected: a district this table has not seen is still a usable key for
    joining a source to itself, and pretending otherwise would discard data
    over a missing alias.
    """
    if not name:
        return ""

    cleaned = re.sub(r"[^\w\s/]", " ", str(name)).strip().upper()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        return ""

    if cleaned in _ALIASES:
        return _ALIASES[cleaned]

    if "/" in cleaned:
        for part in (p.strip() for p in cleaned.split("/")):
            if part in _ALIASES:
                return _ALIASES[part]
        # Neither side is known; keep the more modern-looking second part,
        # which is the convention the yield file follows.
        parts = [p.strip() for p in cleaned.split("/") if p.strip()]
        return parts[-1] if parts else cleaned

    return cleaned


def is_unresolved(name: str | None) -> bool:
    """Whether this district is known to be unpairable across the sources."""
    return normalise(name) in UNRESOLVED


def unresolved_reason(name: str | None) -> str | None:
    """Why a district cannot be paired, or None if it can."""
    return UNRESOLVED.get(normalise(name))


def reconcile(left: set[str], right: set[str]) -> dict[str, object]:
    """Report how two sources' district-name sets overlap once normalised.

    Used by the data-quality report so the join's coverage is a published
    figure rather than an assumption.
    """
    left_map = {normalise(n): n for n in left if normalise(n)}
    right_map = {normalise(n): n for n in right if normalise(n)}
    shared = sorted(set(left_map) & set(right_map))

    return {
        "left_count": len(left_map),
        "right_count": len(right_map),
        "matched": shared,
        "matched_count": len(shared),
        "left_only": sorted(set(left_map) - set(right_map)),
        "right_only": sorted(set(right_map) - set(left_map)),
        "unresolved": sorted(
            d for d in set(left_map) | set(right_map) if d in UNRESOLVED
        ),
    }


__all__ = [
    "UNRESOLVED",
    "normalise",
    "is_unresolved",
    "unresolved_reason",
    "reconcile",
]
