# Vendata Gacetas Scraper (Node.js)

Scrapea **todos** los registros del buscador de Gacetas Oficiales de Vendata y los guarda en MongoDB, en una base de datos nueva llamada `vendata_gacetas`.

## ¿De dónde salen los datos?

La página pública `https://vendata.org/site/gacetas-oficiales/` es un WordPress que embebe el buscador alojado en `https://vendata.org/site/consultas/`. Ese buscador usa **DataTables con server-side processing** contra el endpoint:

```
https://vendata.org/site/consultas/index_processing.php
```

que responde JSON paginado (`recordsTotal`, `data`). El scraper recorre todas las páginas (~215.650 registros) y hace upsert en Mongo.

## Requisitos

- Node.js 18+ (probado con v24). Usa el `fetch` nativo.
- Una instancia de MongoDB accesible (por defecto `mongodb://localhost:27017`).

## Instalación

```powershell
cd vendata-scraper
npm install
```

## Uso

```powershell
# Scrapear todo desde cero
npm run scrape

# Reanudar si se cortó (idempotente, no duplica)
npm run resume

# Ver cuántos registros hay en la fuente y cuántos ya en la BD
npm run count
```

## Configuración (variables de entorno opcionales)

| Variable    | Default                      | Descripción                          |
|-------------|------------------------------|--------------------------------------|
| `MONGO_URI` | `mongodb://localhost:27017`  | Cadena de conexión a MongoDB         |
| `DB_NAME`   | `vendata_gacetas`            | Base de datos destino                |
| `COLLECTION`| `gacetas`                    | Colección destino                    |
| `PAGE_SIZE` | `5000`                       | Filas por petición                   |
| `DELAY_MS`  | `400`                        | Pausa entre peticiones (ms)          |
| `START_AT`  | `0`                          | Offset inicial manual                |

Ejemplo en PowerShell:

```powershell
$env:MONGO_URI = "mongodb://localhost:27017"; $env:PAGE_SIZE = "2000"; npm run scrape
```

## Esquema del documento guardado

```jsonc
{
  "_id": "1",                 // id de la fuente (clave primaria, evita duplicados)
  "id": "1",
  "numeroGaceta": "39624",
  "fechaGaceta": "25/02/2011",
  "fechaMaterial": "26/11/2010",
  "tipo": "Normativas (Reglamentos internos, etc)",
  "funcionario": "CONRADO JESUS ROVERO MORA",
  "cargo": "Viceministro",
  "contenido": "Se reforma la Comisión ...",
  "poder": "Ejecutivo",
  "ente": "Presidencia de la República",
  "organo": "...",
  "nivel1": "...", "nivel2": "...", "nivel3": "...",
  "fechaGacetaISO": "2011-02-25",
  "fechaMaterialISO": "2010-11-26",
  "detalleUrl": "https://vendata.org/site/consultas/gaceta_detalle.php?id=1",
  "raw": ["...","..."],       // fila completa original por si hace falta
  "scrapedAt": "2026-05-28T..."
}
```

## Reanudación y progreso

- Guarda en cada página (tras escribir en Mongo) un archivo **`progress.json`** con el offset por el que va:
  ```json
  { "nextStart": 50000, "lastDone": 50000, "total": 215650, "pageSize": 5000, "savedAt": "..." }
  ```
- `npm run resume` lee ese archivo y continúa **exactamente** donde quedó. Si no existe, estima el punto de reanudación por el número de documentos ya guardados en la BD.
- Al terminar, marca `"completed": true`.

## Protección anti-flood (rate limiting)

- Guarda **conforme avanza**: cada página se escribe en Mongo de inmediato, así que un corte no pierde lo ya descargado.
- Si el sitio responde **HTTP 429 / 403 / 503** (posible bloqueo), espera de forma creciente (30s, 60s, ...) antes de reintentar.
- Si recibe HTML en vez de JSON (captcha / página de bloqueo) lo detecta y reintenta.
- Si tras varios reintentos no logra avanzar, **se detiene limpiamente** indicando cuántos registros lleva y que reanudes con `npm run resume`.
- Para ir más suave, sube `DELAY_MS` y baja `PAGE_SIZE`, p. ej.: `$env:DELAY_MS="1500"; $env:PAGE_SIZE="1000"; npm run scrape`.

## Notas

- **Sin duplicados**: usa el `id` de la fuente como `_id` de MongoDB. La unicidad de `_id` que impone Mongo hace **imposible** la redundancia; reanudar reprocesa páginas sin duplicar (las reemplaza).
- **Codificación**: la fuente entrega texto con doble codificación UTF-8 (mojibake); el scraper lo repara automáticamente (`latin1 -> utf8`).
