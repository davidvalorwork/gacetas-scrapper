"""Build docs/benchmark_2026_ollama.html from bench JSON + Mongo queries."""
import json
import os
import html

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(REPO, "docs")

with open(os.path.join(DOCS, "bench_2026_ollama.json"), encoding="utf-8") as f:
    bench = json.load(f)
with open(os.path.join(DOCS, "conflictos_2026.json"), encoding="utf-8") as f:
    conflictos = json.load(f)

stats = bench["stats"]

pre_existing = [
    ("V-19593640", "JUAN CARLOS VILLEGAS BRITO", "Ministro del Poder Popular para el Proceso Social de Trabajo"),
    ("V-6823952", "JORGE RODRIGUEZ GOMEZ", "Director del CICPC"),
    ("V-15541220", "PEDRO INFANTE APARICIO", "Primer Vicepresidente de la Asamblea Nacional"),
    ("V-24744711", "GRECIA COLMENARES SANTANDER", "Segunda Vicepresidenta de la Asamblea Nacional"),
    ("V-17038012", "MARIA ALEJANDRA HERNANDEZ", "Secretaria de la Asamblea Nacional"),
    ("V-16092902", "JOSE OMAR MOLINA", "Subsecretario de la Asamblea Nacional"),
    ("V-11395720", "CARMEN GREGORIA PEREZ FERNANDEZ", "FISCAL AUXILIAR INTERINO FISCALIA DECIMA TERCERA"),
    ("V-24656296", "CAROLING ALEXANDRA AZOCAR ALEJOS", "Trasladada Fiscal Auxiliar Interino Fiscalia 26"),
    ("V-14908093", "JESUS DANIEL VERDU QUINTANA", "Designado Fiscal Auxiliar Interino en Miranda"),
    ("V-26684810", "MARIELY AGUILERA SALAZAR", "Designada Fiscal Auxiliar Interino Fiscalia 44"),
    ("V-19063367", "ESTEPHANY GABRIELA MORALES DE CASTILLO", "Designada Fiscal Provisorio en Yaracuy"),
    ("V-18789559", "VERONICA JOSE RAMONA RAMOS SALAZAR", "Designada Fiscal Provisorio en Sucre"),
    ("V-19849102", "JOHANNA CAROLINA COLMENARES MENDOZA", "FISCAL AUXILIAR INTERINO FISCALIA VIGESIMA SEXTA"),
    ("V-18103227", "MARIANA CAROLINA MUJICA PARRA", "FISCAL AUXILIAR INTERINO FISCALIA VIGESIMA SEXTA"),
    ("V-16421838", "VICTOR OMAR GARCIA ROJAS", "FISCAL AUXILIAR SUPERIOR DE INVESTIGACION"),
    ("V-16791794", "CARLOS JAVIER BLANCO VIVAS", "Presidente de la Fundacion Mision Habitat"),
    ("V-12517252", "ELKER DARIO BONILLA CAMACHO", "Gerente (E) Oficina de Gestion Administrativa"),
    ("V-21345794", "JHON ANDERSON HERNANDEZ COLMENAREZ", "traslado como Fiscal Auxiliar Interino"),
    ("V-26458612", "GENESIS SARAHI PERALTA SANCHEZ", "traslado como Fiscal Auxiliar Interino"),
    ("V-11397300", "LORENA RAMONA VALDERRAMA BASTIDAS", "traslado como Fiscal Provisorio"),
]

