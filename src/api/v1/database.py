import os
from pymongo import MongoClient
from pymongo.database import Database

def get_db() -> Database:
    """Obtiene la instancia de MongoDB conectada."""
    mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    db_name = os.environ.get("MONGO_DB_NAME", "gacetas_db")
    client = MongoClient(mongo_uri)
    return client[db_name]
