#!/usr/bin/env node
/**
 * Scraper del buscador de Gacetas Oficiales de Vendata.
 *
 * Fuente real de datos (descubierta tras analizar https://vendata.org/site/gacetas-oficiales/):
 *   La pagina publica es un WordPress que embebe el buscador en /site/consultas/.
 *   Ese buscador usa DataTables con "server-side processing" contra:
 *     https://vendata.org/site/consultas/index_processing.php
 *   El endpoint responde JSON tipo DataTables: { draw, recordsTotal, recordsFiltered, data: [[...columnas...]] }
 *   Total de registros al momento de escribir esto: ~215.650
 *
 * Guarda todos los registros en MongoDB -> base de datos "vendata_gacetas", coleccion "gacetas".
 * Idempotente: hace upsert por `id`, asi que se puede re-ejecutar o reanudar sin duplicar.
 *
 * Uso:
 *   node scrape.js              # scrapea todo desde el inicio
 *   node scrape.js --resume     # reanuda desde donde quedo (segun docs ya en la coleccion)
 *   node scrape.js --count      # solo muestra cuantos registros hay en la fuente y en la BD
 *
 * Variables de entorno (opcionales):
 *   MONGO_URI    (default: mongodb://localhost:27017)
 *   DB_NAME      (default: vendata_gacetas)
 *   COLLECTION   (default: gacetas)
 *   PAGE_SIZE    (default: 5000)   filas por peticion
 *   DELAY_MS     (default: 400)    pausa entre peticiones (cortesia con el servidor)
 *   START_AT     (default: 0)      offset inicial manual
 */

import { MongoClient } from "mongodb";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROGRESS_FILE = join(__dirname, "progress.json");

// ---------------------------------------------------------------------------
// Configuracion
// ---------------------------------------------------------------------------
const ENDPOINT = "https://vendata.org/site/consultas/index_processing.php";
const REFERER = "https://vendata.org/site/consultas/";

const MONGO_URI = process.env.MONGO_URI || "mongodb://localhost:27017";
const DB_NAME = process.env.DB_NAME || "vendata_gacetas";
const COLLECTION = process.env.COLLECTION || "gacetas";
const PAGE_SIZE = parseInt(process.env.PAGE_SIZE || "5000", 10);
const DELAY_MS = parseInt(process.env.DELAY_MS || "400", 10);
const MAX_RETRIES = 4;

const argv = process.argv.slice(2);
const RESUME = argv.includes("--resume");
const COUNT_ONLY = argv.includes("--count");

// ---------------------------------------------------------------------------
// Utilidades
// ---------------------------------------------------------------------------
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** Guarda en disco por que pagina/offset vamos, para poder reanudar. */
function saveProgress(p) {
  try {
    writeFileSync(PROGRESS_FILE, JSON.stringify(p, null, 2), "utf8");
  } catch (e) {
    console.warn(`  ! No se pudo escribir progress.json: ${e.message}`);
  }
}

/** Lee el progreso guardado (o null si no existe). */
function loadProgress() {
  if (!existsSync(PROGRESS_FILE)) return null;
  try {
    return JSON.parse(readFileSync(PROGRESS_FILE, "utf8"));
  } catch {
    return null;
  }
}

/**
 * Repara el "mojibake" de doble codificacion UTF-8.
 * El endpoint entrega cadenas como "ComisiÃ³n" (bytes UTF-8 de "o-acento"
 * interpretados como Latin-1). Re-codificando latin1 -> utf8 se recupera "Comision" con acento.
 * El ASCII puro queda intacto, asi que es seguro aplicarlo a todo.
 */
function fixEncoding(str) {
  if (typeof str !== "string" || str.length === 0) return str;
  // Solo intentamos reparar si hay codigos en el rango 0x80-0xFF (marcadores de mojibake).
  let suspect = false;
  for (let i = 0; i < str.length; i++) {
    const code = str.charCodeAt(i);
    if (code >= 0x80 && code <= 0xff) {
      suspect = true;
      break;
    }
  }
  if (!suspect) return str;
  try {
    return Buffer.from(str, "latin1").toString("utf8");
  } catch {
    return str;
  }
}

