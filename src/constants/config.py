"""
Configuration from environment (MongoDB). Easy to change per environment.
"""
import os

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "gacetas_db")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "gacetas")