new_personas = [
    ("V-1313864", "EDISSON ISMAEL ALVAREZ OROPEZA", "FISCAL AUXILIAR INTERINO a la FISCALIA OCTAVA"),
    ("V-14515635", "ORCLY JOSE GARCIA LUGO", "Representante de los trabajadores y las trabajadoras"),
    ("V-12932760", "OMAR JESUS GARCIA PUCHE", "Representante de los trabajadores y las trabajadoras"),
    ("V-13903869", "Gleidys Taimar Carreno Gomez Cortez", "Economico Financiera"),
    ("V-00363054", "POMPEYO SUAREZ QUIROZ", "Auxiliar de la Administracion Aduanera"),
    ("V-02071267", "Luis Eduardo Tolosa Duarte", "Gerente Aduana Principal Las Piedras Paraguana"),
    ("V-13322083", "MAYIRA YURIMAR MONTOYA", "reconocimiento a sus destacados aportes"),
    ("V-20997143", "MIRANDA MISYERLIN NAZARETH SOJO HERNANDEZ", "reconocimiento a sus destacados aportes"),
    ("V-11506348", "ANGELA MARIA PEREIRA DE MEJIA", "reconocimiento a sus destacados aportes"),
    ("V-8948354", "MARIA JOSEFINA DA CORTE LUNA", "GESTION CURRICULAR"),
    ("V-9873047", "ARMANDO JOSE HERNANDEZ NUNEZ", "GESTION CURRICULAR"),
    ("V-6308446", "DILCIA JANETTE RICO ALVARADO", "GESTION CURRICULAR"),
]

organismos = [
    ("ORG:MIN_EDUCACION_UNIVERSITARIA", "Ministerio del Poder Popular para la Educacion Universitaria", "Refrendado"),
    ("ORG:MIN_PROCESO_SOCIAL_DE_TRABAJO", "Ministerio del Poder Popular para el Proceso Social de Trabajo", "organo rector en materia de trabajo y seguridad social"),
    ("ORG:MIN_CIENCIA_Y_TECNOLOGIA", "Ministerio del Poder Popular para la Ciencia y Tecnologia", "RESOLUCION"),
    ("ORG:MIN_TRANSPORTE", "Ministerio del Poder Popular para el Transporte", "como Ministro del Poder Popular para el Transporte"),
    ("ORG:MIN_COMUNICACION_INFORMACION", "Ministerio del Poder Popular para la Comunicacion e Informacion", "RESOLUCION"),
]

conflict_rows = []
for p in conflictos[:60]:
    aps = p.get("apariciones") or []
    apariciones_text = "; ".join([f"G{a.get('numero_gaceta','?')} p{a.get('pagina','?')}" for a in aps if a.get('numero_gaceta')]) or "-"
    for cf in (p.get("conflictos") or []):
        tipo_cf = cf.get("tipo", "?")
        if tipo_cf == "mismo_cedula_otro_nombre":
            descr = f"<b>{html.escape((cf.get('nombre_actual') or '')[:60])}</b> &harr; {html.escape((cf.get('nombre_nuevo') or '')[:60])}"
        elif tipo_cf == "mismo_nombre_otra_cedula":
            descr = f"otra cedula con mismo nombre: {html.escape(cf.get('otra_cedula',''))}"
        elif tipo_cf == "baja_confianza_modelo":
            descr = f"gaceta {cf.get('numero_gaceta','?')} pag {cf.get('pagina','?')}"
        else:
            descr = html.escape(json.dumps(cf, ensure_ascii=False))[:120]
        conflict_rows.append((
            p.get("cedula", ""),
            (p.get("nombre", "") or "")[:50],
            tipo_cf,
            descr,
            apariciones_text,
        ))

def tr(*cells):
    return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"

pre_table = "\n".join(tr(html.escape(c), html.escape(n), html.escape(ctx)) for c, n, ctx in pre_existing)
new_table = "\n".join(tr(html.escape(c), html.escape(n), html.escape(ctx)) for c, n, ctx in new_personas)
org_table = "\n".join(tr(html.escape(c), html.escape(n), html.escape(ctx)) for c, n, ctx in organismos)
conf_table = "\n".join(tr(html.escape(c), html.escape(n), html.escape(t), d, html.escape(ap)) for c, n, t, d, ap in conflict_rows[:50])

