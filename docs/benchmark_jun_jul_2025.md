# Benchmark Jun-Jul 2025 - Ollama gemma3:12b

**Fecha:** 2026-05-20  
**Modelo:** `gemma3:12b-it-q4_K_M` via Ollama local  
**Hardware:** RTX 3060 12GB + i7-12700KF + 32GB RAM  
**Periodo:** Gacetas de Junio y Julio 2025 (filename `*-2025-06-*` o `*-2025-07-*`)

## Universo

| Metrica | Valor |
|---|---|
| Gacetas Jun-Jul 2025 | 50 |
| Paginas totales | 712 |
| Chunks emitidos | 128 |
| Tokens de entrada estimados | 859,058 |
| **Tiempo total** | **175 min (2.9 h)** |
| Personas devueltas por el modelo | 1236 |
| Personas validadas (kept) | 1009 |
| Personas nuevas creadas | 155 |
| Personas pre-existentes actualizadas | 510 |
| Personas con conflicto detectado | 342 |
| Marcadas baja confianza | 27 |

## Filtrado anti-alucinacion

| Categoria | Conteo |
|---|---:|
| Dropped sin cedula | 95 |
| Dropped no aparece en bloque | 103 |
| Dropped placeholder | 14 |
| Dropped sin RIF | 15 |
| **Total descartado** | **227** |
| % descartado del total | 18.4% |

## Pre-existentes vs nuevas

- **Personas unicas mencionadas en Jun-Jul 2025:** 1,001
- **Pre-existentes en BD revalidadas por gemma3:** 819
- **Nuevas aportadas por gemma3 (creadas con campo `tipo`):** 182
- De las 182 nuevas: 80 naturales, 98 organismos, 4 juridicas (RIF)
- 293 marcadas `por_verificar` (conflictos / baja confianza)

## Personas por gaceta

Top 25 gacetas por cantidad de personas distintas mencionadas:

| Gaceta | Fecha | Personas | Paginas con personas |
|---|---|---:|---:|
| 43157 | 26/06/2025 | 84 | 18 |
| 43145 | 09/06/2025 | 52 | 7 |
| 43143 | 05/06/2025 | 47 | 11 |
| 43177 | 25/07/2025 | 45 | 13 |
| 43172 | 17/07/2025 | 40 | 11 |
| 43164 | 07/07/2025 | 39 | 15 |
| 43142 | 04/06/2025 | 38 | 10 |
| 43156 | 25/06/2025 | 38 | 17 |
| 43169 | 14/07/2025 | 38 | 21 |
| 43148 | 12/06/2025 | 38 | 7 |
| 43161 | 02/07/2025 | 38 | 10 |
| 43175 | 22/07/2025 | 37 | 14 |
| 43163 | 04/07/2025 | 37 | 13 |
| 43144 | 06/06/2025 | 36 | 7 |
| 43173 | 18/07/2025 | 33 | 11 |
| 43151 | 17/06/2025 | 32 | 11 |
| 43179 | 29/07/2025 | 32 | 13 |
| 43155 | 23/06/2025 | 31 | 19 |
| 43140 | 02/06/2025 | 30 | 4 |
| 43153 | 19/06/2025 | 30 | 8 |
| 43162 | 03/07/2025 | 30 | 7 |
| 43176 | 23/07/2025 | 30 | 9 |
| 43166 | 09/07/2025 | 28 | 6 |
| 43165 | 08/07/2025 | 27 | 9 |
| 43146 | 10/06/2025 | 26 | 11 |

_Total gacetas con menciones: 48 / 50_

## Personas por pagina (top 40 paginas con mas menciones)

