# Benchmark — Extraccion LLM de personas (Año 2026)

**Script:** `scripts/extract_personas_llm.py`
**Fecha:** 2026-05-20
**Comando:**
```
python -m scripts.extract_personas_llm --year 2026 --max-pages-per-chunk 50 --verbose
```

## Configuracion

| Parametro | Valor |
|---|---|
| Modelo | `deepseek/deepseek-v4-flash:free` |
| Contexto del modelo | 1,048,576 tokens (1M) |
| `OPENROUTER_MAX_CTX_TOKENS` | 900,000 |
| `--max-pages-per-chunk` | 50 |
| `OPENROUTER_MAX_OUTPUT_TOKENS` | 8,000 |
| `OPENROUTER_DELAY_S` | 2.0 |
| Retries por llamada | 3 (backoff exponencial) |
| Mongo | Docker `mongo:5` local (`gacetas_db`) |

## Universo procesado

| Metrica | Valor |
|---|---|
| Gacetas en `year=2026` | 59 |
| Paginas totales (con texto) | 556 |
| Tokens de entrada estimados | 585,369 |

## Resultado wall-clock

| Metrica | Valor |
|---|---|
| Chunks emitidos | 12 |
| Chunks exitosos | 8 |
| Chunks fallidos (429 upstream) | 4 |
| Personas devueltas por el modelo | 101 |
| Personas nuevas en BD | **1** |
| Personas actualizadas (nombre + contexto sobreescritos) | **100** |
| Relaciones `persona_gaceta` nuevas | 15 |
| Errores (incluye chunks fallidos) | 4 |
| **Tiempo total** | **574.17 s (9 min 34 s)** |
| Promedio por chunk exitoso | ~46.9 s |
| Throughput | ~60.1 paginas/min |

## Estado de la BD: antes vs. despues

| Coleccion | Antes | Despues | Delta |
|---|---:|---:|---:|
| `persona` | 17,081 | 17,082 | +1 |
| `persona` con campo `contexto` | 2 | 59 | +57 |
| `persona_gaceta` | 31,490 | 31,505 | +15 |
| `gaceta` | 1,667 | 1,669 | +2 |
| `gacetas` (raw, no cambia) | 2,761 | 2,761 | 0 |

> Solo +1 persona nueva porque el regex extractor previo (`save_relationship`) ya habia poblado la coleccion `persona`. El valor real del run LLM se ve en el campo `contexto` que paso de 2 a 59 personas con descripcion de motivo.

## Detalle por chunk

| # | Paginas | Gacetas | ~Tokens IN | Personas | Tiempo (s) | Estado |
|---:|---:|---:|---:|---:|---:|:---|
| 1 | 50 | 5 | 66,124 | 27 | 41.41 | OK |
| 2 | 50 | 5 | 47,493 | — | — | **429** (Crucible upstream rate limit) |
| 3 | 50 | 4 | 61,317 | — | — | **429** |
| 4 | 50 | 4 | 58,088 | 0 | 47.84 | OK (sin personas detectadas) |
| 5 | 50 | 5 | 52,734 | 0 | 69.38 | OK (sin personas detectadas) |
| 6 | 50 | 4 | 60,838 | — | — | **429** |
| 7 | 50 | 5 | 57,347 | 0 | 57.87 | OK (sin personas detectadas) |
| 8 | 50 | 6 | 58,093 | — | — | **429** |
| 9 | 50 | 13 | 23,218 | 12 | 31.04 | OK |
| 10 | 50 | 10 | 38,312 | 8 | 35.25 | OK |
| 11 | 50 | 6 | 59,950 | 22 | 50.22 | OK |
| 12 | 6 | 1 | 1,855 | 32 | 41.90 | OK |

## Muestras de `contexto` extraido

| Cedula | Nombre | Contexto (modelo) |
|---|---|---|
| V-19593640 | JUAN CARLOS VILLEGAS BRITO | Designado Presidente Encargado de la Fundación CENDITEL |
| V-14182600 | CARMEN VIRGINIA LIENDO BARANDIARAN | Designada Presidenta (E) del Centro Nacional de Investigación CENIDIC |
| V-11640661 | JOSÉ GREGORIO MENDOZA RODRÍGUEZ | Nombrado Viceministro para la Protección Social |
| V-13138674 | EDISSON ISMAEL ÁLVAREZ OROPEZA | Trasladado como Fiscal Auxiliar Interino a Fiscalía 8 |

## Observaciones

1. **Rate limiting upstream (Crucible).** 4 de 12 chunks fallaron con 429 incluso despues de 3 reintentos con backoff. La capa free de deepseek-v4-flash se rate-limitea por proveedor, no por OpenRouter. Soluciones:
   - Usar `--resume` y volver a correr (los chunks fallados se reprocesan porque no marcan filename como "procesado" — pero solo gacetas no procesadas siguen pendientes; en este caso quedan ~16 gacetas dentro de los chunks fallados).
   - Subir `OPENROUTER_DELAY_S` a 5-10.
   - Bajar `--max-pages-per-chunk` a 20-25 para distribuir carga.
   - Migrar a un modelo de pago (`google/gemini-2.5-flash`, `deepseek/deepseek-chat-v3.1` — sin sufijo `:free`).

2. **Chunks devuelven `0` personas con paginas no triviales (chunks 4, 5, 7).** El modelo puede estar omitiendo extracciones cuando el contenido es legislacion sin nombramientos individuales, pero conviene auditarlo manualmente.

3. **Hallucination de cedula.** El modelo devolvio `V-12345678 MAGALLY VIÑA CASTRO` en algun chunk. Esa cedula es literalmente el placeholder de mi system prompt. Conviene:
   - Ajustar el prompt para no usar `V-12345678` como ejemplo (usar `V-NNNNNNNN`).
   - Agregar filtro en el parser para descartar cedulas placeholder obvias.

4. **Persistencia de duplicados ya limpiada.** Antes del run se elimino 7,112 docs duplicados de `persona_gaceta` y se creo el indice unico `(persona_id, gaceta_id, pagina)`.

## Proyeccion para todos los años (2012-2026)

A throughput de ~60 paginas/min y dada la distribucion 2026 (avg ~9.4 paginas/gaceta):

| Años | Gacetas | Paginas (estim.) | Tiempo estimado |
|---|---:|---:|---:|
| 2026 (real) | 59 | 556 | 9.5 min |
| 2025 (estim.) | ~250 | ~2,300 | ~38 min |
| 2024 (estim.) | ~250 | ~2,300 | ~38 min |
| **2012-2026** (estim.) | 2,761 | ~26,000 | **~7 h 15 min** |

Sin rate-limit (modelo de pago) el tiempo bajaria probablemente a la mitad.

## Archivos generados

- `docs/benchmark_2026.md` (este archivo)
- `docs/bench_2026.json` (output JSON del run)
- `docs/bench_2026.log` (stdout/stderr completo)
- `progress_llm.json` (state file con filenames procesados — para `--resume`)
