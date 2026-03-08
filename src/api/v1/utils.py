import unicodedata
import re
from typing import List, Dict, Any

def build_accent_insensitive_regex(term: str) -> str:
    """Prepara un patrón de búsqueda que ignora acentos al convertirse en Regex."""
    if not term:
        return ""
    # 1. Normalizamos (quitamos tildes del input real por si el usuario sí los puso)
    term = unicodedata.normalize('NFD', term).encode('ascii', 'ignore').decode('utf-8')
    # 2. Escapamos los caracteres reservados para no dañar el regex
    term = re.escape(term)
    # 3. Sustituimos cada vocal por un grupo que abarque acentuaciones típicas
    term = term.replace('a', '[aáAÁ]').replace('A', '[aáAÁ]')
    term = term.replace('e', '[eéEÉ]').replace('E', '[eéEÉ]')
    term = term.replace('i', '[iíIÍ]').replace('I', '[iíIÍ]')
    term = term.replace('o', '[oóOÓ]').replace('O', '[oóOÓ]')
    term = term.replace('u', '[uúUÚ]').replace('U', '[uúUÚ]')
    return term

def build_search_conditions(params: dict) -> List[Dict[str, Any]]:
    """Construye las condiciones $match para MongoDB tolerantes a acentos."""
    and_conditions = []
    
    if params.get("query"):
        q_regex = build_accent_insensitive_regex(params["query"])
        and_conditions.append({
            "$or": [
                {"cedula": {"$regex": q_regex, "$options": "i"}},
                {"nombre": {"$regex": q_regex, "$options": "i"}}
            ]
        })
        
    if params.get("cedula"):
        c_regex = build_accent_insensitive_regex(params["cedula"])
        and_conditions.append({"cedula": {"$regex": f"^{c_regex}", "$options": "i"}})
        
    if params.get("nombre"):
        n_regex = build_accent_insensitive_regex(params["nombre"])
        and_conditions.append({"nombre": {"$regex": n_regex, "$options": "i"}})

    return and_conditions
