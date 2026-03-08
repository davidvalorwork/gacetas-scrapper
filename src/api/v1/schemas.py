"""
Data transfer objects and serialization for the API V1.
Modifica este archivo para cambiar los campos exactos que recibe y envía la API.
"""

def parse_search_request(args: dict) -> dict:
    """
    Parsea y limpia los parámetros de entrada desde la URL.
    Puedes agregar o remover campos aquí (ej. agregar un rango de fechas).
    """
    return {
        "query": args.get("q", "").strip(),
        "cedula": args.get("cedula", "").strip(),
        "nombre": args.get("nombre", "").strip(),
        "limit": max(1, min(100, int(args.get("limit", 15)))), # Limit max to 100
        "page": max(1, int(args.get("page", 1)))
    }

def format_aparicion(ap: dict) -> dict:
    """
    Mapeo de campos de cada aparición individual de una persona.
    """
    return {
        "numero_gaceta": ap.get("numero_gaceta"),
        "fecha_publicacion": ap.get("fecha"),
        "numero_pagina": ap.get("pagina"),
        "archivo_pdf": ap.get("filename")
    }

def format_persona_response(persona_doc: dict) -> dict:
    """
    Mapeo principal de persona.
    Modifica este diccionario para retornar más o menos datos al integrador.
    """
    apariciones = persona_doc.get("apariciones", [])
    
    return {
        "id_referencia": str(persona_doc.get("_id", "")),
        "documento_identidad": persona_doc.get("cedula"),
        "nombre_completo": persona_doc.get("nombre"),
        "total_menciones": int(persona_doc.get("total_apariciones", len(apariciones))),
        "menciones_gaceta": [format_aparicion(ap) for ap in apariciones if ap.get("numero_gaceta")]
    }

def format_paginated_response(data: list, total: int, page: int, limit: int) -> dict:
    """
    Formato de respuesta paginada estandarizada.
    """
    return {
        "estado": "exito",
        "datos": [format_persona_response(doc) for doc in data],
        "paginacion": {
            "total_registros": total,
            "pagina_actual": page,
            "limite_por_pagina": limit,
            "total_paginas": (total + limit - 1) // limit if limit > 0 else 0
        }
    }
