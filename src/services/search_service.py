"""
Application services: search all gacetas (via port) for cédulas and military terms.
Uses GacetaRepository (port) and text matchers (utils). Easy to change repository or patterns.
"""
from typing import Optional, Any, List

from src.ports.repository import GacetaRepository, GacetaDocument
from src.utils.text_matchers import (
    find_cedulas_with_context,
    find_military_mentions_with_context,
    find_rank_name_ci_title_with_context,
    find_ciudadano_rank_name_ci_cargo_with_context,
)
from src.constants.search import SNIPPET_LEN_CEDULA, SNIPPET_LEN_MILITARY


def search_cedulas(
    repository: GacetaRepository,
    limit_gacetas: Optional[int] = None,
) -> List[dict[str, Any]]:
    """
    Iterate all gacetas from the repository; for each gaceta, scan all pages.
    Return list of hits with gaceta metadata, page number, and context.
    """
    results: List[dict[str, Any]] = []
    for doc in repository.iter_gacetas(limit=limit_gacetas):
        # Prefer per-page scan so we can report page_number
        for page in doc.pages:
            hits = find_cedulas_with_context(page.text)
            for h in hits:
                snippet = (
                    h["context_before"][-SNIPPET_LEN_CEDULA:]
                    + " ["
                    + h["cedula"]
                    + "] "
                    + h["context_after"][:SNIPPET_LEN_CEDULA]
                ).strip()
                results.append({
                    "gaceta": doc.filename,
                    "numero_gaceta": doc.numero_gaceta,
                    "fecha": doc.fecha,
                    "year": doc.year,
                    "page_number": page.page_number,
                    "cedula": h["cedula"],
                    "letter": h["letter"],
                    "number": h["number"],
                    "context_before": h["context_before"],
                    "context_after": h["context_after"],
                    "snippet": snippet,
                })
        if not doc.pages and doc.full_text:
            hits = find_cedulas_with_context(doc.full_text)
            for h in hits:
                snippet = (
                    h["context_before"][-SNIPPET_LEN_CEDULA:]
                    + " ["
                    + h["cedula"]
                    + "] "
                    + h["context_after"][:SNIPPET_LEN_CEDULA]
                ).strip()
                results.append({
                    "gaceta": doc.filename,
                    "numero_gaceta": doc.numero_gaceta,
                    "fecha": doc.fecha,
                    "year": doc.year,
                    "page_number": None,
                    "cedula": h["cedula"],
                    "letter": h["letter"],
                    "number": h["number"],
                    "context_before": h["context_before"],
                    "context_after": h["context_after"],
                    "snippet": snippet,
                })
    return results


def search_military(
    repository: GacetaRepository,
    limit_gacetas: Optional[int] = None,
) -> List[dict[str, Any]]:
    """
    Iterate all gacetas from the repository; for each gaceta, scan all pages.
    Return list of hits with gaceta metadata, page number, and context.
    """
    results: List[dict[str, Any]] = []
    for doc in repository.iter_gacetas(limit=limit_gacetas):
        for page in doc.pages:
            hits = find_military_mentions_with_context(page.text)
            for h in hits:
                snippet = (
                    h["context_before"][-SNIPPET_LEN_MILITARY:]
                    + " <<"
                    + h["term"]
                    + ">> "
                    + h["context_after"][:SNIPPET_LEN_MILITARY]
                ).strip()
                results.append({
                    "gaceta": doc.filename,
                    "numero_gaceta": doc.numero_gaceta,
                    "fecha": doc.fecha,
                    "year": doc.year,
                    "page_number": page.page_number,
                    "term": h["term"],
                    "context_before": h["context_before"],
                    "context_after": h["context_after"],
                    "snippet": snippet,
                })
        if not doc.pages and doc.full_text:
            hits = find_military_mentions_with_context(doc.full_text)
            for h in hits:
                snippet = (
                    h["context_before"][-SNIPPET_LEN_MILITARY:]
                    + " <<"
                    + h["term"]
                    + ">> "
                    + h["context_after"][:SNIPPET_LEN_MILITARY]
                ).strip()
                results.append({
                    "gaceta": doc.filename,
                    "numero_gaceta": doc.numero_gaceta,
                    "fecha": doc.fecha,
                    "year": doc.year,
                    "page_number": None,
                    "term": h["term"],
                    "context_before": h["context_before"],
                    "context_after": h["context_after"],
                    "snippet": snippet,
                })
    return results


