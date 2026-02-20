"""
Adapter: MongoDB implementation of GacetaRepository.
Reads from the same collection used by ocr_processor.
"""
from typing import Iterator, Optional

from src.constants.config import MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION_NAME
from src.ports.repository import GacetaDocument, GacetaPage


class MongoGacetaRepository:
    """Reads all gacetas and all pages from MongoDB."""

    def __init__(
        self,
        uri: Optional[str] = None,
        db_name: Optional[str] = None,
        collection_name: Optional[str] = None,
    ) -> None:
        self._uri = uri or MONGO_URI
        self._db_name = db_name or MONGO_DB_NAME
        self._collection_name = collection_name or MONGO_COLLECTION_NAME
        self._client = None
        self._collection = None

    def _ensure_connected(self):
        if self._collection is not None:
            return
        if not self._uri:
            raise RuntimeError("MONGO_URI not set")
        try:
            from pymongo import MongoClient
            self._client = MongoClient(self._uri, serverSelectionTimeoutMS=5000)
            db = self._client[self._db_name]
            self._collection = db[self._collection_name]
            self._client.server_info()
        except ImportError as e:
            raise RuntimeError("pymongo not installed. pip install pymongo") from e
        except Exception as e:
            raise RuntimeError(f"Cannot connect to MongoDB: {e}") from e

    def count(self) -> int:
        self._ensure_connected()
        return self._collection.count_documents({})

    def iter_gacetas(self, limit: Optional[int] = None) -> Iterator[GacetaDocument]:
        self._ensure_connected()
        cursor = self._collection.find(
            {},
            {"filename": 1, "numero_gaceta": 1, "fecha": 1, "year": 1, "pages": 1, "full_text": 1},
        )
        if limit is not None:
            cursor = cursor.limit(limit)
        for doc in cursor:
            pages = doc.get("pages") or []
            yield GacetaDocument(
                filename=doc.get("filename", ""),
                numero_gaceta=doc.get("numero_gaceta", ""),
                fecha=doc.get("fecha", ""),
                year=doc.get("year"),
                pages=[
                    GacetaPage(
                        page_number=p.get("page_number"),
                        text=(p.get("text") or ""),
                    )
                    for p in pages
                ],
                full_text=doc.get("full_text") or "",
            )

    def save_relationship(self, cedula: str, nombre: str, numero_gaceta: str, filename: str, fecha: str, pagina: Optional[int]):
        """Saves the relationship in MongoDB collections: persona, gaceta, persona_gaceta."""
        self._ensure_connected()
        db = self._client[self._db_name]
        
        # 1. Save or get Persona
        persona_coll = db["persona"]
        persona_doc = persona_coll.find_one({"cedula": cedula})
        if not persona_doc:
            res = persona_coll.insert_one({"cedula": cedula, "nombre": nombre})
            persona_id = res.inserted_id
        else:
            persona_id = persona_doc["_id"]
            if persona_doc.get("nombre") == "Desconocido" and nombre != "Desconocido":
                persona_coll.update_one({"_id": persona_id}, {"$set": {"nombre": nombre}})
                
        # 2. Save or get Gaceta metadata
        gaceta_coll = db["gaceta"]
        gaceta_doc = gaceta_coll.find_one({"numero_gaceta": numero_gaceta})
        if not gaceta_doc:
            res = gaceta_coll.insert_one({"numero_gaceta": numero_gaceta, "filename": filename, "fecha": fecha})
            gaceta_id = res.inserted_id
        else:
            gaceta_id = gaceta_doc["_id"]
            update_fields = {}
            if "filename" not in gaceta_doc:
                update_fields["filename"] = filename
            if "fecha" not in gaceta_doc:
                update_fields["fecha"] = fecha
            if update_fields:
                gaceta_coll.update_one({"_id": gaceta_id}, {"$set": update_fields})
            
        # 3. Create Persona-Gaceta Relationship
        rel_coll = db["persona_gaceta"]
        rel_coll.insert_one({
            "persona_id": persona_id,
            "gaceta_id": gaceta_id,
            "pagina": pagina
        })
