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
    # Matches formats like V-1234, J-1234, j. 123.123, V1234567, etc.
    # We explicitly exclude 'N' because it matches generic "Número" references.
    return re.compile(
        r"(?i)\b([VJEGP][.\-*°\s]{0,3})\s*(\d[\d.,]*\d|\d)\b"
    )

_CEDULA_RE = _cedula_pattern()

# Regex to find names (2 to 6 words), enforcing it starts and ends with a solid word, allowing connectors in the middle.
_NAME_RE = re.compile(
    r"\b(?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+|[A-ZÁÉÍÓÚÑ]{2,})\s+(?:(?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+|[A-ZÁÉÍÓÚÑ]{2,}|de|del|la|las|los|y|DE|DEL|LA|LAS|LOS|Y)\s+){0,4}(?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+|[A-ZÁÉÍÓÚÑ]{2,})\b"
)

# Regex to require at least one relevant keyword near the cedula
_KEYWORDS_RE = re.compile(
    r"\b(ciudadano|ciudadana|ciudadanos|ciudadanas|empresa|empresas|junta directiva|titular|titulares|representante|representantes|c\.?i\.?|rif|cédula|cedula|identidad|identificado|identificada|identifican|inscrita|inscrito|apoderado|apoderada|venezolano|venezolana|mayor de edad|presidente|presidenta|director|directora|socio|socia|accionista|domiciliado|domiciliada|registro mercantil|pasaporte|portador|portadora)\b",
    re.IGNORECASE
)

# Words to ignore when extracting names, to avoid matching legal boilerplate like "Cédula de Identidad"
_BLACKLIST_RE = re.compile(
    r"(?i)\b(c[eé]dula|identidad|rep[uú]blica|bolivariana|venezuela|ministerio|poder|popular|gaceta|oficial|art[ií]culo|ciudadano|ciudadana|titular|resoluci[oó]n|nacional|director|directora|presidente|presidenta|coordinador|coordinadora|despacho|providencia|registro|mercantil|civil|tomo|folio|protocolo|n[°*o]?|"
    r"salud|integral|comunitaria|asic|hospital|cl[ií]nica|ambulatorio|ambulatoria|red|direcci[oó]n|estadal|estado|corporaci[oó]n|fundaci[oó]n|misi[oó]n|barrio|adentro|instituto|centro|regional|municipal|servicio|social|desarrollo|[aá]rea)\b"
)

def extract_name(ctx_before: str, ctx_after: str) -> str | None:
    # Clean the context from known non-name capitalized words
    clean_before = _BLACKLIST_RE.sub(" ", ctx_before)
    clean_after = _BLACKLIST_RE.sub(" ", ctx_after)
    
    # Check in before:
    matches_before = list(_NAME_RE.finditer(clean_before))
    if matches_before:
        # returns the last name before the cedula
        return matches_before[-1].group(0)
    
    # Check in after:
    matches_after = list(_NAME_RE.finditer(clean_after))
    if matches_after:
        # returns the first name after the cedula
        return matches_after[0].group(0)
    
    return None

def has_valid_context(ctx_before: str, ctx_after: str) -> bool:
    combined_context = f"{ctx_before} {ctx_after}"
    return bool(_KEYWORDS_RE.search(combined_context))

def find_cedulas_with_context(text: str) -> list[dict[str, Any]]:
    """
    Find all Venezuelan cédula-like patterns in text with surrounding context.
    Returns list of dicts: cedula, letter, number, start, end, context_before, context_after, and name.
    """
    results = []
    for m in _CEDULA_RE.finditer(text):
        start, end = m.start(), m.end()
        
        raw_ced = m.group(0).strip()
        raw_letter = m.group(1).upper()
        raw_number = m.group(2)
        
        # Clean letter: retain only the primary character (V, J, E, G, P)
        clean_letter = re.sub(r"[^VJEGP]", "", raw_letter)
        
        # Clean number: retain only digits
        digits_only = re.sub(r"[^\d]", "", raw_number)
        
        # A valid Venezuelan Cedula or RIF should rarely have fewer than 4 digits.
        # This filters out false positives like "N* 6", "N2", "N. 003".
        if len(digits_only) < 4:
            continue
            
        # Homologated cedula format: "L-12345678"
        std_cedula = f"{clean_letter}-{digits_only}"
            
        # Keyword context check to filter out things like "N. 41.648" inside generic sentences
        keyword_ctx_before = text[max(0, start - 150) : start]
        keyword_ctx_after = text[end : end + 150]
        if not has_valid_context(keyword_ctx_before, keyword_ctx_after):
            continue

        # Grab a smaller context for names to avoid overlapping with other sentences
        ctx_before = text[max(0, start - 120) : start]
        ctx_after = text[end : end + 120]
        
        name = extract_name(ctx_before, ctx_after)
        
        # also capture full context for snippets
        full_ctx_before = text[max(0, start - CEDULA_CONTEXT_CHARS) : start]
        full_ctx_after = text[end : end + CEDULA_CONTEXT_CHARS]
        
        results.append({
            "cedula": std_cedula,
            "cedula_original": raw_ced,
            "letter": clean_letter,
            "number": digits_only,
            "name": name if name else "Desconocido",
            "start": start,
            "end": end,
            "context_before": full_ctx_before.strip(),
            "context_after": full_ctx_after.strip(),
        })
    return results
