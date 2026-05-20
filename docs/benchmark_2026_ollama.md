# Benchmark — Extraccion LLM local con Ollama (Año 2026)

**Script:** `scripts/extract_personas_llm.py`
**Fecha:** 2026-05-20
**Modelo:** `gemma3:12b-it-q4_K_M` via Ollama
**Hardware:** RTX 3060 12GB + i7-12700KF + 32GB RAM

## Configuracion del run

| Parametro | Valor |
|---|---|
| Modelo | `gemma3:12b-it-q4_K_M` (~8.1GB en disco, todo en VRAM) |
| Backend | Ollama 0.24.0 local (`http://localhost:11434`) |
| `OLLAMA_NUM_CTX` | 16,384 |
| `--max-pages-per-chunk` | 8 |
| `--max-ctx-tokens` | 12,000 |
| `OPENROUTER_DELAY_S` | 0 (sin rate-limit, es local) |
| Temperatura | 0 |
| Mongo | Docker `mongo:5` local (`gacetas_db`) |

## Comando

```bash
OPENROUTER_BASE_URL=http://localhost:11434 \
OPENROUTER_MODEL=gemma3:12b-it-q4_K_M \
OLLAMA_NUM_CTX=16384 \
OPENROUTER_DELAY_S=0 \
BENCH_OUT_JSON=docs/bench_2026_ollama.json \
python -m scripts.extract_personas_llm --year 2026 \
  --max-pages-per-chunk 8 --max-ctx-tokens 12000 --verbose
```

## Mejoras incluidas en este run vs corrida anterior con OpenRouter

1. **Verificacion literal anti-alucinacion.** Cada cedula extraida debe aparecer en el bloque enviado al modelo (digit match con strip de separadores). Si no aparece, se descarta.
2. **Campo `cita` verbatim.** El modelo devuelve la sub-cadena exacta donde extrae cada cedula; verificada contra el texto.
3. **Campo `confidence`** (alta/media/baja). Baja confianza marca la persona con `por_verificar: true`.
4. **OCR-tolerant normalizer.** Acepta `V-1.234.567`, `CI 12345678`, `V12345678`, `12.345.678`, espacios y comas.
5. **Tres tipos:** `natural` (cedula V/E), `juridica` (RIF J/G/P), `organismo` (ministerios y entes publicos, slug-id).
6. **Deteccion de conflictos:**
   - Misma cedula → dos nombres distintos: `conflictos[].tipo = mismo_cedula_otro_nombre`
   - Mismo nombre → dos cedulas distintas: `conflictos[].tipo = mismo_nombre_otra_cedula`
   - Baja confianza del modelo: `conflictos[].tipo = baja_confianza_modelo`
7. **Filtro de placeholder cedulas** (V-12345678, V-NNNNNNNN, V-00000000, etc).
8. **Nombre completion**: si el LLM trae cedula pero nombre vacio, se conserva el nombre existente en BD.

## Universo procesado

| Metrica | Valor |
|---|---|
| Gacetas en `year=2026` | 59 |
| Paginas totales | 556 |
| Tokens de entrada estimados | 585,318 |
| Chunks emitidos | 92 |

## Resultado wall-clock

| Metrica | Valor |
|---|---|
| **Tiempo total** | **11,650 s (3h 14min)** |
| Promedio s/chunk | 90.2 |
| Promedio s/pagina | 14.3 |
| Chunk mas lento | 297 s (8 pag, 7,702 tokens, 29 personas) |
| Chunk mas rapido (con output) | 9 s (3 pag, sin personas) |
| Errores HTTP/timeout | 4 |
| Throughput | ~4.2 paginas/min |

## Output del modelo y filtrado