style = """
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 1100px; margin: 20px auto; padding: 20px; color: #222; background: #fff; }
  h1 { border-bottom: 3px solid #003366; padding-bottom: 6px; color: #003366; }
  h2 { color: #003366; border-bottom: 1px solid #ccc; padding-bottom: 4px; margin-top: 30px; }
  .meta { background: #f8f9fa; border-left: 4px solid #003366; padding: 10px 16px; margin: 16px 0; }
  .cards { display: flex; flex-wrap: wrap; gap: 12px; margin: 18px 0; }
  .card { flex: 1 1 200px; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; }
  .card .num { font-size: 1.8em; font-weight: 700; color: #003366; }
  .card .lbl { font-size: 0.85em; color: #555; }
  table { border-collapse: collapse; width: 100%; font-size: 0.85em; margin: 10px 0; }
  th, td { border: 1px solid #ccc; padding: 5px 8px; text-align: left; vertical-align: top; }
  th { background: #e2e8f0; color: #003366; }
  tr:nth-child(even) { background: #f8fafc; }
  .tag { display: inline-block; padding: 1px 7px; border-radius: 3px; font-size: 0.78em; font-weight: 600; }
  .tag-ok { background: #d1fae5; color: #065f46; }
  .tag-warn { background: #fef3c7; color: #92400e; }
  .tag-bad { background: #fee2e2; color: #991b1b; }
  .small { font-size: 0.8em; color: #666; }
  code { background: #f1f5f9; padding: 1px 5px; border-radius: 3px; font-size: 0.85em; }
  @media print {
    body { max-width: 100%; margin: 0; padding: 10mm; font-size: 10pt; }
    h2 { page-break-after: avoid; }
    table { page-break-inside: auto; font-size: 9pt; }
    tr { page-break-inside: avoid; }
    .cards { display: block; }
    .card { display: inline-block; width: 23%; margin: 2px; padding: 8px; }
    .no-print { display: none; }
  }
  @page { size: A4; margin: 12mm; }
"""

needs_review = stats.get("needs_review", 0)
conflict_updated = stats.get("personas_conflict_updated", 0)
flagged = conflict_updated + needs_review

html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Benchmark Ollama gemma3:12b - Gacetas 2026</title>
<style>{style}</style>
</head>
<body>

<h1>Benchmark Ollama <code>gemma3:12b-it-q4_K_M</code> &mdash; Gacetas 2026</h1>

<div class="meta">
  <b>Fecha:</b> 2026-05-20 &nbsp;|&nbsp;
  <b>Hardware:</b> RTX 3060 12GB + i7-12700KF &nbsp;|&nbsp;
  <b>Backend:</b> Ollama local &nbsp;|&nbsp;
  <b>Gacetas:</b> 59 (year=2026) &nbsp;|&nbsp;
  <b>Paginas:</b> 556
</div>

<h2>Resumen ejecutivo</h2>
<div class="cards">
  <div class="card"><div class="num">{stats['wall_seconds']/60:.0f} min</div><div class="lbl">Tiempo total (3h 14m)</div></div>
  <div class="card"><div class="num">{stats['personas_returned']}</div><div class="lbl">Personas devueltas por el modelo</div></div>
  <div class="card"><div class="num">{stats['personas_kept']}</div><div class="lbl">Personas validadas (kept)</div></div>
  <div class="card"><div class="num">{stats['personas_created']}</div><div class="lbl">Personas nuevas creadas</div></div>
  <div class="card"><div class="num">{stats['personas_updated']}</div><div class="lbl">Pre-existentes actualizadas</div></div>
  <div class="card"><div class="num">{flagged}</div><div class="lbl">Conflictos / baja confianza</div></div>
</div>

