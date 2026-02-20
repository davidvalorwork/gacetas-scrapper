"""
Port: abstraction for reading gacetas (all documents, all pages).
Implementations (adapters) can use MongoDB, files, etc.
"""
from typing import Protocol, Iterator, Optional
from dataclasses import dataclass


@dataclass
class GacetaPage:
    page_number: Optional[int]
    text: str


@dataclass
class GacetaDocument:
    filename: str
    numero_gaceta: str
    fecha: str
    year: Optional[int]
    pages: list[GacetaPage]
    full_text: str


class GacetaRepository(Protocol):
    """Provides access to all registered gacetas and their pages."""

    def iter_gacetas(self, limit: Optional[int] = None) -> Iterator[GacetaDocument]:
        """Yield every gaceta (all pages). If limit is set, yield at most that many gacetas."""
        ...

    def count(self) -> int:
        """Total number of gacetas in the store."""
        ...