| Metrica | Valor |
|---|---|
| Personas devueltas por el modelo | 691 |
| **Personas validadas (kept)** | **554** |
| Dropped — sin cedula valida | 71 |
| Dropped — cedula/cita no aparece en bloque (halucinacion) | 54 |
| Dropped — placeholder explicito (V-12345678 etc) | 5 |
| Dropped — sin RIF valido (tipo juridica) | 7 |
| Dropped — sin nombre de organismo | 0 |
| Marcadas baja confianza (`por_verificar`) | 11 |

Tasa de alucinacion bruta: **(54+5+71+7)/691 = 19.8%** descartado por validadores.

## Persistencia en BD

| Metrica | Valor |
|---|---|
| Personas creadas (nuevas) | 132 |
| Personas actualizadas (existentes, sin conflicto) | 333 |
| Personas actualizadas con conflicto detectado | 89 |
| Relaciones persona-gaceta insertadas | 554 |

## DB antes vs despues

| Coleccion | Antes | Despues | Delta |
|---|---:|---:|---:|
| `persona` | 17,081 | 17,214 | +133 |
| `persona` con `contexto` | 58 | 459 | +401 |
| `persona` con `por_verificar` | 0 | 83 | +83 |
| `persona_gaceta` | 31,505 | 31,836 | +331 |
| `gaceta` | 1,669 | 1,672 | +3 |

### Distribucion por tipo (solo entidades creadas/marcadas en este run)

| tipo | Conteo |
|---|---:|
| natural | 75 |
| organismo | 56 |
| juridica | 1 |
| **Total con `tipo`** | **132** |

(Las ~17k personas previas no tienen `tipo` porque fueron creadas por el extractor regex original.)

## Pre-existencia: cedulas que ya estaban y que el modelo volvio a encontrar

Personas mencionadas en gacetas del 2026 (segun la tabla `persona_gaceta`): **580 unicas**.

| Categoria | Conteo |
|---|---:|
| Personas mencionadas en 2026 — total unicas | 580 |
| Personas mencionadas en 2026 con `contexto` (poblado por gemma3) | 459 |
| Personas mencionadas en 2026 marcadas `por_verificar` | 83 |
| Personas nuevas en 2026 (creadas por gemma3) | 132 |
| Personas **pre-existentes** revalidadas por gemma3 | 448 |
| Pre-existentes en 2026 que gemma3 NO volvio a tocar (solo regex) | 121 |

Esto cumple el objetivo: **gemma3 confirmo 448 cedulas que ya existian + agrego 132 nuevas que el regex se habia perdido**.

## Conflictos detectados — resumen

Personas con `por_verificar: true`: **83**

| Tipo de conflicto | Entradas |
|---|---:|
| `mismo_cedula_otro_nombre` (OCR/lineas partidas mayormente) | 85 |
| `baja_confianza_modelo` | 11 |
| `mismo_nombre_otra_cedula` | 0 |

> Casi todos los conflictos de "mismo cedula otro nombre" son ruido OCR (saltos de linea, caracteres rotos como `MEL�NDEZ`, abreviaturas como `(E)`). Una limpieza posterior simple puede normalizar antes de comparar.

### Muestras de conflictos

| Cedula | Nombre actual | Nombre nuevo (gemma3) | Tipo |
|---|---|---|---|
| V-15147094 | Alexis Antonio Andrade | Alexis Anrorlo Andrade | mismo_cedula_otro_nombre (OCR) |
| V-20914807 | AUGUSTO\nALEJANDRO MEL�NDEZ | AUGUSTO ALEJANDRO MEL�NDEZ IULI | mismo_cedula_otro_nombre (linea partida) |
| V-23695886 | Abogado\nRONALD ALEXANDER RATIA APONTE | RONALD ALEXANDER RATIA APONTE | mismo_cedula_otro_nombre (titulo arrastrado) |
| V-13919493 | MORAIMA DEL VALLE MEDINA SILVA | — | baja_confianza_modelo (gaceta 43296, pag 2) |

Listado completo en `docs/conflictos_2026.json`.

## Muestras de extraccion exitosa

