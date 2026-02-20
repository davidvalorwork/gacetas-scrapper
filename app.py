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
    match_stage = {}
    if query:
        # Case insensitive search on cedula or name
        match_stage = {
            "$or": [
                {"cedula": {"$regex": query, "$options": "i"}},
                {"nombre": {"$regex": query, "$options": "i"}}
            ]
        }
        
    pipeline = [
        {"$match": match_stage},
        {"$lookup": {
            "from": "persona_gaceta",
            "localField": "_id",
            "foreignField": "persona_id",
            "as": "relationships"
        }},
        {"$unwind": "$relationships"},
        {"$lookup": {
            "from": "gaceta",
            "localField": "relationships.gaceta_id",
            "foreignField": "_id",
            "as": "gaceta_info"
        }},
        {"$unwind": "$gaceta_info"},
        {"$project": {
            "_id": 0,
            "cedula": 1,
            "nombre": 1,
            "numero_gaceta": "$gaceta_info.numero_gaceta",
            "filename": "$gaceta_info.filename",
            "pagina": "$relationships.pagina"
        }},
        {"$limit": 100}
    ]
    
    results = list(db.persona.aggregate(pipeline))
    return jsonify(results)

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    # Serve PDFs directly from the downloads folder
    downloads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
    return send_from_directory(downloads_dir, filename)

if __name__ == '__main__':
    # Start the Flask development server
    app.run(debug=True, port=5000)
