#!/usr/bin/env node
/**
 * Exporta la coleccion vendata_gacetas.gacetas a:
 *   1) exports/vendata_gacetas.backup.ndjson  -> backup completo (1 doc JSON por linea, incluye `raw`)
 *   2) exports/vendata_gacetas.csv            -> CSV limpio para compartir (sin codigos internos)
 *
 * Streaming via cursor para no cargar todo en memoria.
 * El CSV lleva BOM UTF-8 para que Excel muestre bien los acentos.
 *
 * Uso: node export.js
 */

import { MongoClient } from "mongodb";
import { createWriteStream, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = join(__dirname, "exports");

const MONGO_URI = process.env.MONGO_URI || "mongodb://localhost:27017";
const DB_NAME = process.env.DB_NAME || "vendata_gacetas";
const COLLECTION = process.env.COLLECTION || "gacetas";

// Columnas del CSV (orden y encabezados legibles)
const CSV_COLUMNS = [
  ["id", "ID"],
  ["numeroGaceta", "Numero Gaceta"],
  ["fechaGaceta", "Fecha Gaceta"],
  ["fechaMaterial", "Fecha Material"],
  ["tipo", "Tipo"],
  ["funcionario", "Funcionario"],
  ["cargo", "Cargo"],
  ["contenido", "Contenido"],
  ["poder", "Poder"],
  ["ente", "Ente"],
  ["organo", "Organo"],
  ["nivel1", "Nivel 1"],
  ["nivel2", "Nivel 2"],
  ["nivel3", "Nivel 3"],
  ["fechaGacetaISO", "Fecha Gaceta (ISO)"],
  ["detalleUrl", "URL Detalle"],
];

/** Escapa un valor para CSV (comillas dobles, saltos de linea, comas). */
function csvCell(value) {
  if (value == null) return '""';
  const s = String(value).replace(/"/g, '""');
  return `"${s}"`;
}

async function main() {
  mkdirSync(OUT_DIR, { recursive: true });
  const client = new MongoClient(MONGO_URI);
  await client.connect();
  const col = client.db(DB_NAME).collection(COLLECTION);

  const total = await col.countDocuments();
  console.log(`Exportando ${total} documentos de ${DB_NAME}.${COLLECTION} ...`);

  const ndjsonPath = join(OUT_DIR, "vendata_gacetas.backup.ndjson");
  const csvPath = join(OUT_DIR, "vendata_gacetas.csv");
  const ndjson = createWriteStream(ndjsonPath, { encoding: "utf8" });
  const csv = createWriteStream(csvPath, { encoding: "utf8" });

  // BOM UTF-8 para Excel + fila de encabezados
  csv.write("﻿");
  csv.write(CSV_COLUMNS.map(([, label]) => csvCell(label)).join(",") + "\r\n");

  // Orden natural de insercion (ya es ascendente por id porque se scrapeo en orden).
  const cursor = col.find({});
  let n = 0;
  for await (const doc of cursor) {
    ndjson.write(JSON.stringify(doc) + "\n");
    csv.write(CSV_COLUMNS.map(([key]) => csvCell(doc[key])).join(",") + "\r\n");
    if (++n % 25000 === 0) console.log(`  ${n}/${total}`);
  }

  await new Promise((res) => ndjson.end(res));
  await new Promise((res) => csv.end(res));
  await client.close();

  console.log(`\n=== Exportacion lista (${n} filas) ===`);
  console.log(`Backup: ${ndjsonPath}`);
  console.log(`CSV:    ${csvPath}`);
}

main().catch((err) => {
  console.error("ERROR:", err);
  process.exit(1);
});
