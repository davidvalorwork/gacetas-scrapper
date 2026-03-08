from flask import Blueprint, request, jsonify

from src.api.v1.schemas import parse_search_request, format_paginated_response
from src.services.api_service import query_personas_mongo
from src.api.v1.utils import build_search_conditions
from src.api.v1.database import get_db

api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

@api_v1_bp.route('/personas', methods=['GET'])
def buscar_personas():
    """
    Endpoint para integraciones externas. Permite buscar personas registradas
    en las Gacetas por su número de cédula o nombre y apellido.

    ---
    Parámetros (Query params):
    - `cedula` (str, opcional): Búsqueda por documento de identidad. 
                       Formato esperado: Incluir la letra y el guión, ej. "V-12345678" o "E-12345678".
                       La búsqueda se hace por coincidencia exacta de inicio (empieza con). No case-sensitive y sin acentos.
    - `nombre` (str, opcional): Búsqueda por nombre o apellido. 
                       Comportamiento: "Case-insensitive" y sin acentos. Buscar `perez` equivale a `Pérez` o `PEREZ`
                       Busca coincidencias parciales.
    - `q`      (str, opcional): Término genérico. Busca coincidencias (case-insensitive y sin acentos) tanto en nombres como en cédulas simultáneamente.
    - `page`   (int, opcional): Número de la página para la paginación (default: 1).
    - `limit`  (int, opcional): Límite de resultados por página. Mínimo 1, Máximo 100 (default: 15).

    Retorna:
    Un JSON con `estado`, los `datos` (con todas las apariciones en las gacetas) y la metadata de `paginacion`.
    """
    # 1. Parsear y normalizar parámetros de entrada
    params = parse_search_request(request.args)
    
    # 2. Construir condiciones de búsqueda tolerantes a acentos
    and_conditions = build_search_conditions(params)

    # 3. Consultar base de datos
    db = get_db()
    data, total = query_personas_mongo(
        db=db, 
        match_conditions=and_conditions, 
        page=params["page"], 
        limit=params["limit"]
    )
    
    # 4. Formatear y retornar respuesta estandarizada
    response = format_paginated_response(
        data=data,
        total=total,
        page=params["page"],
        limit=params["limit"]
    )
    
    return jsonify(response)
