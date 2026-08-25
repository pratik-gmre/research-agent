"""
Converts legacy Preeti-encoded Devanagari text to proper Unicode.

Many Nepal government/institutional PDFs (this booklet included) were
typeset with the Preeti font: visually it renders as Devanagari, but
the underlying character codes are just remapped ASCII. pdfplumber
extracts those raw codes, so it comes out as gibberish like
"of] k/LIffsf] ;dofjlw @ 306fsf] x'g]5" instead of
"यो परीक्षाको समयावधि २ घण्टाको हुनेछ". No retrieval or prompt tuning
fixes this - the text has to be re-mapped at the character level.

Conversion runs per line, not on the whole page at once, because a
single page usually mixes real English (titles, URLs, "Website:") with
Preeti-encoded Nepali, and running the Preeti map over genuine English
text destroys it (e.g. "Online" -> "इलष्लिभ"). Each line is converted
only if doing so increases its Devanagari character ratio; otherwise
the original is kept. URLs/emails are protected from conversion
entirely since they contain no real words to score against.

This is a heuristic, not a perfect font-encoding detector - expect
occasional imperfect renderings (a conjunct glyph rendered slightly
wrong), but it turns "unreadable to the embedding model" into "mostly
readable," which is the difference that matters for retrieval.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from npttf2utf.base.fontmapper import FontMapper

_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
_URL_OR_EMAIL_RE = re.compile(r"\S*(?:https?://|www\.|@[\w.-]+\.\w+)\S*", re.IGNORECASE)
_WORD_RE = re.compile(r"[A-Za-z]+")

# Small, deliberately generic list - just enough to recognize "this line
# is genuinely English prose/headings" vs "this is Preeti gibberish that
# happens to be made of ASCII letters."
_COMMON_ENGLISH_WORDS = frozenset("""
the of and to in a is that for on with as by at be this from or an it
are was were will shall can may not no yes if then than but so such
university institute engineering campus office dean board committee
website online admit card form date time place subject full marks page
mathematics physics chemistry english schedule notice payment fee exam
examination entrance number name student college semester year month
""".split())


@lru_cache(maxsize=1)
def _get_mapper() -> FontMapper:
    map_json = Path(__import__("npttf2utf").__file__).parent / "map.json"
    return FontMapper(str(map_json))


def _devanagari_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    devanagari = sum(1 for c in text if _DEVANAGARI_RE.match(c))
    return devanagari / len(letters)


def _looks_like_english(line: str) -> bool:
    words = _WORD_RE.findall(line.lower())
    if not words:
        return True  # nothing but digits/punctuation - nothing to convert
    matches = sum(1 for w in words if w in _COMMON_ENGLISH_WORDS)
    return (matches / len(words)) > 0.2


def _convert_line(line: str, mapper: FontMapper) -> str:
    if _looks_like_english(line):
        return line

    # Protect URLs/emails so they aren't run through the Preeti map.
    protected: list[str] = []

    def _stash(match: re.Match) -> str:
        protected.append(match.group(0))
        return f"\uE000{len(protected) - 1}\uE001"

    shielded = _URL_OR_EMAIL_RE.sub(_stash, line)
    converted = mapper.map_to_unicode(shielded, from_font="Preeti")

    if _devanagari_ratio(converted) <= _devanagari_ratio(line):
        return line  # conversion didn't help - keep the original

    for i, original in enumerate(protected):
        converted = converted.replace(f"\uE000{i}\uE001", original)

    return converted


def fix_preeti_encoding(text: str) -> str:
    """Run Preeti-detection/conversion over every line of a text block."""
    if not text.strip():
        return text
    mapper = _get_mapper()
    return "\n".join(_convert_line(line, mapper) for line in text.split("\n"))
