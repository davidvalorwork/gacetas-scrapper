"""
CLI entry: parse args, connect repository, run search services, print and save results to MongoDB.
Run with: python -m src   or   python src/cli.py (from project root).
"""
import sys
import argparse

from dotenv import load_dotenv
load_dotenv()

from src.adapters.mongodb import MongoGacetaRepository
from src.services.search_service import search_cedulas


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search gacetas for Venezuelan cédulas and store them in MongoDB."
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit number of gacetas to scan (for testing)")
    args = parser.parse_args()

    try:
        repository = MongoGacetaRepository()
        total_gacetas = repository.count()
    except RuntimeError as e:
        print(f"⚠️  {e}", file=sys.stderr)
        print("Configura MONGO_URI en .env", file=sys.stderr)
        return 1

    to_scan = min(args.limit, total_gacetas) if args.limit else total_gacetas
    print(f"Alcance: {to_scan} gacetas (de {total_gacetas} registradas).\n")

    print("Buscando cédulas y nombres, y guardando en MongoDB...")
    cedulas = search_cedulas(repository, limit_gacetas=args.limit)
    
    saved_count = 0
    for i, r in enumerate(cedulas):
        if i < 20:
            print(f"  [{i+1}] Gaceta {r['numero_gaceta']} p.{r.get('page_number')} | {r['cedula']} -> Nombre: {r.get('nombre')}")
        elif i == 20:
            print(f"  ... y {len(cedulas) - 20} más.")
            
        try:
            repository.save_relationship(
                cedula=r["cedula"],
                nombre=r.get("nombre", "Desconocido"),
                numero_gaceta=r["numero_gaceta"],
                filename=r["gaceta"],
                pagina=r.get("page_number")
            )
            saved_count += 1
        except Exception as e:
            print(f"⚠️ Error guardando en BD para cédula {r['cedula']}: {e}", file=sys.stderr)

    # --- Resumen final ---
    print("\n" + "=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    print(f"Número total de cédulas encontradas: {len(cedulas)}")
    print(f"Relaciones guardadas en MongoDB: {saved_count}")
    print("Colecciones actualizadas: 'persona', 'gaceta', 'persona_gaceta'.")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
