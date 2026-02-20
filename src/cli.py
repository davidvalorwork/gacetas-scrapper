"""
CLI entry: parse args, connect repository, run search services, print and/or save results.
Run with: python -m src   or   python src/cli.py (from project root).
"""
import sys
import json
import argparse
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from src.adapters.mongodb import MongoGacetaRepository
from src.services.search_service import (
    search_cedulas,
    search_military,
    search_rank_name_ci_title,
    search_ciudadano_rank_name_ci_cargo,
)
from src.utils.csv_export import build_csv_rows, write_csv, CSV_COLUMNS


def _military_two_word_only(military: list) -> list:
    return [r for r in military if len((r.get("term") or "").split()) == 2]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search gacetas for Venezuelan cédulas and/or military mentions."
    )
    parser.add_argument("--cedulas", action="store_true", help="Search for cédulas (B/V/E/J/G + digits)")
    parser.add_argument("--military", action="store_true", help="Search for military terms")
    parser.add_argument("--out", type=str, help="Write results to JSON file")
    parser.add_argument("--csv", type=str, metavar="FILE", help="Write CSV with columns: Nombres, Apellidos, Cédula, Rango, Nombramiento, Número Gaceta, Fecha")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of gacetas to scan (for testing)")
    args = parser.parse_args()

    if not args.cedulas and not args.military:
        args.cedulas = True
        args.military = True

    try:
        repository = MongoGacetaRepository()
        total_gacetas = repository.count()
    except RuntimeError as e:
        print(f"⚠️  {e}", file=sys.stderr)
        print("Configura MONGO_URI en .env", file=sys.stderr)
        return 1
    if args.limit is not None:
        to_scan = min(args.limit, total_gacetas)
        print(f"Alcance: {to_scan} gacetas (de {total_gacetas} registradas), todas las páginas de cada una.\n")
    else:
        print(f"Alcance: todas las gacetas registradas ({total_gacetas}), todas las páginas de cada una.\n")

    all_results = {
        "cedulas": [],
        "military": [],
        "rank_name_ci": [],
        "ciudadano_rank_name_ci": [],
        "meta": {"limit_gacetas": args.limit, "total_gacetas_in_db": total_gacetas},
    }
    cedulas: list = []
    military: list = []
    rank_name_ci: list = []
    ciudadano_rank_name_ci: list = []

    if args.cedulas:
        print("Buscando cédulas venezolanas (B/V/E/J/G + dígitos)...")
        cedulas = search_cedulas(repository, limit_gacetas=args.limit)
        all_results["cedulas"] = cedulas
        for i, r in enumerate(cedulas[:20]):
            print(f"  [{i+1}] {r['gaceta']} p.{r.get('page_number')} | {r['cedula']}")
        if len(cedulas) > 20:
            print(f"  ... y {len(cedulas) - 20} más.")

    if args.military:
        print("\nBuscando menciones militares...")
        military = search_military(repository, limit_gacetas=args.limit)
        all_results["military"] = military
        military_2 = _military_two_word_only(military)
        print(f"  Total menciones: {len(military)}. De 2 palabras (rango/tipo): {len(military_2)}")
        for i, r in enumerate(military_2[:30]):
            print(f"  {r['term']!r}  |  {r['gaceta']}  p.{r.get('page_number')}")
        if len(military_2) > 30:
            print(f"  ... y {len(military_2) - 30} más.")

    print("\nBuscando formato Rango + Nombre + C.I + Cargo (ej.: General de Brigada NOMBRE, C.I Nº 12.685.318, Presidente Ejecutivo)...")
    rank_name_ci = search_rank_name_ci_title(repository, limit_gacetas=args.limit)
    all_results["rank_name_ci"] = rank_name_ci
    print(f"  Encontrados: {len(rank_name_ci)}")
    for i, r in enumerate(rank_name_ci[:15]):
        print(f"  {r['rank']} | {r['full_name']} | C.I {r['ci_number']} | {r['title']} | {r['gaceta']} p.{r.get('page_number')}")
    if len(rank_name_ci) > 15:
        print(f"  ... y {len(rank_name_ci) - 15} más.")

    print("\nBuscando formato 'En relación a la ciudadana/o RANGO NOMBRE, titular de la cédula... (CARGO)'...")
    ciudadano_rank_name_ci = search_ciudadano_rank_name_ci_cargo(repository, limit_gacetas=args.limit)
    all_results["ciudadano_rank_name_ci"] = ciudadano_rank_name_ci
    print(f"  Encontrados: {len(ciudadano_rank_name_ci)}")
    for i, r in enumerate(ciudadano_rank_name_ci[:10]):
        cargo_preview = (r.get("cargo") or "")[:50]
        if (r.get("cargo") or "").strip():
            cargo_preview = cargo_preview + "..." if len((r.get("cargo") or "")) > 50 else cargo_preview
        print(f"  {r['rank']} {r['full_name']} | C.I {r['ci_full']} | {cargo_preview} | {r['gaceta']} p.{r.get('page_number')}")
    if len(ciudadano_rank_name_ci) > 10:
        print(f"  ... y {len(ciudadano_rank_name_ci) - 10} más.")

    # --- Resumen final ---
    print("\n" + "=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    if args.cedulas and cedulas:
        total_ced = len(cedulas)
        todas_cedulas = [r["cedula"] for r in cedulas]
        print(f"Número total de cédulas encontradas: {total_ced}")
        print(f"Cédulas (array): {todas_cedulas}")
    if args.military and military:
        military_2 = _military_two_word_only(military)
        print(f"Menciones militares (solo 2 palabras / rango): {len(military_2)}")
        terminos_2 = list(dict.fromkeys(r["term"] for r in military_2))
        print(f"Rangos/tipos (únicos): {terminos_2}")
    if rank_name_ci:
        print(f"Formato Rango+Nombre+C.I+Cargo: {len(rank_name_ci)}")
    if ciudadano_rank_name_ci:
        print(f"Formato 'En relación a la ciudadana/o' + Rango+Nombre+C.I+(Cargo): {len(ciudadano_rank_name_ci)}")
    print("=" * 60)

    if args.out:
        outpath = Path(args.out)
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\nJSON guardado en: {outpath}")

    if args.csv:
        rows = build_csv_rows(
            cedulas,
            military,
            rank_name_ci=rank_name_ci,
            ciudadano_rank_name_ci=ciudadano_rank_name_ci,
            military_two_words_only=True,
        )
        write_csv(Path(args.csv), rows)
        print(f"\nCSV guardado en: {args.csv}  (columnas: {', '.join(CSV_COLUMNS)})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