| Gaceta | Pagina | Personas en pagina |
|---|---:|---:|
| 43157 | 12 | 18 |
| 43169 | 2 | 18 |
| 43173 | 3 | 18 |
| 43144 | 3 | 17 |
| 43153 | 1 | 15 |
| 43172 | 7 | 15 |
| 43157 | 7 | 14 |
| 43157 | 11 | 14 |
| 43143 | 6 | 13 |
| 43145 | 7 | 13 |
| 43148 | 3 | 13 |
| 43162 | 4 | 13 |
| 43163 | 3 | 13 |
| 43173 | 2 | 13 |
| 43140 | 2 | 12 |
| 43142 | 3 | 12 |
| 43145 | 3 | 12 |
| 43148 | 2 | 12 |
| 43161 | 13 | 12 |
| 43140 | 4 | 11 |
| 43142 | 2 | 11 |
| 43146 | 6 | 11 |
| 43161 | 6 | 11 |
| 43164 | 2 | 11 |
| 43165 | 10 | 11 |
| 43176 | 2 | 11 |
| 43151 | 10 | 10 |
| 43156 | 6 | 10 |
| 43157 | 10 | 10 |
| 43167 | 3 | 10 |
| 43175 | 2 | 10 |
| 43143 | 7 | 9 |
| 43144 | 2 | 9 |
| 43145 | 4 | 9 |
| 43145 | 5 | 9 |
| 43152 | 2 | 9 |
| 43156 | 8 | 9 |
| 43157 | 14 | 9 |
| 43159 | 9 | 9 |
| 43162 | 1 | 9 |

## Personas detalle (etiquetadas)

Etiquetas:
- :NEW: persona aportada por gemma3 (no existia antes)
- :OK: persona pre-existente en BD revalidada por gemma3
- :CONFLICT: marcada `por_verificar`

Muestras (primeras 80 menciones ordenadas por gaceta y pagina):

