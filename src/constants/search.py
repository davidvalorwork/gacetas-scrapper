"""
Search-related constants: cédula pattern parameters, military terms, context sizes.
Modify here to change what is searched and how much context is captured.
"""

# Venezuelan cédula: letter (B, V, E, J, G) + 6–9 digits
CEDULA_LETTERS = "BVEGJ"
CEDULA_DIGITS_MIN = 5
CEDULA_DIGITS_MAX = 9
CEDULA_CONTEXT_CHARS = 400
SNIPPET_LEN_CEDULA = 150

# Military-related terms (phrases and words)
MILITARY_TERMS = [
    "Ministro de Defensa",
    "Ministerio de Defensa",
    "Ministro del Poder Popular para la Defensa",
    "FANB",
    "Fuerza Armada Nacional Bolivariana",
    "Fuerzas Armadas",
    "militar",
    "militares",
    "General de División",
    "General de Brigada",
    "Mayor General",
    "General en Jefe",
    "Almirante",
    "Vicealmirante",
    "Contralmirante",
    "Comandante General",
    "Comandante en Jefe",
    "Comandancia General",
    "Ministerio de la Defensa",
    "Defensa Nacional",
    "ZODI",
    "región de defensa",
    "oficial militar",
    "oficiales militares",
    "tropas",
    "batallón",
    "batallon",
    "regimiento",
]

MILITARY_CONTEXT_CHARS = 500
SNIPPET_LEN_MILITARY = 120
# Length of context stored in CSV for verification (fuller snippet to read the page)
CSV_CONTEXT_VERIFICATION_CHARS = 800

# Format: "General de Brigada NOMBRE APELLIDO, C.I Nº 12.685.318, Presidente Ejecutivo."
# Also: "Mayor JOSÉ ALFREDO..., C.I N* 11.025.190, Presidente Honorario."
# Order: longer ranks first for regex alternation (e.g. "Mayor General" before "Mayor")
RANK_NAME_CI_TITLE_RANKS = [
    "General en Jefe",
    "General de División",
    "General de Brigada",
    "Mayor General",
    "Teniente Coronel",
    "Vicealmirante",
    "Contralmirante",
    "Comandante General",
    "Comandante en Jefe",
    "Almirante",
    "Coronel",
    "Mayor",
    "Capitán",
    "Capitan",
    "Teniente",
    "Sargento",
    "Alférez",
    "Alferez",
]
RANK_NAME_CI_CONTEXT_CHARS = 300

# Format: "En relación a la ciudadana MAYOR JOXA WILMERBIS CARIAS PACHECO, titular de la
# cédula de identidad NO V-13.532.261 en su carácter de (JEFE DE DIVISIÓN DE BIENES PÚBLICOS)..."
# Single-word ranks after "ciudadano/a" (order: longer first)
CIUDADANO_RANK_NAME_CI_RANKS = [
    "Mayor",
    "Capitan",
    "Capitán",
    "Teniente",
    "Coronel",
    "Sargento",
    "Alférez",
    "Alferez",
    "Suboficial",
    "Comandante",
    "Almirante",
    "Vicealmirante",
    "Contralmirante",
]
CIUDADANO_RANK_NAME_CI_CONTEXT_CHARS = 400
