"""
LLM-based persona extractor for Gaceta Oficial pages.

Reads pages from the configured Mongo collection of gacetas, batches multiple
pages into a single OpenRouter chat-completion call based on a configurable
input-token budget, asks the model to identify every natural person with a
Venezuelan cedula, and upserts into:
  - persona            ({cedula, nombre, contexto})
  - gaceta             ({numero_gaceta, filename, fecha})
  - persona_gaceta     ({persona_id, gaceta_id, pagina})

The "contexto" field is a 10-word summary of how/why the person appeared in
that specific gaceta/page.

Examples:
  python -m scripts.extract_personas_llm --year 2024
  python -m scripts.extract_personas_llm --year-range 2020-2024
  python -m scripts.extract_personas_llm --gaceta 43287
  python -m scripts.extract_personas_llm --filename 43287-2024-01-02-ORDINARIA.pdf
  python -m scripts.extract_personas_llm --year 2024 --dry-run
  python -m scripts.extract_personas_llm --year 2024 --resume

Required env (.env):
  OPENROUTER_API_KEY     OpenRouter secret key (sk-or-...)
  MONGO_URI              e.g. mongodb://localhost:27017/

Optional env:
  OPENROUTER_MODEL              default: google/gemini-2.5-pro
  OPENROUTER_BASE_URL           default: https://openrouter.ai/api/v1
  OPENROUTER_MAX_CTX_TOKENS     input token budget per call, default 200000
  OPENROUTER_MAX_OUTPUT_TOKENS  default 8000
  OPENROUTER_TIMEOUT_S          default 300
  OPENROUTER_DELAY_S            sleep between calls, default 1.0
  OPENROUTER_SITE_URL           sent as HTTP-Referer (OpenRouter analytics)
  OPENROUTER_APP_NAME           sent as X-Title (OpenRouter analytics)
  MONGO_DB_NAME                 default: gacetas_db
  MONGO_COLLECTION_NAME         default: gacetas
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional, Tuple

import requests
from pymongo import MongoClient, UpdateOne

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "gacetas_db")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "gacetas")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-pro")
DEFAULT_MAX_CTX_TOKENS = int(os.getenv("OPENROUTER_MAX_CTX_TOKENS", "200000"))
MAX_OUTPUT_TOKENS = int(os.getenv("OPENROUTER_MAX_OUTPUT_TOKENS", "8000"))
REQUEST_TIMEOUT = int(os.getenv("OPENROUTER_TIMEOUT_S", "300"))
RATE_DELAY = float(os.getenv("OPENROUTER_DELAY_S", "1.0"))
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "https://github.com/")
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "gacetas-extractor")

CHARS_PER_TOKEN = 4  # rough estimate for Spanish OCR text

SYSTEM_PROMPT = """Eres un extractor de informacion oficial de la Gaceta Oficial de la Republica Bolivariana de Venezuela.

OBJETIVO: leer fragmentos de paginas (texto producido por OCR, asi que puede tener errores) y devolver TODAS las entidades nombradas que aparezcan en el texto:
1) Personas naturales con cedula V- o E-.
2) Personas juridicas (empresas, fundaciones, asociaciones) con RIF J-, G- o P-.
3) Organismos publicos / gobierno nombrados de forma especifica (ministerios, viceministerios, institutos autonomos, comisiones, fundaciones del Estado, alcaldias, gobernaciones, fuerzas armadas, etc), aunque no tengan RIF visible.

Se EXHAUSTIVO. El texto viene de OCR, es comun encontrar:
- Cedulas/RIFs con 'O' en lugar de '0', 'l' en lugar de '1', puntos o espacios extra.
- Nombres partidos por salto de linea (junta NOMBRE + APELLIDOS).
- Razones sociales cortadas (junta lineas de la razon social).

Salida: SOLO un objeto JSON valido, sin markdown, sin texto antes ni despues:
{"personas": [ {"tipo": ..., "cedula": ..., "cedula_observada": ..., "nombre": ..., "cita": ..., "contexto": ..., "confidence": ..., "numero_gaceta": ..., "page_number": ...} ]}

Campos:
- tipo: "natural" (persona con V-/E-) | "juridica" (empresa con J-/G-/P-) | "organismo" (gobierno/ente publico).
- cedula: identificador canonico reconstruido.
    - natural: V- o E- + 6 a 9 digitos (V-19593640).
    - juridica: J- / G- / P- + 8-10 digitos con guion final opcional (J-12345678-9).
    - organismo: omite (deja "" o null).