/**
 * Mapea una fila cruda (array de columnas de DataTables) a un documento estructurado.
 * Indices observados en la respuesta del endpoint:
 *   0  id                 7  contenido        13 nivel3
 *   1  numeroGaceta       8  poder            31 fechaGacetaISO  (yyyy-mm-dd)
 *   2  fechaGaceta        9  ente             32 fechaMaterialISO (yyyy-mm-dd)
 *   3  fechaMaterial     10  organo
 *   4  tipo              11  nivel1
 *   5  funcionario       12  nivel2
 *   6  cargo
 * Las columnas 14-30 son codigos internos de filtrado; se conservan en `raw`.
 */
function mapRow(cols) {
  const c = cols.map(fixEncoding);
  return {
    _id: c[0], // usamos el id de la fuente como clave primaria (idempotencia)
    id: c[0],
    numeroGaceta: c[1] || null,
    fechaGaceta: c[2] || null, // dd/mm/yyyy
    fechaMaterial: c[3] || null, // dd/mm/yyyy
    tipo: c[4] || null,
    funcionario: c[5] || null,
    cargo: c[6] || null,
    contenido: c[7] || null,
    poder: c[8] || null,
    ente: c[9] || null,
    organo: c[10] || null,
    nivel1: c[11] || null,
    nivel2: c[12] || null,
    nivel3: c[13] || null,
    fechaGacetaISO: c[31] || null, // yyyy-mm-dd
    fechaMaterialISO: c[32] || null,
    detalleUrl: `https://vendata.org/site/consultas/gaceta_detalle.php?id=${c[0]}`,
    raw: c, // fila completa por si se necesita algun codigo/columna extra
    scrapedAt: new Date(),
  };
}

/**
 * Pide una pagina al endpoint DataTables y devuelve { recordsTotal, data }.
 */
