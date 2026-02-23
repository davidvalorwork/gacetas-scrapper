import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Replace with your MongoDB connection details if needed
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "gacetas_db")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 15))
    skip = (page - 1) * limit
    letter = request.args.get('letter', '').strip().upper()
    range_filter = request.args.get('range', '').strip()
    sort_by = request.args.get('sort', 'newest')

    and_conditions = []
    
    if query:
        and_conditions.append({
            "$or": [
                {"cedula": {"$regex": query, "$options": "i"}},
                {"nombre": {"$regex": query, "$options": "i"}}
            ]
        })
        
    if letter:
        and_conditions.append({"cedula": {"$regex": f"^{letter}-", "$options": "i"}})
        
    if range_filter == "0-10":
        and_conditions.append({"cedula": {"$regex": r"^[A-Za-z]-\d{1,7}$"}})
    elif range_filter == "10-20":
        and_conditions.append({"cedula": {"$regex": r"^[A-Za-z]-1\d{7}$"}})
    elif range_filter == "20-30":
        and_conditions.append({"cedula": {"$regex": r"^[A-Za-z]-2\d{7}$"}})
    elif range_filter == "30+":
        and_conditions.append({"cedula": {"$regex": r"^[A-Za-z]-([3-9]\d{7}|\d{9,})$"}})

    pipeline = []
    if and_conditions:
        if len(and_conditions) == 1:
            pipeline.append({"$match": and_conditions[0]})
        else:
            pipeline.append({"$match": {"$and": and_conditions}})

    if sort_by == 'apariciones':
        pipeline.extend([
            {"$lookup": {
                "from": "persona_gaceta",
                "localField": "_id",
                "foreignField": "persona_id",
                "as": "_pg_tmp"
            }},
            {"$addFields": {
                "temp_count": {"$size": "$_pg_tmp"}
            }},
            {"$sort": {"temp_count": -1, "_id": -1}}
        ])

    facet_data = []
    if sort_by != 'apariciones':
        facet_data.append({"$sort": {"_id": -1}})
        
    facet_data.extend([
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
            "_id": 0,
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
        {"$sort": {"total_apariciones": -1} if sort_by == 'apariciones' else {"cedula": -1}}
    ])
    
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

    return jsonify({
        "data": data,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if limit > 0 else 0
    })

@app.route('/api/mine', methods=['POST'])
def api_mine():
    import subprocess
    import sys
    import json
    
    # Reset progress file
    progress_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "progress.json")
    try:
        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump({"percentage": 0, "message": "Iniciando extracción...", "status": "processing"}, f)
    except:
        pass

    # Runs the CLI script in the background as a module so 'src' imports work properly
    subprocess.Popen([sys.executable, "-m", "src.cli"])
    return jsonify({"status": "success", "message": "Extracción iniciada en segundo plano. Esto puede tardar varios minutos dependiendo de la cantidad de gacetas."})

@app.route('/api/progress', methods=['GET'])
def api_progress():
    import json
    progress_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "progress.json")
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return jsonify(data)
        except:
            return jsonify({"percentage": 0, "message": "Leyendo estado...", "status": "processing"})
    return jsonify({"percentage": 0, "message": "No hay tarea en progreso", "status": "idle"})

@app.route('/api/clear', methods=['POST'])
def api_clear():
    # Delete all documents in the related collections
    try:
        db.persona.delete_many({})
        db.gaceta.delete_many({})
        db.persona_gaceta.delete_many({})
        return jsonify({"status": "success", "message": "Base de datos limpiada con éxito."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    # Serve PDFs directly from the downloads folder
    downloads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
    return send_from_directory(downloads_dir, filename)

if __name__ == '__main__':
    # Start the Flask development server
    app.run(debug=True, port=5000)
