"""
Build CSV rows from cédula and military results with strategic columns.
Columns: Nombres, Apellidos, Cédula, Rango, Nombramiento, Número Gaceta, Fecha, Página, Contexto
"""
import csv
from pathlib import Path
from typing import Any, List

from src.utils.name_extractor import extract_nombres_apellidos, extract_nombres_apellidos_from_extended_context
from src.constants.search import CSV_CONTEXT_VERIFICATION_CHARS

CSV_COLUMNS = [
    "Nombres",
    "Apellidos",
    "Cédula",
    "Rango",
    "Nombramiento",
    "Número Gaceta",
    "Fecha",
    "Página",
    "Contexto",
]


def _is_two_word_term(term: str) -> bool:
    return len(term.split()) == 2


def _format_page(page_number: Any) -> str:
    if page_number is None:
        return ""
    return str(page_number)


def _build_context_snippet(context_before: str, middle: str, context_after: str, total_chars: int) -> str:
    half = max(100, total_chars // 2)
    before = context_before[-half:] if len(context_before) > half else context_before
    after = context_after[:half] if len(context_after) > half else context_after
    return f"{before} {middle} {after}".strip()


def _split_full_name(full_name: str) -> tuple[str, str]:
    """Split 'NOMBRE SEGUNDO APELLIDO SEGUNDO_APELLIDO' into (nombres, apellidos)."""
    words = full_name.split()
    if not words:
        return ("", "")
    if len(words) <= 2:
        return (words[0], words[1] if len(words) > 1 else "")
    if len(words) == 3:
        return (words[0], " ".join(words[1:]))
    return (" ".join(words[:2]), " ".join(words[2:]))


def build_csv_rows(
    cedulas: List[dict[str, Any]],
    military: List[dict[str, Any]],
    rank_name_ci: List[dict[str, Any]] | None = None,
    ciudadano_rank_name_ci: List[dict[str, Any]] | None = None,
    military_two_words_only: bool = True,
) -> List[dict[str, str]]:
    """
    Build one row per cédula hit, military hit (optionally only 2-word terms),
    rank+name+CI+title hit, and ciudadano+rank+name+CI+cargo hit.
    Each row includes Página and Contexto for verification.
    """
    rows: List[dict[str, str]] = []
    ctx_len = CSV_CONTEXT_VERIFICATION_CHARS
    rank_name_ci = rank_name_ci or []
    ciudadano_rank_name_ci = ciudadano_rank_name_ci or []

    for r in cedulas:
        nombres, apellidos = extract_nombres_apellidos(
            r.get("context_before", ""),
            r.get("context_after", ""),
        )
        contexto = _build_context_snippet(
            r.get("context_before", ""),
            f"[{r.get('cedula', '')}]",
            r.get("context_after", ""),
            ctx_len,
        )
        rows.append({
            "Nombres": nombres,
            "Apellidos": apellidos,
            "Cédula": r.get("cedula", ""),
            "Rango": "",
            "Nombramiento": "",
            "Número Gaceta": r.get("numero_gaceta", ""),
            "Fecha": r.get("fecha", ""),
            "Página": _format_page(r.get("page_number")),
            "Contexto": contexto,
        })

    military_list = military
    if military_two_words_only:
        military_list = [r for r in military if _is_two_word_term(r.get("term", ""))]
    for r in military_list:
        term = r.get("term", "")
        nombres, apellidos = extract_nombres_apellidos_from_extended_context(
            r.get("context_before", ""),
            r.get("context_after", ""),
        )
        contexto = _build_context_snippet(
            r.get("context_before", ""),
            f"<<{term}>>",
            r.get("context_after", ""),
            ctx_len,
        )
        rows.append({
            "Nombres": nombres,
            "Apellidos": apellidos,
            "Cédula": "",
            "Rango": term,
            "Nombramiento": term,
            "Número Gaceta": r.get("numero_gaceta", ""),
            "Fecha": r.get("fecha", ""),
            "Página": _format_page(r.get("page_number")),
            "Contexto": contexto,
        })

    for r in rank_name_ci:
        full_name = r.get("full_name", "")
        nombres, apellidos = _split_full_name(full_name)
        ci = (r.get("ci_number") or "").strip()
        contexto = _build_context_snippet(
            r.get("context_before", ""),
            f"{r.get('rank', '')} {full_name}, C.I {ci}, {r.get('title', '')}",
            r.get("context_after", ""),
            ctx_len,
        )
        rows.append({
            "Nombres": nombres,
            "Apellidos": apellidos,
            "Cédula": ci,
            "Rango": r.get("rank", ""),
            "Nombramiento": r.get("title", ""),
            "Número Gaceta": r.get("numero_gaceta", ""),
            "Fecha": r.get("fecha", ""),
            "Página": _format_page(r.get("page_number")),
            "Contexto": contexto,
        })

    for r in ciudadano_rank_name_ci:
        full_name = r.get("full_name", "")
        nombres, apellidos = _split_full_name(full_name)
        ci_full = r.get("ci_full", "") or f"{r.get('ci_letter', '')}-{r.get('ci_number', '')}"
        cargo = r.get("cargo", "")
        contexto = _build_context_snippet(
            r.get("context_before", ""),
            f"En relación a la ciudadana/o {r.get('rank', '')} {full_name}, C.I {ci_full}, ({cargo})",
            r.get("context_after", ""),
            ctx_len,
        )
        rows.append({
            "Nombres": nombres,
            "Apellidos": apellidos,
            "Cédula": ci_full,
            "Rango": r.get("rank", ""),
            "Nombramiento": cargo,
            "Número Gaceta": r.get("numero_gaceta", ""),
            "Fecha": r.get("fecha", ""),
            "Página": _format_page(r.get("page_number")),
            "Contexto": contexto,
        })

    return rows


def write_csv(filepath: Path, rows: List[dict[str, str]]) -> None:
    """Write rows to CSV with UTF-8 and Excel-friendly BOM for Spanish."""
    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
