"""
Build CSV rows from cédula results with strategic columns.
Columns: Nombres, Apellidos, Cédula, Número Gaceta, Fecha, Página, Contexto
"""
import csv
from pathlib import Path
from typing import Any, List

from src.utils.name_extractor import extract_nombres_apellidos
from src.constants.search import CSV_CONTEXT_VERIFICATION_CHARS

CSV_COLUMNS = [
    "Nombres",
    "Apellidos",
    "Cédula",
    "Número Gaceta",
    "Fecha",
    "Página",
    "Contexto",
]


def _format_page(page_number: Any) -> str:
    if page_number is None:
        return ""
    return str(page_number)


def _build_context_snippet(context_before: str, middle: str, context_after: str, total_chars: int) -> str:
    half = max(100, total_chars // 2)
    before = context_before[-half:] if len(context_before) > half else context_before
    after = context_after[:half] if len(context_after) > half else context_after
    return f"{before} {middle} {after}".strip()


def build_csv_rows(cedulas: List[dict[str, Any]]) -> List[dict[str, str]]:
    """
    Build one row per cédula hit. Each row includes Página and Contexto for verification.
    """
    rows: List[dict[str, str]] = []
    ctx_len = CSV_CONTEXT_VERIFICATION_CHARS

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
