"""
Text matching utilities: find Venezuelan cédulas in a string,
returning each match with surrounding context, and extracting nearby names.
"""
import re
from typing import Any

from src.constants.search import (
    CEDULA_CONTEXT_CHARS,
)


def _cedula_pattern():
    # Matches formats like V-1234, J-1234, j. 123.123, N* 128382, N. 123,232,33, V1234567, etc.
    return re.compile(
        r"(?i)\b([VJEGN][.\-*°\s]{0,3})\s*(\d[\d.,]*\d|\d)\b"
    )

_CEDULA_RE = _cedula_pattern()

# Regex to find names (2 to 6 capitalized words, handling de/del/la/las/los/y)
_NAME_RE = re.compile(
    r"\b(?:(?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b|de|del|la|las|los|y)\s+){1,5}[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b"
)

def extract_name(ctx_before: str, ctx_after: str) -> str | None:
    # Check in before:
    matches_before = list(_NAME_RE.finditer(ctx_before))
    if matches_before:
        # returns the last name before the cedula
        return matches_before[-1].group(0)
    
    # Check in after:
    matches_after = list(_NAME_RE.finditer(ctx_after))
    if matches_after:
        # returns the first name after the cedula
        return matches_after[0].group(0)
    
    return None

def find_cedulas_with_context(text: str) -> list[dict[str, Any]]:
    """
    Find all Venezuelan cédula-like patterns in text with surrounding context.
    Returns list of dicts: cedula, letter, number, start, end, context_before, context_after, and name.
    """
    results = []
    for m in _CEDULA_RE.finditer(text):
        start, end = m.start(), m.end()
        # Grab a smaller context for names to avoid overlapping with other sentences
        ctx_before = text[max(0, start - 60) : start]
        ctx_after = text[end : end + 60]
        
        raw_ced = m.group(0).strip()
        letter = m.group(1).upper()
        number = m.group(2)
        
        name = extract_name(ctx_before, ctx_after)
        
        # also capture full context for snippets
        full_ctx_before = text[max(0, start - CEDULA_CONTEXT_CHARS) : start]
        full_ctx_after = text[end : end + CEDULA_CONTEXT_CHARS]
        
        results.append({
            "cedula": raw_ced,
            "letter": letter,
            "number": number,
            "name": name if name else "Desconocido",
            "start": start,
            "end": end,
            "context_before": full_ctx_before.strip(),
            "context_after": full_ctx_after.strip(),
        })
    return results