def search_rank_name_ci_title(
    repository: GacetaRepository,
    limit_gacetas: Optional[int] = None,
) -> List[dict[str, Any]]:
    """
    Find pattern: Rango + Nombre completo + , C.I Nº número + , Cargo.
    Example: General de Brigada JHONNY ALBERTO MORALES RODRÍGUEZ, C.I Nº 12.685.318, Presidente Ejecutivo.
    """
    results: List[dict[str, Any]] = []
    for doc in repository.iter_gacetas(limit=limit_gacetas):
        for page in doc.pages:
            hits = find_rank_name_ci_title_with_context(page.text)
            for h in hits:
                results.append({
                    "gaceta": doc.filename,
                    "numero_gaceta": doc.numero_gaceta,
                    "fecha": doc.fecha,
                    "year": doc.year,
                    "page_number": page.page_number,
                    "rank": h["rank"],
                    "full_name": h["full_name"],
                    "ci_number": h["ci_number"],
                    "title": h["title"],
                    "context_before": h["context_before"],
                    "context_after": h["context_after"],
                })
        if not doc.pages and doc.full_text:
            hits = find_rank_name_ci_title_with_context(doc.full_text)
            for h in hits:
                results.append({
                    "gaceta": doc.filename,
                    "numero_gaceta": doc.numero_gaceta,
                    "fecha": doc.fecha,
                    "year": doc.year,
                    "page_number": None,
                    "rank": h["rank"],
                    "full_name": h["full_name"],
                    "ci_number": h["ci_number"],
                    "title": h["title"],
                    "context_before": h["context_before"],
                    "context_after": h["context_after"],
                })
    return results


def search_ciudadano_rank_name_ci_cargo(
    repository: GacetaRepository,
    limit_gacetas: Optional[int] = None,
) -> List[dict[str, Any]]:
    """
    Find pattern: En relación a la ciudadana/o RANGO NOMBRE, titular de la cédula de identidad [NO] V-13.532.261 en su carácter de (CARGO).
    """
    results: List[dict[str, Any]] = []
    for doc in repository.iter_gacetas(limit=limit_gacetas):
        for page in doc.pages:
            hits = find_ciudadano_rank_name_ci_cargo_with_context(page.text)
            for h in hits:
                results.append({
                    "gaceta": doc.filename,
                    "numero_gaceta": doc.numero_gaceta,
                    "fecha": doc.fecha,
                    "year": doc.year,
                    "page_number": page.page_number,
                    "rank": h["rank"],
                    "full_name": h["full_name"],
                    "ci_letter": h["ci_letter"],
                    "ci_number": h["ci_number"],
                    "ci_full": h["ci_full"],
                    "cargo": h["cargo"],
                    "context_before": h["context_before"],
                    "context_after": h["context_after"],
                })
        if not doc.pages and doc.full_text:
            hits = find_ciudadano_rank_name_ci_cargo_with_context(doc.full_text)
            for h in hits:
                results.append({
                    "gaceta": doc.filename,
                    "numero_gaceta": doc.numero_gaceta,
                    "fecha": doc.fecha,
                    "year": doc.year,
                    "page_number": None,
                    "rank": h["rank"],
                    "full_name": h["full_name"],
                    "ci_letter": h["ci_letter"],
                    "ci_number": h["ci_number"],
                    "ci_full": h["ci_full"],
                    "cargo": h["cargo"],
                    "context_before": h["context_before"],
                    "context_after": h["context_after"],
                })
    return results