<h2>Filtrado anti-alucinacion</h2>
<table>
<tr><th>Categoria</th><th>Conteo</th></tr>
<tr><td>Personas devueltas por el modelo</td><td>{stats['personas_returned']}</td></tr>
<tr><td>Validadas (pasaron filtros)</td><td><span class="tag tag-ok">{stats['personas_kept']}</span></td></tr>
<tr><td>Dropped &mdash; sin cedula valida</td><td><span class="tag tag-warn">{stats.get('dropped_no_cedula',0)}</span></td></tr>
<tr><td>Dropped &mdash; cedula/cita no aparece en bloque</td><td><span class="tag tag-bad">{stats.get('dropped_not_in_text',0)}</span></td></tr>
<tr><td>Dropped &mdash; placeholder (V-12345678 etc)</td><td><span class="tag tag-bad">{stats.get('dropped_placeholder',0)}</span></td></tr>
<tr><td>Dropped &mdash; sin RIF valido (juridica)</td><td><span class="tag tag-warn">{stats.get('dropped_no_rif',0)}</span></td></tr>
<tr><td>Marcadas baja confianza (<code>por_verificar</code>)</td><td><span class="tag tag-warn">{needs_review}</span></td></tr>
</table>

<h2>Cedulas pre-existentes que el modelo revalido</h2>
<p class="small">580 personas mencionadas en gacetas 2026. <b>448 ya existian en BD</b> antes del run y gemma3 las confirmo de nuevo + les puso contexto. <b>132 son completamente nuevas</b> aportadas por gemma3.</p>
<table>
<tr><th>Cedula</th><th>Nombre (existente)</th><th>Contexto puesto por gemma3</th></tr>
{pre_table}
</table>
<p class="small">(20 muestras; total pre-existentes revalidadas: 448)</p>

<h2>Cedulas NUEVAS aportadas por gemma3</h2>
<p class="small">El extractor regex previo no las habia detectado. gemma3 las encontro en las gacetas del 2026.</p>
<table>
<tr><th>Cedula</th><th>Nombre</th><th>Contexto</th></tr>
{new_table}
</table>
<p class="small">(12 muestras; total nuevas: 132)</p>

<h2>Organismos / Gobierno detectados</h2>
<table>
<tr><th>Identificador</th><th>Nombre</th><th>Contexto</th></tr>
{org_table}
</table>
<p class="small">Total organismos creados: 56 &nbsp;|&nbsp; Personas juridicas (RIF): 1</p>

<h2>Conflictos detectados</h2>
<p class="small">83 personas marcadas con <code>por_verificar: true</code>. 85 conflictos de tipo "mismo_cedula_otro_nombre" (la mayoria son ruido OCR &mdash; saltos de linea, caracteres rotos, titulos pegados al nombre). 11 marcadas por baja confianza del modelo. 0 conflictos de tipo "mismo_nombre_otra_cedula" en este run.</p>
<table>
<tr><th>Cedula</th><th>Nombre actual</th><th>Tipo</th><th>Detalle</th><th>Apariciones</th></tr>
{conf_table}
</table>
<p class="small">(50 muestras; ver <code>docs/conflictos_2026.json</code> para listado completo)</p>

<h2>Comparativa contra OpenRouter</h2>
<table>
<tr><th>Metrica</th><th>OpenRouter (deepseek-v4-flash:free)</th><th>Ollama local (gemma3:12b)</th></tr>
<tr><td>Tiempo total</td><td>9.5 min</td><td>3h 14min</td></tr>
<tr><td>Costo</td><td>$0 (rate-limit upstream)</td><td>$0 (electricidad)</td></tr>
<tr><td>Personas devueltas</td><td>101</td><td>691</td></tr>
<tr><td>Personas validadas</td><td>101 (sin filtro)</td><td>554</td></tr>
<tr><td>Contextos poblados</td><td>57</td><td>401</td></tr>
<tr><td>Conflictos detectados</td><td>0 (no impl)</td><td>96</td></tr>
<tr><td>Tipos extraidos</td><td>solo natural</td><td>natural + juridica + organismo</td></tr>
<tr><td>Throughput</td><td>~60 pag/min</td><td>~4.2 pag/min</td></tr>
</table>

<p class="small no-print">Generado por <code>scripts/build_benchmark_html.py</code> a partir de <code>docs/bench_2026_ollama.json</code> + queries a Mongo.</p>

</body></html>
"""

out = os.path.join(DOCS, "benchmark_2026_ollama.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html_doc)
print(f"Wrote {out}: {len(html_doc)} bytes")
