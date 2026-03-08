import sys
import os
import unittest
from unittest.mock import patch

# Add the root directory to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from src.api.v1.schemas import parse_search_request

class TestApiV1(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_parse_search_request(self):
        """Prueba que los parámetros se parsean y limitan correctamente."""
        args = {"q": "  Juan ", "limit": "500", "page": "-1"}
        parsed = parse_search_request(args)
        self.assertEqual(parsed["query"], "Juan")
        self.assertEqual(parsed["limit"], 100)  # Max limit
        self.assertEqual(parsed["page"], 1)     # Min page

    @patch('src.api.v1.routes.query_personas_mongo')
    @patch('src.api.v1.routes.get_db')
    def test_buscar_personas_endpoint(self, mock_get_db, mock_query):
        """Prueba el endpoint de la API asegurando que formatea la respuesta esperada."""
        # Mocking mongo results
        mock_data = [
            {
                "_id": "dummy_id",
                "cedula": "V-12345678",
                "nombre": "JUAN PEREZ",
                "total_apariciones": 1,
                "apariciones": [
                    {
                        "numero_gaceta": "12345",
                        "fecha": "2023-01-01",
                        "pagina": 5,
                        "filename": "gaceta_12345.pdf"
                    }
                ]
            }
        ]
        mock_query.return_value = (mock_data, 1) # data, total

        response = self.client.get('/api/v1/personas?cedula=V-12345678')
        self.assertEqual(response.status_code, 200)
        
        json_data = response.get_json()
        self.assertEqual(json_data["estado"], "exito")
        self.assertEqual(json_data["paginacion"]["total_registros"], 1)
        self.assertEqual(len(json_data["datos"]), 1)
        
        # Validando la estructura devuelta
        persona = json_data["datos"][0]
        self.assertEqual(persona["documento_identidad"], "V-12345678")
        self.assertEqual(persona["nombre_completo"], "JUAN PEREZ")
        self.assertEqual(persona["total_menciones"], 1)
        self.assertEqual(persona["menciones_gaceta"][0]["numero_gaceta"], "12345")

if __name__ == '__main__':
    unittest.main()