async function fetchPage(start, length, draw) {
  const url = `${ENDPOINT}?draw=${draw}&start=${start}&length=${length}`;
  let lastErr;
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), 60_000);
    try {
      const res = await fetch(url, {
        signal: controller.signal,
        headers: {
          "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
          "X-Requested-With": "XMLHttpRequest",
          Accept: "application/json, text/javascript, */*; q=0.01",
          Referer: REFERER,
        },
      });
      // Posible bloqueo por exceso de peticiones / proteccion del sitio.
      if (res.status === 429 || res.status === 403 || res.status === 503) {
        const wait = 30_000 * attempt; // espera larga y creciente
        console.warn(
          `  ! Posible bloqueo (HTTP ${res.status}) en start=${start}. Esperando ${wait / 1000}s antes de reintentar...`
        );
        await sleep(wait);
        throw new Error(`HTTP ${res.status} (rate-limit)`);
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const text = await res.text();
      let json;
      try {
        json = JSON.parse(text);
      } catch {
        // El servidor devolvio HTML (captcha / pagina de bloqueo) en vez de JSON.
        throw new Error("Respuesta no-JSON (posible captcha o pagina de bloqueo)");
      }
      if (!Array.isArray(json.data)) throw new Error("Respuesta sin campo 'data'");
      return { recordsTotal: json.recordsTotal, data: json.data };
    } catch (err) {
      lastErr = err;
      const backoff = 2000 * attempt;
      console.warn(
        `  ! Error en start=${start} (intento ${attempt}/${MAX_RETRIES}): ${err.message}. Reintentando en ${backoff}ms...`
      );
      await sleep(backoff);
    } finally {
      clearTimeout(t);
    }
  }
  throw new Error(`Fallo definitivo en start=${start}: ${lastErr?.message}`);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  const client = new MongoClient(MONGO_URI);
  await client.connect();
  const col = client.db(DB_NAME).collection(COLLECTION);

  // Indices utiles para consultas posteriores (idempotente)
  await col.createIndexes([
    { key: { numeroGaceta: 1 } },
    { key: { fechaGacetaISO: 1 } },
    { key: { tipo: 1 } },
    { key: { funcionario: 1 } },
    { key: { poder: 1 } },
  ]);

  // Sondeo inicial para conocer el total en la fuente
  const probe = await fetchPage(0, 1, 1);
  const total = probe.recordsTotal;
  const inDb = await col.countDocuments();
  console.log(`Fuente: ${total} registros | Base de datos (${DB_NAME}.${COLLECTION}): ${inDb} registros`);

  if (COUNT_ONLY) {
    await client.close();
    return;
  }

  let start = parseInt(process.env.START_AT || "0", 10);
  if (RESUME) {
    const prog = loadProgress();
    if (prog && Number.isInteger(prog.nextStart)) {
      // Reanudar exactamente donde quedo segun el archivo de progreso.
      start = prog.nextStart;
      console.log(`Reanudando desde progress.json -> start=${start} (guardado: ${prog.savedAt})`);
    } else {
      // Sin archivo de progreso: estimamos por el numero de docs ya guardados.
      start = Math.max(0, Math.floor(inDb / PAGE_SIZE) * PAGE_SIZE);
      console.log(`Sin progress.json; reanudando por conteo de BD -> start=${start}`);
    }
  }

  let draw = 2;
  let upserted = 0;
  const t0 = Date.now();

  while (start < total) {
    let data;
    try {
      ({ data } = await fetchPage(start, PAGE_SIZE, draw++));
    } catch (err) {
      // Fallo definitivo (probable bloqueo del sitio). Lo descargado YA esta guardado.
      const saved = await col.countDocuments();
      console.error(`\n! Detenido en start=${start}: ${err.message}`);
      console.error(`  Ya hay ${saved} registros guardados en ${DB_NAME}.${COLLECTION} (sin duplicados).`);
      console.error(`  Reanuda mas tarde con:  npm run resume`);
      await client.close();
      process.exit(2);
    }

    if (data.length === 0) {
      console.log("Pagina vacia; fin.");
      break;
    }

    // Sin duplicados: _id = id de la fuente. replaceOne+upsert reemplaza si ya existe,
    // inserta si es nuevo. MongoDB impone unicidad de _id, asi que no hay redundancia
    // aunque una pagina se reprocese al reanudar.
    const docs = data.map(mapRow).filter((d) => d._id != null && d._id !== "");
    const ops = docs.map((doc) => ({
      replaceOne: { filter: { _id: doc._id }, replacement: doc, upsert: true },
    }));
    const result = await col.bulkWrite(ops, { ordered: false });
    upserted += (result.upsertedCount || 0) + (result.modifiedCount || 0);

    const done = Math.min(start + data.length, total);
    const pct = ((done / total) * 100).toFixed(1);
    const rate = done / ((Date.now() - t0) / 1000);
    const eta = rate > 0 ? Math.round((total - done) / rate) : 0;
    console.log(
      `[${done}/${total}] ${pct}%  (+${data.length} filas)  ~${rate.toFixed(0)} reg/s  ETA ${eta}s`
    );

    start += PAGE_SIZE;
    // Persistimos el progreso en disco DESPUES de guardar la pagina en Mongo.
    saveProgress({
      nextStart: start,
      lastDone: done,
      total,
      pageSize: PAGE_SIZE,
      savedAt: new Date().toISOString(),
    });

    if (start < total) await sleep(DELAY_MS);
  }

  saveProgress({
    nextStart: total,
    lastDone: total,
    total,
    pageSize: PAGE_SIZE,
    completed: true,
    savedAt: new Date().toISOString(),
  });

  const finalCount = await col.countDocuments();
  console.log(`\n=== Listo ===`);
  console.log(`Documentos en ${DB_NAME}.${COLLECTION}: ${finalCount}`);
  console.log(`Tiempo total: ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  await client.close();
}

main().catch((err) => {
  console.error("ERROR FATAL:", err);
  process.exit(1);
});
