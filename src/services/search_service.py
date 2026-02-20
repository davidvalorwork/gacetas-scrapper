"""
Application services: search all gacetas (via port) for cédulas.
Uses GacetaRepository (port) and text matchers (utils). Easy to change repository or patterns.
"""
from typing import Optional, Any, List

from src.ports.repository import GacetaRepository
from src.utils.text_matchers import find_cedulas_with_context
from src.constants.search import SNIPPET_LEN_CEDULA


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
                    "nombre": h["name"],
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
                    "nombre": h["name"],
                    "context_before": h["context_before"],
                    "context_after": h["context_after"],
                    "snippet": snippet,
                })
    return results
