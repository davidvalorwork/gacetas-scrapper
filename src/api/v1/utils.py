import unicodedata
import re
from typing import List, Dict, Any

# Clase de regex por letra base → cubre sus variantes acentuadas (y ñ/ç).
# Se usa con $options:"i", pero incluimos mayúsculas por robustez.
_ACCENT_CLASSES = {
    'a': '[aáàâäãAÁÀÂÄÃ]',
    'e': '[eéèêëEÉÈÊË]',
    'i': '[iíìîïIÍÌÎÏ]',
    'o': '[oóòôöõOÓÒÔÖÕ]',
    'u': '[uúùûüUÚÙÛÜ]',
    'n': '[nñNÑ]',
    'c': '[cçCÇ]',
}


def build_accent_insensitive_regex(term: str) -> str:
    """
    Prepara un patrón de regex que ignora acentos.

    Mapea cada carácter de forma independiente (sin replaces globales que se
    pisen entre sí) para que, p. ej., "Peña" se busque como "Pena" → [nñ]a, y
    "Pérez" matchee "perez".
    """
    if not term:
        return ""
    # Quitamos los diacríticos del input para mapear sobre la letra base ASCII.
    base = (
        unicodedata.normalize('NFD', term)
        .encode('ascii', 'ignore')
        .decode('utf-8')
    )
    out = []
    for ch in base:
        lower = ch.lower()
        if lower in _ACCENT_CLASSES:
            out.append(_ACCENT_CLASSES[lower])
        else:
            out.append(re.escape(ch))
    return ''.join(out)


def _tokenize(text: str) -> List[str]:
    """Divide el texto en palabras (tokens) no vacías."""
    return [t for t in re.split(r'\s+', (text or '').strip()) if t]


def _all_tokens_match(text: str, fields: List[str]) -> List[Dict[str, Any]]:
    """
    Devuelve una condición $and donde CADA token debe aparecer en alguno de los
    `fields`. Así "Nicolas Maduro" matchea "MADURO MOROS, NICOLAS" aunque las
    palabras no sean contiguas ni lleven los mismos acentos.
    """
    conditions = []
    for tok in _tokenize(text):
        rx = build_accent_insensitive_regex(tok)
        conditions.append({
            "$or": [{f: {"$regex": rx, "$options": "i"}} for f in fields]
        })
    return conditions


def build_search_conditions(params: dict) -> List[Dict[str, Any]]:
    """Construye las condiciones $match para MongoDB tolerantes a acentos."""
    and_conditions: List[Dict[str, Any]] = []

    # Término genérico: busca cada palabra en nombre o cédula.
    if params.get("query"):
        and_conditions.extend(
            _all_tokens_match(params["query"], ["nombre", "cedula"])
        )

    # Cédula: coincidencia por inicio (empieza con).
    if params.get("cedula"):
        c_regex = build_accent_insensitive_regex(params["cedula"])
        and_conditions.append({"cedula": {"$regex": f"^{c_regex}", "$options": "i"}})

    # Nombre: cada palabra debe aparecer en el nombre (orden indistinto).
    if params.get("nombre"):
        and_conditions.extend(_all_tokens_match(params["nombre"], ["nombre"]))

    return and_conditions