### Naturales

| Cedula | Nombre | Contexto |
|---|---|---|
| V-13138674 | EDISSON ISMAEL ALVAREZ OROPEZA | FISCAL AUXILIAR INTERINO a la FISCALIA OCTAVA |
| V-14515635 | ORCLY JOSE GARCIA LUGO | Representante de los trabajadores y las trabajadoras |
| V-12932760 | OMAR JESUS GARCIA PUCHE | Representante de los trabajadores y las trabajadoras |
| V-19593640 | JUAN CARLOS VILLEGAS BRITO | Designado Presidente Encargado de la Fundacion CENDITEL |

### Juridicas (RIF)

| RIF | Razon social | Contexto |
|---|---|---|
| G-20009781-7 | FUNDACION "FONDO ADMINISTRATIVO DE SALUD PARA EL..." | Fundacion del Estado |

### Organismos

| Identificador | Nombre | Contexto |
|---|---|---|
| ORG:MINISTERIO_DEL_PODER_POPULAR_PARA_LA_EDUCACION_UNIVERSITARIA | Ministerio del Poder Popular para la Educacion Universitaria | Refrendado |
| ORG:MINISTERIO_DEL_PODER_POPULAR_PARA_EL_PROCESO_SOCIAL_DE_TRABAJO | Ministerio del Poder Popular para el Proceso Social de Trabajo | organo rector en materia de trabajo y seguridad social |
| ORG:MINISTERIO_DEL_PODER_POPULAR_PARA_EL_TRANSPORTE | Ministerio del Poder Popular para el Transporte | como Ministro del Poder Popular para el Transporte |

## Comparacion contra OpenRouter (run anterior)

| Metrica | OpenRouter (deepseek-v4-flash:free) | Ollama local (gemma3:12b) |
|---|---:|---:|
| Tiempo total | 574 s (9.5 min) | 11,650 s (3h 14min) |
| Costo | $0 (free, con rate-limit) | $0 (electricidad ~0.3 kWh) |
| Chunks fallidos | 4 (429 upstream) | 4 (HTTP/parse) |
| Personas devueltas | 101 | 691 |
| Personas validadas | 101 (sin filtro) | 554 |
| Personas con contexto poblado | 57 | 401 |
| Conflictos detectados | 0 (no impl.) | 96 |
| Tipos extraidos | solo natural | natural + juridica + organismo |

Throughput: OpenRouter ~60 paginas/min (cuando no rate-limit); gemma3 local ~4.2 paginas/min. **Ollama es ~14x mas lento** pero produce 5x mas hits validados y captura organismos + juridicas.

## Limitaciones observadas

1. **Lentitud de chunk con muchas personas.** Chunks con 25+ designaciones tardan ~5 min (el modelo genera ~5000 tokens). Para volumen alto vale alargar `max-pages-per-chunk` o usar quantizacion menor.
2. **OCR roto contamina nombres.** Caracteres `�`, saltos en medio de nombres y abreviaturas como `(E)` quedan en el nombre final. Se necesita post-proceso de limpieza OCR antes de comparar conflictos.
3. **Hallucinacion residual.** 19.8% de las salidas del modelo fueron descartadas por el filtro literal. La mayoria por nombres genericos ("EL MINISTRO") sin cedula.
4. **Organismos por nombre, no por RIF.** El modelo a veces propone organismos pero el RIF no aparece en el texto. Por eso `juridica` solo tuvo 1 entrada — los entes publicos pasan como `organismo`.

## Archivos

- `docs/benchmark_2026_ollama.md` (este archivo)
- `docs/benchmark_2026_ollama.html` (version printable A4)
- `docs/bench_2026_ollama.json` (output JSON del run)
- `docs/bench_2026_ollama.log` (stdout completo)
- `docs/conflictos_2026.json` (lista completa de personas con `por_verificar:true` y sus apariciones)
- `progress_llm.json` (state file)
