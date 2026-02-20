"""
Text matching utilities: find Venezuelan cédulas and military terms in a string,
returning each match with surrounding context. Uses constants for patterns and context size.
"""
import re
from typing import Any

from src.constants.search import (
    CEDULA_LETTERS,
    CEDULA_DIGITS_MIN,
    CEDULA_DIGITS_MAX,
    CEDULA_CONTEXT_CHARS,
    MILITARY_TERMS,
    MILITARY_CONTEXT_CHARS,
    RANK_NAME_CI_TITLE_RANKS,
    RANK_NAME_CI_CONTEXT_CHARS,
    CIUDADANO_RANK_NAME_CI_RANKS,
    CIUDADANO_RANK_NAME_CI_CONTEXT_CHARS,
)


def _cedula_pattern():
    letters = re.escape(CEDULA_LETTERS)
    return re.compile(
        rf"\b([{letters}])\s*[-]?\s*(\d{{{CEDULA_DIGITS_MIN},{CEDULA_DIGITS_MAX}}})\b",
        re.IGNORECASE,
    )


def _military_pattern():
    alternatives = "|".join(re.escape(t) for t in MILITARY_TERMS)
    return re.compile(
        rf"(\b(?:{alternatives})\b)",
        re.IGNORECASE,
    )


_CEDULA_RE = _cedula_pattern()
_MILITARY_RE = _military_pattern()


def _rank_name_ci_title_pattern():
    """Rango NOMBRE, C.I [N*|Nº|N9|N?] número, Cargo. Acepta: C.1 (OCR), C.i¡, N*%, número con salto de línea."""
    ranks_alt = "|".join(re.escape(r) for r in RANK_NAME_CI_TITLE_RANKS)
    # C.I / C.1 / C.i¡ ; N opcional: Nº N* N? N9 N*% (solo símbolos, sin dígitos para no tragar el número) ; \s* incluye newline
    return re.compile(
        rf"({ranks_alt})\s+([A-Za-zÁÉÍÓÚÑáéíóúñ\s]+?),\s*(?:C\.?\s*[I1l¡][\.¡]?|Cédula|cedula)\s*(?:N[º°?*9%]*\s*)?\s*([\d.,]+)\s*,\s*([^\n,]+)",
        re.IGNORECASE,
    )


_RANK_NAME_CI_RE = _rank_name_ci_title_pattern()


def _ciudadano_rank_name_ci_pattern():
    """Format: En relación a la ciudadana MAYOR NOMBRE APELLIDO, titular de la cédula de identidad NO V-13.532.261 en su carácter de (CARGO)."""
    ranks_alt = "|".join(re.escape(r) for r in CIUDADANO_RANK_NAME_CI_RANKS)
    return re.compile(
        rf"En relación a la ciudadan[oa]\s+({ranks_alt})\s+([A-Za-zÁÉÍÓÚÑáéíóúñ\s]+?),\s*titular de\s+la (?:cédula|cedula) de identidad\s*(?:NO\s*)?([{re.escape(CEDULA_LETTERS)}])-?\s*([\d.]+)"
        rf"(?:(?:\s|\S)*?en su carácter de\s*\(([^)]+)\))?",
        re.IGNORECASE | re.DOTALL,
    )


_CIUDADANO_RANK_NAME_CI_RE = _ciudadano_rank_name_ci_pattern()


def find_cedulas_with_context(text: str) -> list[dict[str, Any]]:
    """
    Find all Venezuelan cédula-like patterns in text with surrounding context.
    Returns list of dicts: cedula, letter, number, start, end, context_before, context_after.
    """
    results = []
    for m in _CEDULA_RE.finditer(text):
        start, end = m.start(), m.end()
        ctx_before = text[max(0, start - CEDULA_CONTEXT_CHARS) : start]
        ctx_after = text[end : end + CEDULA_CONTEXT_CHARS]
        results.append({
            "cedula": m.group(0),
            "letter": m.group(1).upper(),
            "number": m.group(2),
            "start": start,
            "end": end,
            "context_before": ctx_before.strip(),
            "context_after": ctx_after.strip(),
        })
    return results


def find_rank_name_ci_title_with_context(text: str) -> list[dict[str, Any]]:
    """
    Find pattern: Rango + Nombre completo + , C.I Nº número + , Cargo/título.
    Example: General de Brigada JHONNY ALBERTO MORALES RODRÍGUEZ, C.I Nº 12.685.318, Presidente Ejecutivo.
    Returns list of dicts: rank, full_name, ci_number, title, start, end, context_before, context_after.
    """
    results = []
    for m in _RANK_NAME_CI_RE.finditer(text):
        start, end = m.start(), m.end()
        rank = m.group(1).strip()
        full_name = m.group(2).strip()
        ci_number = m.group(3).strip()
        title = m.group(4).strip()
        ctx_before = text[max(0, start - RANK_NAME_CI_CONTEXT_CHARS) : start]
        ctx_after = text[end : end + RANK_NAME_CI_CONTEXT_CHARS]
        results.append({
            "rank": rank,
            "full_name": full_name,
            "ci_number": ci_number,
            "title": title,
            "start": start,
            "end": end,
            "context_before": ctx_before.strip(),
            "context_after": ctx_after.strip(),
        })
    return results


def find_ciudadano_rank_name_ci_cargo_with_context(text: str) -> list[dict[str, Any]]:
    """
    Find pattern: En relación a la ciudadana/o RANGO NOMBRE, titular de la cédula de identidad [NO] V-13.532.261 en su carácter de (CARGO).
    Returns list of dicts: rank, full_name, ci_letter, ci_number, cargo, start, end, context_before, context_after.
    """
    results = []
    for m in _CIUDADANO_RANK_NAME_CI_RE.finditer(text):
        start, end = m.start(), m.end()
        rank = m.group(1).strip()
        full_name = m.group(2).strip()
        ci_letter = m.group(3).strip().upper()
        ci_number = m.group(4).strip()
        cargo = (m.group(5) or "").strip()
        ctx_before = text[max(0, start - CIUDADANO_RANK_NAME_CI_CONTEXT_CHARS) : start]
        ctx_after = text[end : end + CIUDADANO_RANK_NAME_CI_CONTEXT_CHARS]
        results.append({
            "rank": rank,
            "full_name": full_name,
            "ci_letter": ci_letter,
            "ci_number": ci_number,
            "ci_full": f"{ci_letter}-{ci_number}",
            "cargo": cargo,
            "start": start,
            "end": end,
            "context_before": ctx_before.strip(),
            "context_after": ctx_after.strip(),
        })
    return results


def find_military_mentions_with_context(text: str) -> list[dict[str, Any]]:
    """
    Find all military term matches in text with surrounding context.
    Returns list of dicts: term, start, end, context_before, context_after.
    """
    results = []
    for m in _MILITARY_RE.finditer(text):
        start, end = m.start(), m.end()
        ctx_before = text[max(0, start - MILITARY_CONTEXT_CHARS) : start]
        ctx_after = text[end : end + MILITARY_CONTEXT_CHARS]
        results.append({
            "term": m.group(1),
            "start": start,
            "end": end,
            "context_before": ctx_before.strip(),
            "context_after": ctx_after.strip(),
        })
    return results
