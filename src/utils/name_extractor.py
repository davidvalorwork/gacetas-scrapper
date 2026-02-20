"""
Heuristic extraction of names and surnames from context around a cédula.
Used for CSV export. We only use lines immediately adjacent to the cédula
and reject common document/OCR words. If nothing looks like a real name,
we return empty strings so the CSV does not show false names.
"""
import re
from typing import Tuple

# Words that are clearly not person names (gaceta text, labels, OCR noise).
# Lowercase for comparison.
_NOT_NAMES = frozenset({
    "de", "la", "el", "los", "las", "y", "en", "al", "del", "un", "una", "por", "con",
    "gaceta", "oficial", "república", "bolivariana", "venezuela", "ministerio", "nacional",
    "artículo", "articulo", "decreto", "ley", "resolución", "resolucion", "número", "numero",
    "poder", "popular", "presidente", "ministro", "director", "secretario", "titular",
    "identificación", "identificacion", "cédula", "cedula", "nombre", "apellido",
    "ciudadano", "ciudadana", "solicitante", "compareciente", "firma", "fecha",
    "página", "pagina", "pág", "pag", "oficina", "registro", "civil", "estado",
    "república", "republica", "domicilio", "nacionalidad", "profesión", "profesion",
    "naturalización", "naturalizacion", "orden", "publicación", "publicacion",
    "ejecutivo", "judicial", "legislativo", "gobierno", "administración", "administracion",
    "asunto", "referencia", "documento", "expediente", "certificado", "notaría", "notaria",
    "sí", "si", "no", "ser", "será", "sera", "ha", "han", "es", "son", "está", "esta",
    "para", "que", "como", "sus", "suscrito", "firmado", "presente", "siguiente",
    "primero", "segundo", "tercero", "cuarto", "quinto", "sexto", "séptimo", "septimo",
    "aprueba", "dicta", "publica", "notifica", "certifica", "consta", "expone",
    "naturalizado", "naturalizada", "inscrito", "inscrita", "nacido", "nacida",
    "domiciliado", "domiciliada", "comparece", "solicita", "designado", "designada",
    "nombrado", "nombrada", "titular", "suplente", "encargado", "encargada",
    "imprenta", "nacional", "gob", "ve", "caracas", "distrito", "capital",
    "general", "mayor", "almirante", "comandante", "contralmirante", "vicealmirante",
    "división", "division", "brigada", "fuerzas", "armadas", "defensa", "fanb", "zodi",
    "ascenso", "ascendido", "designado", "nombramiento", "rango", "grado",
})


def _normalize_word(w: str) -> str:
    return w.strip().lower()


def _looks_like_name_word(w: str) -> bool:
    """Word must be at least 2 chars, only letters (with accents), not in blacklist."""
    if len(w) < 2:
        return False
    if not re.match(r"^[A-Za-zÁáÉéÍíÓóÚúÑñÜü\-]+$", w):
        return False
    return _normalize_word(w) not in _NOT_NAMES


def _candidate_line(line: str) -> bool:
    """Line must have 2–5 words that all look like name parts; no digits."""
    line = line.strip()
    if len(line) < 4 or len(line) > 120:
        return False
    if re.search(r"\d", line):
        return False
    words = line.split()
    if not (2 <= len(words) <= 5):
        return False
    return all(_looks_like_name_word(w) for w in words)


def extract_nombres_apellidos(context_before: str, context_after: str) -> Tuple[str, str]:
    """
    Try to extract a real name from the lines immediately next to the cédula.
    We only consider:
      - the last line of context_before (right before the cédula), and
      - the first line of context_after (right after the cédula).
    Words must look like name words (no document keywords, no numbers).
    Returns ("", "") when nothing looks like a person's name, so the CSV stays clean.
    """
    def first_line(text: str) -> str:
        for ln in text.splitlines():
            ln = ln.strip()
            if ln:
                return ln
        return ""

    def last_line(text: str) -> str:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        return lines[-1] if lines else ""

    # Only the immediate neighbor lines (closest to cédula)
    candidates = [
        last_line(context_before),
        first_line(context_after),
    ]
    for line in candidates:
        if not line or not _candidate_line(line):
            continue
        words = line.split()
        if len(words) <= 2:
            nombres = words[0]
            apellidos = words[1] if len(words) > 1 else ""
        elif len(words) == 3:
            nombres = words[0]
            apellidos = " ".join(words[1:])
        else:
            nombres = " ".join(words[:2])
            apellidos = " ".join(words[2:])
        return (nombres.strip(), apellidos.strip())

    return ("", "")