- cedula_observada: cadena LITERAL como aparece en el texto (puede traer OCR roto). Si tipo=organismo, omite.
- nombre: nombre completo / razon social / nombre del organismo, reconstruido. Mayusculas si asi viene.
- cita: sub-cadena LITERAL del texto (max 200 caracteres) que contenga el identificador y/o nombre. Copia palabra por palabra del bloque, sin cambios.
- contexto: ~10 palabras del motivo o cargo (designado, ascendido, adjudicacion, autorizacion, etc).
- confidence: "alta" si todo claro, "media" si reconstruiste OCR o uniste lineas, "baja" si tienes duda.
- numero_gaceta y page_number: del encabezado "### GACETA <n> | FECHA <f> | PAGE <p>".

REGLAS DURAS:
- Las citas DEBEN existir literal en el bloque. No inventes.
- Los digitos de cedula/RIF observada deben provenir del texto. Si no estan, no emitas la entrada.
- Para "organismo": solo emite cuando el nombre esta concreto en el texto (no "El Ministro" generico, si "Ministerio del Poder Popular para la Salud").
- Personas con cargo pero SIN cedula concreta: no emitas como natural (a menos que el cargo refiera a un organismo nombrado, en cuyo caso emite el organismo).
- No incluyas texto fuera del JSON.

Si un bloque no tiene entidades extraibles: {"personas": []}.

