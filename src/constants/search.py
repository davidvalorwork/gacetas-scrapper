"""
Search-related constants: cédula pattern parameters and context sizes.
Modify here to change what is searched and how much context is captured.
"""

# Venezuelan cédula: letter (B, V, E, J, G) + 6–9 digits
CEDULA_LETTERS = "BVEGJ"
CEDULA_DIGITS_MIN = 5
CEDULA_DIGITS_MAX = 9
CEDULA_CONTEXT_CHARS = 400
SNIPPET_LEN_CEDULA = 150

# Length of context stored in CSV for verification (fuller snippet to read the page)
CSV_CONTEXT_VERIFICATION_CHARS = 800