| Gaceta | Pag | Cedula | Nombre | Tipo | Etiqueta | Contexto |
|---|---:|---|---|---|---|---|
| 43140 | 1 | ORG:MINISTERIO_DEL_PODER_POPULAR_PARA_LA_DEFENSA | MINISTERIO DEL PODER POPULAR PARA LA DEFENSA | organismo | :NEW: | Resolución conjunta |
| 43140 | 1 | ORG:MINISTERIO_DEL_PODER_POPULAR_DE_ECONOMIA_Y_FINANZAS | Ministerio del Poder Popular de Economía y Finanza | organismo | :NEW: | autorización a la sociedad mercantil AGENTE DE ADUANA W 8 |
| 43140 | 2 | V-14122851 | ANABEL PEREIRA
FERNÁNDEZ | natural | :OK: | Miembro Principal del Directorio Ejecutivo del Banco de Desarrollo Eco |
| 43140 | 2 | V-13287869 | Tejera Morillo | natural | :OK: |  |
| 43140 | 2 | V-6730839 | Janeth Solange José Luis
Castillo Martínez | natural | :OK: |  |
| 43140 | 2 | V-10820066 | Jesús Eduardo Nicolas | natural | :CONFLICT: | Miembro Principal del Área Jurídica |
| 43140 | 2 | V-14958255 | JOSÉ MIGUEL RONDÓN COLINA | natural | :NEW: | Miembro Suplente del Área Jurídica |
| 43140 | 2 | V-15512822 | DAVID ALEXIS MORENO GARCÍA | natural | :NEW: | Miembro Principal del Área Técnica |
| 43140 | 2 | V-15007464 | FRANCISCO ANTONIO SILVA VIDAL | natural | :NEW: | Miembro Suplente del Área Técnica |
| 43140 | 2 | V-17198694 | GRECIA LISSET PALMA DE MILIAN | natural | :NEW: | Miembro Principal del Área Económica — Financiera |
| 43140 | 2 | V-12814442 | LUIS ÁLVARO PEÑUELA CADENA | natural | :NEW: | Miembro Suplente del Área Económica — Financiera |
| 43140 | 2 | V-17016097 | ALEXANDRA KARINA MATA DE RODRÍGUEZ | natural | :NEW: | Miembro Principal de la Secretaría |
| 43140 | 2 | V-20818531 | MELANY DE LOS ÁNGELES DÍAZ LUNA | natural | :NEW: | Miembro Suplente de la Secretaría |
| 43140 | 2 | ORG:SERVICIO_AUTONOMO_DE_LA_FUERZA_AEREA_VENEZOLANA_SAFAV | SERVICIO AUTÓNOMO DE LA FUERZA AÉREA VENEZOLANA (S | organismo | :NEW: | Constituir la COMISIÓN DE CONTRATACIONES PÚBLICAS |
| 43140 | 3 | V-10300226 | JOSÉ DAVID CABELLO RONDÓN | natural | :OK: | Superintendente del Servicio Nacional Integrado de Administración Adua |
| 43140 | 3 | V-12616314 | DAVID GASPARRI REY | natural | :OK: |  |
| 43140 | 3 | V-6730515 | DAVID GASPARRI REY | natural | :OK: |  |
| 43140 | 3 | V-14122851 | ANABEL PEREIRA
FERNÁNDEZ | natural | :OK: | Miembro Principal del Directorio Ejecutivo del Banco de Desarrollo Eco |
| 43140 | 3 | ORG:SERVICIO_NACIONAL_INTEGRADO_DE_ADMINISTRACION_ADUANERA_Y_TRIBUTARIA | SERVICIO NACIONAL INTEGRADO DE ADMINISTRACIÓN ADUA | organismo | :NEW: | Providencia mediante la cual se reajusta el valor de la |
| 43140 | 3 | ORG:BANCO_DE_DESARROLLO_ECONOMICO_Y_SOCIAL_DE_VENEZUELA_BANDES | BANCO DE DESARROLLO ECONÓMICO Y SOCIAL DE VENEZUEL | organismo | :NEW: | Nombrar como Miembros Principales y Suplentes del Directorio Ejecutivo |
| 43140 | 4 | V-13499947 | JESÚS ADELMO PEÑA DUGARTE | natural | :OK: |  |
| 43140 | 4 | V-11945178 | Jorge Arreaza | natural | :CONFLICT: | secretario ejecutivo de la Alianza Bolivariana |
| 43140 | 4 | V-13029634 | RECTOR
SECRETARIA

MAGALY VIDIA NEWTON CARRERA | natural | :OK: |  |
| 43140 | 4 | V-15306370 | PARA LA
KELLY SABRINA PACHECO SUÁREZ | natural | :CONFLICT: | Miembros Principales |
| 43140 | 4 | V-14728837 | HERNÁN JOSÉ VARGAS PÉREZ | natural | :OK: |  |
| 43140 | 4 | ORG:MINISTERIO_DEL_PODER_POPULAR_PARA_LA_EDUCACION_UNIVERSITARIA | Ministerio del Poder Popular para la Educación Uni | organismo | :NEW: | RESOLUCIÓN N* 076 |
| 43140 | 4 | ORG:UNIVERSIDAD_NACIONAL_EXPERIMENTAL_SIMON_RODRIGUEZ | UNIVERSIDAD NACIONAL EXPERIMENTAL SIMÓN RODRÍGUEZ | organismo | :NEW: | Representantes principal y suplente del Ministerio del Poder Popular p |
| 43140 | 4 | ORG:UNIVERSIDAD_NACIONAL_EXPERIMENTAL_DE_LAS_ARTES_UNEARTE | UNIVERSIDAD NACIONAL EXPERIMENTAL DE LAS ARTES (UN | organismo | :NEW: | Secretario General |
| 43140 | 4 | ORG:UNIVERSIDAD_NACIONAL_DE_LAS_COMUNAS_UNACOM | UNIVERSIDAD NACIONAL DE LAS COMUNAS (UNACOM) | organismo | :NEW: | Miembros del Consejo Universitario |
| 43140 | 4 | ORG:TRIBUNAL_SUPREMO_DE_JUSTICIA | TRIBUNAL SUPREMO DE JUSTICIA | organismo | :NEW: | designada |
| 43140 | 4 | ORG:DIRECCION_EJECUTIVA_DE_LA_MAGISTRATURA | DIRECCIÓN EJECUTIVA DE LA MAGISTRATURA | organismo | :NEW: | Resolución mediante la cual se designa al ciudadano José Gregorio |
| 43141 | 1 | V-36893134 | CAMILLA FABRI | natural | :OK: | Viceministra de Comunicación Internacional |
| 43141 | 2 | V-6823952 | JORGE RODRÍGUEZ GÓMEZ | natural | :CONFLICT: | presidente de la Asamblea Nacional |
| 43141 | 2 | V-15541220 | PEDRO INFANTE APARICIO | natural | :CONFLICT: | primer vicepresidente de la Asamblea Nacional |
| 43141 | 2 | V-11448109 | RAMÓN CELESTINO
VELASQUEZ ARAGUAYAÁN | natural | :CONFLICT: | Ministro |
| 43141 | 2 | V-11945178 | Jorge Arreaza | natural | :CONFLICT: | secretario ejecutivo de la Alianza Bolivariana |
| 43141 | 2 | V-36893134 | CAMILLA FABRI | natural | :OK: | Viceministra de Comunicación Internacional |
| 43141 | 3 | V-19830462 | JENDUAR NAZARETH SERRANO
MONTILLA | natural | :OK: | Director Estadal de la Unidad Territorial Agrícola |
| 43141 | 3 | V-15653668 | DALIEMY CAROLINA LOYO

HERNÁNDEZ | natural | :OK: | Directora General de Mercadeo Pesquero |
| 43141 | 3 | V-13984678 | SACHENKA MILDRED CASTILLO
OCHOA | natural | :OK: | Directora General de Desarrollo Industrial Pesquero |
| 43141 | 4 | V-13984678 | SACHENKA MILDRED CASTILLO
OCHOA | natural | :OK: | Directora General de Desarrollo Industrial Pesquero |
| 43141 | 4 | V-18557457 | SANTAMARÍA DE LARA | natural | :CONFLICT: | DIRECTORA GENERAL |
| 43141 | 5 | V-18557457 | SANTAMARÍA DE LARA | natural | :CONFLICT: | DIRECTORA GENERAL |
| 43141 | 5 | V-28598769 | Abogado SAMIR JOSÉ SAYEGH BEJARANO | natural | :CONFLICT: | en la FISCALÍA PRIMERA del Ministerio Público |
| 43141 | 5 | V-10572697 | Abogada MARIBEL DE LAS NIEVES MAESTRE | natural | :CONFLICT: | en la FISCALÍA SÉPTIMA del Ministerio Público |
| 43141 | 6 | V-17403711 | Abogada MARÍA JOSÉ CAÑAS
SALAS | natural | :CONFLICT: | en la FISCALÍA CUADRAGÉSIMA CUARTA del Ministerio Público |
| 43141 | 6 | V-21573079 | Abogado FREDDY JOSÉ
APONTE MEJÍAS | natural | :CONFLICT: | a la FISCALÍA 54 NACIONAL CONTRA LA LEGITIMACIÓN DE CAPITALES |
| 43141 | 6 | V-16765772 | Abogada SORANGEL ARENALES MÁRQUEZ | natural | :CONFLICT: | a la FISCALÍA CENTÉSIMA CUADRAGÉSIMA SÉPTIMA del Ministerio Público |
| 43141 | 6 | V-28598769 | Abogado SAMIR JOSÉ SAYEGH BEJARANO | natural | :CONFLICT: | en la FISCALÍA PRIMERA del Ministerio Público |
| 43141 | 6 | V-10572697 | Abogada MARIBEL DE LAS NIEVES MAESTRE | natural | :CONFLICT: | en la FISCALÍA SÉPTIMA del Ministerio Público |
| 43141 | 7 | V-25417573 | Abogado FISHER JOHANDER MOTA UTRERA | natural | :OK: |  |
| 43141 | 7 | V-17403711 | Abogada MARÍA JOSÉ CAÑAS
SALAS | natural | :CONFLICT: | en la FISCALÍA CUADRAGÉSIMA CUARTA del Ministerio Público |
| 43141 | 8 | V-13306435 | Abogada DORICELY DE LA
TRINIDAD DELGADO | natural | :CONFLICT: | a la FISCALÍA TERCERA del Ministerio Público |
| 43141 | 8 | V-21573079 | Abogado FREDDY JOSÉ
APONTE MEJÍAS | natural | :CONFLICT: | a la FISCALÍA 54 NACIONAL CONTRA LA LEGITIMACIÓN DE CAPITALES |
| 43141 | 9 | V-16421838 | VICTOR OMAR GARCÍA ROJAS | natural | :OK: | a la FISCALÍA TRIGÉSIMA PRIMERA del Ministerio Público |
| 43141 | 9 | V-16765772 | Abogada SORANGEL ARENALES MÁRQUEZ | natural | :CONFLICT: | a la FISCALÍA CENTÉSIMA CUADRAGÉSIMA SÉPTIMA del Ministerio Público |
| 43141 | 10 | V-14724596 | Abogada YDANNIA YILET
PEÑA MOLINA | natural | :CONFLICT: | a la FISCALÍA DÉCIMA CUARTA del Ministerio Público |
| 43141 | 11 | V-8799421 | ANGELINA
RODRÍGUEZ RUÍZ | natural | :CONFLICT: | a la FISCALÍA VIGÉSIMA SÉPTIMA del Ministerio del Público |
| 43141 | 11 | V-16421838 | VICTOR OMAR GARCÍA ROJAS | natural | :OK: | a la FISCALÍA TRIGÉSIMA PRIMERA del Ministerio Público |
| 43141 | 12 | V-13306435 | Abogada DORICELY DE LA
TRINIDAD DELGADO | natural | :CONFLICT: | a la FISCALÍA TERCERA del Ministerio Público |
| 43142 | 2 | V-16672333 | Ramírez Fernández | natural | :OK: |  |
| 43142 | 2 | V-14164814 | JIMMY BERRÍOS OJEDA | natural | :CONFLICT: | Presidente de la Junta Liquidadora |
| 43142 | 2 | V-19318 | ESTEFANIA MARGARITA GARCÍA SÁNCHEZ | natural | :OK: |  |
| 43142 | 2 | V-11832584 | ANÍBAL EDUARDO CORONADO MILLÁN | natural | :OK: | DIRECTOR GENERAL |
| 43142 | 2 | V-19000184 | SAÚL FRANCISCO
AMELIACH RANGEL | natural | :OK: |  |
| 43142 | 2 | V-1089584 | Desconocido | natural | :NEW: |  |
| 43142 | 2 | V-11346596 | DE LA
MARQUEZ MONSALVE  
CESAR AUGUSTO | natural | :OK: |  |
| 43142 | 2 | V-11496429 | MIGUEL ÁNGEL RAMONES GALVIZ | natural | :OK: |  |
| 43142 | 2 | ORG:MINISTERIO_DEL_PODER_POPULAR_PARA_EL_ECOSOCIALISMO | Ministerio del Poder Popular para el Ecosocialismo | organismo | :NEW: | Resolución N* 066 |
| 43142 | 2 | ORG:BANCO_DEL_TESORO_C_A | Banco del Tesoro, C.A. | organismo | :NEW: |  |
| 43142 | 2 | ORG:SERVICIO_AUTONOMO_IMPRENTA_NACIONAL_Y_GACETA_OFICIAL | Servicio Autónomo Imprenta Nacional y Gaceta Ofici | organismo | :NEW: | dar carácter oficial a las publicaciones |
| 43142 | 3 | V-8714253 | JORGE ELIESER
MARQUEZ MONSALVE | natural | :OK: | Presidente de la Fundación Radio Miraflores |
| 43142 | 3 | V-11346596 | DE LA
MARQUEZ MONSALVE  
CESAR AUGUSTO | natural | :OK: |  |
| 43142 | 3 | V-11496429 | MIGUEL ÁNGEL RAMONES GALVIZ | natural | :OK: |  |
| 43142 | 3 | V-11465880 | MIEMBRO PRINCIPAL
RIVERA
LUIS JOSÉ SARMIENTO | natural | :OK: |  |
| 43142 | 3 | V-12163594 | GALVIZ
JIMMY JOE MEAYKE | natural | :OK: |  |
| 43142 | 3 | V-16702636 | LUIS ALBERTO VERDE CORONADO | natural | :OK: |  |
| 43142 | 3 | V-19315012 | NÍA MARGARITA GARCÍA SÁNCHEZ | natural | :OK: |  |
| 43142 | 3 | V-14680973 | JOSE GOMEZ ULLOA | natural | :OK: |  |
| 43142 | 3 | V-3883309 | JOSE GOMEZ ULLOA | natural | :OK: |  |

_Listado completo en `docs/personas_por_pagina_jun_jul_2025.json` (total: 1628 apariciones)_