Misma entidad en varias paginas: UNA entrada por page_number."""


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def build_page_block(numero_gaceta: str, fecha: str, page_number, text: str) -> str:
    header = f"### GACETA {numero_gaceta} | FECHA {fecha} | PAGE {page_number}"
    return f"{header}\n{text}\n"


@dataclass
class PageItem:
    numero_gaceta: str
    filename: str
    fecha: str
    year: Optional[int]
    page_number: object
    block: str
    tokens: int


def iter_pages(
    coll,
    *,
    year: Optional[int] = None,
    year_range: Optional[Tuple[int, int]] = None,
    numero_gaceta: Optional[str] = None,
    filename: Optional[str] = None,
    months: Optional[List[int]] = None,
    limit: Optional[int] = None,
    skip_filenames: Optional[set] = None,
) -> Iterator[PageItem]:
    q: dict = {}
    if year is not None:
        q["year"] = year
    if year_range is not None:
        q["year"] = {"$gte": year_range[0], "$lte": year_range[1]}
    if numero_gaceta is not None:
        q["numero_gaceta"] = numero_gaceta
    if filename is not None:
        q["filename"] = filename
    if months and year is not None:
        # filename pattern: NNNNN-YYYY-MM-DD-TYPE.pdf
        patterns = [f"-{year}-{m:02d}-" for m in months]
        regex = "|".join(re.escape(p) for p in patterns)
        q["filename"] = {"$regex": regex}

    cursor = coll.find(
        q,
        {"filename": 1, "numero_gaceta": 1, "fecha": 1, "year": 1, "pages": 1},
    )
    cursor = cursor.sort([("year", 1), ("numero_gaceta", 1)])
    if limit is not None:
        cursor = cursor.limit(limit)

    for doc in cursor:
        fn = doc.get("filename") or ""
        if skip_filenames and fn in skip_filenames:
            continue
        num = doc.get("numero_gaceta") or ""
        fecha = doc.get("fecha") or ""
        yr = doc.get("year")
        for p in doc.get("pages") or []:
            text = (p.get("text") or "").strip()
            if not text:
                continue
            pn = p.get("page_number")
            block = build_page_block(num, fecha, pn, text)
            yield PageItem(
                numero_gaceta=num,
                filename=fn,
                fecha=fecha,
                year=yr,
                page_number=pn,
                block=block,
                tokens=estimate_tokens(block),
            )


def chunk_by_tokens(
    pages: Iterable[PageItem],
    *,
    budget_tokens: int,
    overhead_tokens: int = 4000,
    max_pages_per_chunk: int = 200,
) -> Iterator[List[PageItem]]:
    """Pack pages into chunks <= budget_tokens, splitting oversized pages."""
    buf: List[PageItem] = []
    buf_tok = 0
    effective_budget = max(1000, budget_tokens - overhead_tokens)

    for p in pages:
        if p.tokens > effective_budget:
            if buf:
                yield buf
                buf, buf_tok = [], 0
            for sub in split_oversized(p, effective_budget):
                yield [sub]
            continue
        if buf and (buf_tok + p.tokens > effective_budget or len(buf) >= max_pages_per_chunk):
            yield buf
            buf, buf_tok = [], 0
        buf.append(p)
        buf_tok += p.tokens
    if buf:
        yield buf


def split_oversized(p: PageItem, budget_tokens: int) -> List[PageItem]:
    chars = budget_tokens * CHARS_PER_TOKEN
    text = p.block
    parts = [text[i:i + chars] for i in range(0, len(text), chars)]
    return [
        PageItem(
            numero_gaceta=p.numero_gaceta,
            filename=p.filename,
            fecha=p.fecha,
            year=p.year,
            page_number=p.page_number,
            block=part,
            tokens=estimate_tokens(part),
        )
        for part in parts
    ]


def _is_local_backend(url: str) -> bool:
    return any(h in url for h in ("localhost", "127.0.0.1", ":11434"))


def _ollama_native_base(url: str) -> str:
    base = url.rstrip("/")
    if base.endswith("/v1"):
        base = base[:-3]
    return base


def call_openrouter(model: str, user_content: str) -> str:
    is_local = _is_local_backend(OPENROUTER_BASE_URL)
    if is_local:
        return _call_ollama_native(model, user_content)
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": MAX_OUTPUT_TOKENS,
        "temperature": 0,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": OPENROUTER_SITE_URL,
        "X-Title": OPENROUTER_APP_NAME,
    }
    last_err = None
    for attempt in range(3):
        try:
            r = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            if r.status_code == 429 or r.status_code >= 500:
                last_err = RuntimeError(f"OpenRouter {r.status_code}: {r.text[:300]}")
                time.sleep(min(60, 2 ** attempt * 5))
                continue
            if r.status_code >= 400:
                raise RuntimeError(f"OpenRouter {r.status_code}: {r.text[:500]}")
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            last_err = e
            time.sleep(min(60, 2 ** attempt * 5))
    raise RuntimeError(f"OpenRouter call failed after retries: {last_err}")


def _call_ollama_native(model: str, user_content: str) -> str:
    """Use Ollama's /api/chat so num_ctx is honored."""
    base = _ollama_native_base(OPENROUTER_BASE_URL)
    num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "32768"))
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "stream": False,
        "format": "json",
        "options": {
            "num_ctx": num_ctx,
            "num_predict": MAX_OUTPUT_TOKENS,
            "temperature": 0,
        },
    }
    last_err = None
    for attempt in range(3):
        try:
            r = requests.post(
                f"{base}/api/chat",
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            if r.status_code >= 500:
                last_err = RuntimeError(f"Ollama {r.status_code}: {r.text[:300]}")
                time.sleep(min(30, 2 ** attempt * 3))
                continue
            if r.status_code >= 400:
                raise RuntimeError(f"Ollama {r.status_code}: {r.text[:500]}")
            data = r.json()
            return (data.get("message") or {}).get("content", "")
        except requests.RequestException as e:
            last_err = e
            time.sleep(min(30, 2 ** attempt * 3))
    raise RuntimeError(f"Ollama call failed after retries: {last_err}")


def parse_personas(raw: str) -> List[dict]:
    s = (raw or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    try:
        obj = json.loads(s)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", s)
        if not m:
            return []
        try:
            obj = json.loads(m.group(0))
        except json.JSONDecodeError:
            return []
    if isinstance(obj, dict):
        arr = obj.get("personas") or obj.get("data") or []
    elif isinstance(obj, list):
        arr = obj
    else:
        arr = []
    return [x for x in arr if isinstance(x, dict)]


CEDULA_RE = re.compile(r"^[VEve]-\d{4,12}$")
RIF_RE = re.compile(r"^[JGPjgp]-\d{6,10}(?:-\d)?$")

PLACEHOLDER_CEDULAS = frozenset({
    "V-12345678", "V-11111111", "V-00000000", "V-99999999",
    "V-87654321", "V-12121212",
    "E-12345678", "E-11111111", "E-00000000",
    "J-12345678", "J-12345678-9",
})


def is_placeholder_cedula(cedula: str) -> bool:
    if cedula in PLACEHOLDER_CEDULAS:
        return True
    digits = re.sub(r"\D", "", cedula)
    return len(set(digits)) <= 2  # 1111, 1212, 0000, 1234 (sequential covered separately)


def cedula_in_text(cedula: str, text: str) -> bool:
    """Check cedula appears in the text, tolerating dashes/spaces/dots between letter and digits."""
    if not cedula or not text:
        return False
    digits = re.sub(r"\D", "", cedula)
    letter = cedula[0].upper()
    if len(digits) < 6:
        return False
    text_norm = text.upper()
    text_digits_only = re.sub(r"[^0-9A-Z]", "", text_norm)
    if (letter + digits) in text_digits_only:
        return True
    if digits in text_digits_only:
        return True
    return False


def normalize_rif(raw) -> Optional[str]:
    """Normalize Venezuelan RIF (J-/G-/P-) into canonical form."""
    if raw is None:
        return None
    s = str(raw).strip().upper()
    if not s:
        return None
    s = re.sub(r"^(RIF[:\s]*|N[°O]\.?\s*)", "", s).strip()
    s = re.sub(r"[\s.,/_]", "", s)
    if not s:
        return None
    if "-" not in s and s[0] in ("J", "G", "P"):
        s = s[0] + "-" + s[1:]
    s = s.replace("--", "-")
    m = re.match(r"^([JGP])-?(\d{6,10})(-?(\d))?$", s)
    if not m:
        return None
    letter, digits, _, check = m.groups()
    if check:
        return f"{letter}-{digits}-{check}"
    return f"{letter}-{digits}"


def slugify_organismo(nombre: str) -> str:
    """Stable slug from organismo name to use as identifier."""
    s = (nombre or "").upper().strip()
    replacements = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ñ": "N", "Ü": "U"}
    for k, v in replacements.items():
        s = s.replace(k, v)
    s = re.sub(r"[^A-Z0-9]+", "_", s).strip("_")
    return ("ORG:" + s)[:200] if s else ""


def normalize_cedula(raw) -> Optional[str]:
    """Tolerant cedula normalizer.

    Accepts formats like:
      V-12345678 / V12345678 / V 12 345 678 / V.12.345.678
      E-1234567 / 12.345.678 / 12,345,678 / CI 12345678 / C.I.-12345678
      Cedula: 12345678 / N° 12345678
    Returns canonical "V-NNNNNNNN" or None if not a plausible cedula.
    """
    if raw is None:
        return None
    s = str(raw).strip().upper()
    if not s:
        return None
    # Strip common prefixes from text-style mentions ("CI", "C.I.", "CEDULA:", "N°", "No.")
    s = re.sub(r"^(C\.?\s*I\.?|CEDULA[:\s]*|N[°O]\.?\s*|NRO\.?\s*|N\.?\s*)", "", s).strip()
    # Remove dots, commas, spaces, slashes, underscores used as digit separators.
    s = re.sub(r"[\s.,/_]", "", s)
    if not s:
        return None
    # Strip surrounding garbage (letters that arent V/E)
    if s[0].isalpha() and s[0] not in ("V", "E"):
        # If it starts with a letter different from V/E but has digits, drop the letter.
        rest = re.sub(r"^[A-Z]+-?", "", s)
        if rest and rest[0].isdigit():
            s = "V-" + rest
    # Letter present?
    if "-" not in s and s[0] in ("V", "E"):
        s = s[0] + "-" + s[1:]
    elif "-" not in s and s[0].isdigit():
        s = "V-" + s
    s = s.replace("--", "-").replace("-.", "-")
    # Final shape check
    m = re.match(r"^([VE])-?(\d{4,12})$", s)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}"


def first_n_words(s: str, n: int = 10) -> str:
    words = re.findall(r"\S+", s or "")
    return " ".join(words[:n])


def _names_equivalent(a: str, b: str) -> bool:
    """Compara nombres tolerando mayusculas, espacios extra y acentos basicos."""
    if not a or not b:
        return False
    def norm(s):
        s = s.upper().strip()
        s = re.sub(r"\s+", " ", s)
        replacements = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ñ": "N", "Ü": "U"}
        for k, v in replacements.items():
            s = s.replace(k, v)
        return s
    return norm(a) == norm(b)


def upsert_persona(db, cedula: str, nombre: str, contexto: str, tipo: str = "natural") -> Tuple[object, str]:
    """Upsert con deteccion de conflictos. tipo: natural | juridica | organismo.

    Reglas:
    - Si el LLM trae cedula pero no nombre real → completar con el nombre existente en BD.
    - Si la misma cedula tiene OTRO nombre real en BD → flag por_verificar + lista conflictos.
    - Si OTRA cedula tiene el MISMO nombre → flag por_verificar en ambos.
    - contexto siempre se actualiza con el ultimo del modelo.
    """
    coll = db["persona"]
    contexto_short = first_n_words(contexto, 10)
    nombre_clean = (nombre or "").strip()
    is_real_name = nombre_clean and nombre_clean != "Desconocido"

    existing = coll.find_one({"cedula": cedula})

    if existing is None:
        # Cedula nueva. Antes de insertar revisamos si el nombre ya esta usado por otra cedula.
        conflict_with = None
        if is_real_name and tipo == "natural":
            conflict_with = coll.find_one({
                "cedula": {"$ne": cedula},
                "nombre": nombre_clean,
                "tipo": {"$ne": "organismo"},
            })
        doc = {
            "cedula": cedula,
            "nombre": nombre_clean or "Desconocido",
            "contexto": contexto_short,
            "tipo": tipo,
        }
        if conflict_with:
            doc["por_verificar"] = True
            doc["conflictos"] = [{
                "tipo": "mismo_nombre_otra_cedula",
                "otra_cedula": conflict_with.get("cedula"),
                "nombre": nombre_clean,
            }]
            coll.update_one(
                {"_id": conflict_with["_id"]},
                {
                    "$set": {"por_verificar": True},
                    "$addToSet": {"conflictos": {
                        "tipo": "mismo_nombre_otra_cedula",
                        "otra_cedula": cedula,
                        "nombre": nombre_clean,
                    }},
                },
            )
        res = coll.insert_one(doc)
        return res.inserted_id, ("conflict_created" if conflict_with else "created")

    # Cedula existente.
    existing_nombre = (existing.get("nombre") or "").strip()
    has_real_existing = existing_nombre and existing_nombre != "Desconocido"

    sets = {"contexto": contexto_short}
    add_conflict = None
    action = "updated"

    if not is_real_name and has_real_existing:
        # LLM no trajo nombre util → conservar el de BD (no sobrescribir).
        pass
    elif is_real_name and not has_real_existing:
        sets["nombre"] = nombre_clean
    elif is_real_name and has_real_existing and not _names_equivalent(existing_nombre, nombre_clean):
        # Mismo cedula, nombres distintos → marcar por_verificar y NO sobrescribir nombre.
        sets["por_verificar"] = True
        add_conflict = {
            "tipo": "mismo_cedula_otro_nombre",
            "nombre_actual": existing_nombre,
            "nombre_nuevo": nombre_clean,
        }
        action = "conflict_updated"
    # case equivalente: no cambio

    update = {"$set": sets}
    if add_conflict:
        update["$addToSet"] = {"conflictos": add_conflict}
    coll.update_one({"_id": existing["_id"]}, update)
    return existing["_id"], action


def upsert_gaceta(db, numero_gaceta: str, filename: str, fecha: str) -> object:
    coll = db["gaceta"]
    doc = coll.find_one({"numero_gaceta": numero_gaceta})
    if doc:
        patch = {}
        if not doc.get("filename") and filename:
            patch["filename"] = filename
        if not doc.get("fecha") and fecha:
            patch["fecha"] = fecha
        if patch:
            coll.update_one({"_id": doc["_id"]}, {"$set": patch})
        return doc["_id"]
    res = coll.insert_one({"numero_gaceta": numero_gaceta, "filename": filename, "fecha": fecha})
    return res.inserted_id


def upsert_relationship(db, persona_id, gaceta_id, pagina) -> None:
    coll = db["persona_gaceta"]
    coll.update_one(
        {"persona_id": persona_id, "gaceta_id": gaceta_id, "pagina": pagina},
        {"$setOnInsert": {"persona_id": persona_id, "gaceta_id": gaceta_id, "pagina": pagina}},
        upsert=True,
    )


def dedupe_persona_gaceta(db) -> int:
    """Elimina duplicados legacy en persona_gaceta dejando 1 por (persona_id, gaceta_id, pagina)."""
    pipeline = [
        {"$group": {
            "_id": {"p": "$persona_id", "g": "$gaceta_id", "pg": "$pagina"},
            "ids": {"$push": "$_id"},
            "n": {"$sum": 1},
        }},
        {"$match": {"n": {"$gt": 1}}},
    ]
    removed = 0
    coll = db["persona_gaceta"]
    for group in coll.aggregate(pipeline, allowDiskUse=True):
        ids = group["ids"]
        to_remove = ids[1:]
        if to_remove:
            res = coll.delete_many({"_id": {"$in": to_remove}})
            removed += res.deleted_count
    return removed


def ensure_indexes(db) -> None:
    db["persona"].create_index("cedula", unique=True)
    db["gaceta"].create_index("numero_gaceta", unique=True)
    try:
        db["persona_gaceta"].create_index(
            [("persona_id", 1), ("gaceta_id", 1), ("pagina", 1)],
            unique=True,
            name="uniq_persona_gaceta_pagina",
        )
    except Exception:
        removed = dedupe_persona_gaceta(db)
        print(f"[indexes] persona_gaceta dedupe: {removed} duplicados eliminados")
        db["persona_gaceta"].create_index(
            [("persona_id", 1), ("gaceta_id", 1), ("pagina", 1)],
            unique=True,
            name="uniq_persona_gaceta_pagina",
        )


def load_state(path: Optional[str]) -> dict:
    if not path or not os.path.exists(path):
        return {"processed_filenames": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"processed_filenames": []}


def save_state(path: Optional[str], state: dict) -> None:
    if not path:
        return
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def parse_year_range(s: str) -> Tuple[int, int]:
    m = re.match(r"^\s*(\d{4})\s*-\s*(\d{4})\s*$", s)
    if not m:
        raise argparse.ArgumentTypeError("year-range must be YYYY-YYYY")
    a, b = int(m.group(1)), int(m.group(2))
    if a > b:
        a, b = b, a
    return (a, b)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Extract personas from gacetas via OpenRouter LLM.")
    sel = ap.add_argument_group("seleccion")
    sel.add_argument("--year", type=int, help="Solo gacetas de este anio (campo 'year').")
    sel.add_argument("--year-range", type=parse_year_range, help="Rango YYYY-YYYY inclusivo.")
    sel.add_argument("--gaceta", help="Numero de gaceta exacto (campo numero_gaceta).")
    sel.add_argument("--filename", help="Filename exacto del PDF.")
    sel.add_argument("--months", help="Meses (comma-sep) dentro de --year. Ej: 6,7")
    sel.add_argument("--limit", type=int, help="Maximo de gacetas (no paginas) a procesar.")

    rt = ap.add_argument_group("runtime")
    rt.add_argument("--model", default=DEFAULT_MODEL, help=f"Modelo OpenRouter. Default: {DEFAULT_MODEL}")
    rt.add_argument("--max-ctx-tokens", type=int, default=DEFAULT_MAX_CTX_TOKENS,
                    help=f"Presupuesto de tokens de entrada por llamada. Default {DEFAULT_MAX_CTX_TOKENS}.")
    rt.add_argument("--max-pages-per-chunk", type=int, default=200,
                    help="Tope de paginas por chunk (seguridad).")
    rt.add_argument("--delay-s", type=float, default=RATE_DELAY,
                    help="Pausa entre llamadas (rate limiting).")
    rt.add_argument("--dry-run", action="store_true", help="No escribe a Mongo; imprime extracciones.")
    rt.add_argument("--resume", action="store_true", help="Continua desde state-file (omite filenames procesados).")
    rt.add_argument("--state-file", default="progress_llm.json", help="Archivo de progreso para reanudar.")
    rt.add_argument("--verbose", "-v", action="store_true")

    args = ap.parse_args(argv)

    if not OPENROUTER_API_KEY and not _is_local_backend(OPENROUTER_BASE_URL):
        print("ERROR: OPENROUTER_API_KEY no esta definido en el entorno.", file=sys.stderr)
        return 2
    if not MONGO_URI:
        print("ERROR: MONGO_URI no esta definido en el entorno.", file=sys.stderr)
        return 2

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    db = client[MONGO_DB_NAME]
    coll = db[MONGO_COLLECTION_NAME]

    try:
        client.server_info()
    except Exception as e:
        print(f"ERROR: no se pudo conectar a MongoDB: {e}", file=sys.stderr)
        return 2

    if not args.dry_run:
        try:
            ensure_indexes(db)
        except Exception as e:
            print(f"WARN: ensure_indexes fallo (continuando): {e}", file=sys.stderr)

    state = load_state(args.state_file) if args.resume else {"processed_filenames": []}
    skip = set(state.get("processed_filenames") or []) if args.resume else set()

    print(f"[cfg] model={args.model} ctx_budget={args.max_ctx_tokens} dry_run={args.dry_run} resume={args.resume}")
    print(f"[cfg] mongo={MONGO_DB_NAME}.{MONGO_COLLECTION_NAME}")

    months = None
    if args.months:
        months = [int(x.strip()) for x in args.months.split(",") if x.strip()]
    pages = iter_pages(
        coll,
        year=args.year,
        year_range=args.year_range,
        numero_gaceta=args.gaceta,
        filename=args.filename,
        months=months,
        limit=args.limit,
        skip_filenames=skip,
    )

    chunks = chunk_by_tokens(
        pages,
        budget_tokens=args.max_ctx_tokens,
        max_pages_per_chunk=args.max_pages_per_chunk,
    )

    stats = {
        "chunks": 0, "pages": 0, "personas_returned": 0,
        "personas_created": 0, "personas_updated": 0, "personas_skipped": 0,
        "relationships": 0, "errors": 0,
        "tokens_total": 0,
        "wall_seconds": 0.0,
    }
    per_chunk_times: List[dict] = []

    seen_files: set = set(state.get("processed_filenames") or [])
    t_start = time.time()

    for chunk in chunks:
        stats["chunks"] += 1
        stats["pages"] += len(chunk)
        content = "\n".join(p.block for p in chunk)
        approx_tokens = estimate_tokens(content)
        stats["tokens_total"] += approx_tokens
        gacetas_in_chunk = sorted({p.numero_gaceta for p in chunk})
        t_chunk = time.time()
        print(f"[chunk {stats['chunks']}] pages={len(chunk)} gacetas={len(gacetas_in_chunk)} ~tokens={approx_tokens}")
        if args.verbose:
            print(f"   gaceta_ids={gacetas_in_chunk[:8]}{'...' if len(gacetas_in_chunk) > 8 else ''}")

        try:
            raw = call_openrouter(args.model, content)
        except Exception as e:
            print(f"   ! API error: {e}", file=sys.stderr)
            stats["errors"] += 1
            if args.delay_s:
                time.sleep(args.delay_s)
            continue

        personas = parse_personas(raw)
        stats["personas_returned"] += len(personas)
        if args.verbose:
            print(f"   <- {len(personas)} personas devueltas")

        meta_index = {}
        page_text_index: dict = {}
        for p in chunk:
            key = (str(p.numero_gaceta), _coerce_page(p.page_number))
            meta_index[key] = p
            page_text_index[key] = p.block
        chunk_full_text = "\n".join(p.block for p in chunk)

        filtered: list = []
        normalized_chunk_text = chunk_full_text.upper()
        chunk_norm_collapsed = re.sub(r"\s+", " ", normalized_chunk_text)
        for entry in personas:
            tipo = (entry.get("tipo") or "natural").strip().lower()
            if tipo not in ("natural", "juridica", "organismo"):
                tipo = "natural"
            nombre = (entry.get("nombre") or "").strip()
            cita = (entry.get("cita") or "").strip()
            confidence = (entry.get("confidence") or "").strip().lower()
            num_g = str(entry.get("numero_gaceta") or "").strip()
            pn = _coerce_page(entry.get("page_number"))
            page_text = page_text_index.get((num_g, pn))
            target_text = page_text if page_text is not None else chunk_full_text

            cita_check = False
            if cita and len(cita) > 8:
                cita_norm = re.sub(r"\s+", " ", cita.upper()).strip()
                cita_check = cita_norm in chunk_norm_collapsed

            if tipo == "natural":
                cedula_corrected = normalize_cedula(entry.get("cedula"))
                cedula_observed = normalize_cedula(entry.get("cedula_observada") or entry.get("cedula"))
                cedula = cedula_corrected or cedula_observed
                if not cedula:
                    stats["dropped_no_cedula"] = stats.get("dropped_no_cedula", 0) + 1
                    continue
                if is_placeholder_cedula(cedula):
                    stats["dropped_placeholder"] = stats.get("dropped_placeholder", 0) + 1
                    if args.verbose:
                        print(f"   ! drop placeholder: {cedula} {nombre[:30]}")
                    continue
                literal_check = (
                    (cedula_observed and cedula_in_text(cedula_observed, target_text)) or
                    cedula_in_text(cedula, target_text)
                )
                if not literal_check and not cita_check:
                    stats["dropped_not_in_text"] = stats.get("dropped_not_in_text", 0) + 1
                    if args.verbose:
                        print(f"   ! drop hallucinated natural: {cedula} {nombre[:30]}")
                    continue
                identifier = cedula

            elif tipo == "juridica":
                rif_corrected = normalize_rif(entry.get("cedula"))
                rif_observed = normalize_rif(entry.get("cedula_observada") or entry.get("cedula"))
                rif = rif_corrected or rif_observed
                if not rif:
                    stats["dropped_no_rif"] = stats.get("dropped_no_rif", 0) + 1
                    continue
                if is_placeholder_cedula(rif):
                    stats["dropped_placeholder"] = stats.get("dropped_placeholder", 0) + 1
                    continue
                literal_check = (
                    (rif_observed and cedula_in_text(rif_observed, target_text)) or
                    cedula_in_text(rif, target_text)
                )
                if not literal_check and not cita_check:
                    stats["dropped_not_in_text"] = stats.get("dropped_not_in_text", 0) + 1
                    if args.verbose:
                        print(f"   ! drop hallucinated juridica: {rif} {nombre[:30]}")
                    continue
                identifier = rif

            else:  # organismo
                if not nombre or len(nombre) < 4:
                    stats["dropped_no_org_name"] = stats.get("dropped_no_org_name", 0) + 1
                    continue
                slug = slugify_organismo(nombre)
                if not slug:
                    stats["dropped_no_org_name"] = stats.get("dropped_no_org_name", 0) + 1
                    continue
                nombre_check = nombre.upper() in normalized_chunk_text or " ".join(nombre.upper().split()) in chunk_norm_collapsed
                if not nombre_check and not cita_check:
                    stats["dropped_not_in_text"] = stats.get("dropped_not_in_text", 0) + 1
                    if args.verbose:
                        print(f"   ! drop hallucinated organismo: {nombre[:50]}")
                    continue
                identifier = slug

            entry["_tipo"] = tipo
            entry["_cedula_norm"] = identifier
            entry["_nombre_norm"] = nombre
            entry["_confidence"] = confidence
            entry["_needs_review"] = (confidence == "baja") or (confidence == "media" and not cita_check)
            filtered.append(entry)

        stats["personas_kept"] = stats.get("personas_kept", 0) + len(filtered)
        if args.verbose:
            print(f"   = {len(filtered)} personas validadas (de {len(personas)})")

        for entry in filtered:
            cedula = entry["_cedula_norm"]
            nombre = entry["_nombre_norm"]
            tipo = entry["_tipo"]
            contexto = (entry.get("contexto") or "").strip()
            num_g = str(entry.get("numero_gaceta") or "").strip()
            pn = _coerce_page(entry.get("page_number"))
            needs_review = bool(entry.get("_needs_review"))
            if not nombre:
                nombre = "Desconocido"

            if args.dry_run:
                print(f"   [dry] {cedula} | {nombre[:50]} | g={num_g} p={pn} | {first_n_words(contexto, 10)}")
                continue

            meta = meta_index.get((num_g, pn))
            if meta is None:
                meta = chunk[0]

            try:
                pid, action = upsert_persona(db, cedula, nombre, contexto, tipo=tipo)
                stats[f"personas_{action}"] = stats.get(f"personas_{action}", 0) + 1
                if needs_review:
                    db["persona"].update_one(
                        {"_id": pid},
                        {"$set": {"por_verificar": True},
                         "$addToSet": {"conflictos": {
                             "tipo": "baja_confianza_modelo",
                             "nombre": nombre,
                             "numero_gaceta": meta.numero_gaceta,
                             "pagina": pn,
                         }}},
                    )
                    stats["needs_review"] = stats.get("needs_review", 0) + 1
                gid = upsert_gaceta(db, meta.numero_gaceta, meta.filename, meta.fecha)
                upsert_relationship(db, pid, gid, pn)
                stats["relationships"] += 1
            except Exception as e:
                print(f"   ! DB error for {cedula}: {e}", file=sys.stderr)
                stats["errors"] += 1

        for p in chunk:
            if p.filename:
                seen_files.add(p.filename)
        state["processed_filenames"] = sorted(seen_files)
        save_state(args.state_file, state)

        chunk_elapsed = time.time() - t_chunk
        per_chunk_times.append({
            "chunk": stats["chunks"],
            "pages": len(chunk),
            "gacetas": len(gacetas_in_chunk),
            "tokens": approx_tokens,
            "personas": len(personas),
            "seconds": round(chunk_elapsed, 2),
        })
        print(f"   t={chunk_elapsed:.1f}s")

        if args.delay_s:
            time.sleep(args.delay_s)

    stats["wall_seconds"] = round(time.time() - t_start, 2)
    summary = {"stats": stats, "per_chunk": per_chunk_times}
    print("[done] " + json.dumps(summary, indent=2, ensure_ascii=False))

    bench_path = os.environ.get("BENCH_OUT_JSON")
    if bench_path:
        with open(bench_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"[done] benchmark JSON -> {bench_path}")
    return 0


def _coerce_page(v):
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        try:
            return int(str(v).strip())
        except Exception:
            return v


if __name__ == "__main__":
    sys.exit(main())
