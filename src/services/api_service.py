from typing import List, Dict, Any, Tuple

def query_personas_mongo(db, match_conditions: List[Dict[str, Any]], page: int, limit: int) -> Tuple[List[Dict[str, Any]], int]:
    """
    Lógica de base de datos extraída de la ruta para mantener el código limpio.
    Busca las personas de acuerdo a las condiciones recibidas con paginación.
    Retorna (resultados, total).
    """
    skip = (page - 1) * limit
    
    pipeline = []
    if match_conditions:
        if len(match_conditions) == 1:
            pipeline.append({"$match": match_conditions[0]})
        else:
            pipeline.append({"$match": {"$and": match_conditions}})
            
    facet_data = [
        {"$sort": {"_id": -1}},
        {"$skip": skip},
        {"$limit": limit},
        {"$lookup": {
            "from": "persona_gaceta",
            "localField": "_id",
            "foreignField": "persona_id",
            "as": "relationships"
        }},
        {"$unwind": {"path": "$relationships", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "gaceta",
            "localField": "relationships.gaceta_id",
            "foreignField": "_id",
            "as": "gaceta_info"
        }},
        {"$unwind": {"path": "$gaceta_info", "preserveNullAndEmptyArrays": True}},
        {"$sort": {"gaceta_info.numero_gaceta": -1}},
        {"$group": {
            "_id": "$_id",
            "cedula": {"$first": "$cedula"},
            "nombre": {"$first": "$nombre"},
            "apariciones": {
                "$push": {
                    "numero_gaceta": "$gaceta_info.numero_gaceta",
                    "filename": "$gaceta_info.filename",
                    "fecha": "$gaceta_info.fecha",
                    "pagina": "$relationships.pagina"
                }
            }
        }},
        {"$project": {
            "_id": 1,
            "cedula": 1,
            "nombre": 1,
            "apariciones": {
                "$filter": {
                    "input": "$apariciones",
                    "as": "ap",
                    "cond": {"$ne": ["$$ap.numero_gaceta", None]}
                }
            }
        }},
        {"$addFields": {
            "total_apariciones": {"$size": "$apariciones"}
        }},
        {"$sort": {"cedula": -1}}
    ]

    pipeline.append({
        "$facet": {
            "metadata": [{"$count": "total"}],
            "data": facet_data
        }
    })

    result = list(db.persona.aggregate(pipeline))
    if result and result[0]['metadata']:
        total = result[0]['metadata'][0]['total']
        data = result[0]['data']
    else:
        total = 0
        data = []
        
    return data, total
