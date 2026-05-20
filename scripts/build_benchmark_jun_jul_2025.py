"""Build docs/benchmark_jun_jul_2025.{md,html} from bench JSON + Mongo data."""
import json
import os
import html
import re
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(REPO, "docs")

bench = json.load(open(os.path.join(DOCS, "bench_jun_jul_2025.json"), encoding="utf-8"))
por_gaceta = json.load(open(os.path.join(DOCS, "personas_por_gaceta_jun_jul_2025.json"), encoding="utf-8"))
por_pagina = json.load(open(os.path.join(DOCS, "personas_por_pagina_jun_jul_2025.json"), encoding="utf-8"))
stats = bench["stats"]

# Aggregate por pagina
pages_dict = defaultdict(list)
for r in por_pagina:
    key = (r.get("numero_gaceta") or "?", r.get("pagina") if r.get("pagina") is not None else "?")
    pages_dict[key].append(r)

# Classify each persona aparicion as "pre-existente" or "nueva"
# A persona is "nueva" if it has `tipo` field in our schema (we set tipo only in this gemma3 era)
nueva_cedulas = {r["cedula"] for r in por_pagina if r.get("tipo") and r.get("tipo") != "natural"}
# Better: query directly which persona_ids are with `tipo` — using mongo would be more accurate.
# For simplicity: rely on `tipo` field being explicit (organismo, juridica) or check via the bench stats.
# Cedulas that gemma3 has marked with tipo='natural' (created in our runs) — these are "nuevas".
# Existing personas without `tipo` field are pre-existentes (created by regex extractor).
# In our por_pagina query, we send tipo or "natural" as default — so distinguishing is tricky.
# We requery: nueva = persona has the `tipo` field explicitly stored.

# We need a more reliable signal: query Mongo with raw access. But we can approximate:
# Cedulas with format V-NNNNNNNN where the persona was created in this run.
# We'll trust the BD post-snapshot list of personas with tipo field.

# Load it from a fresh query (already computed above in command, save the list)
nuevas_set = set()
try:
    nuevas_list = json.load(open(os.path.join(DOCS, "nuevas_cedulas_jun_jul.json"), encoding="utf-8"))
    nuevas_set = set(nuevas_list)
except Exception:
    pass

def is_nueva(cedula: str) -> bool:
    return cedula in nuevas_set

# --- MARKDOWN ---
md_lines = []
ml = md_lines.append

ml("# Benchmark Jun-Jul 2025 - Ollama gemma3:12b")
ml("")
ml("**Fecha:** 2026-05-20  ")
ml("**Modelo:** `gemma3:12b-it-q4_K_M` via Ollama local  ")
ml("**Hardware:** RTX 3060 12GB + i7-12700KF + 32GB RAM  ")
ml("**Periodo:** Gacetas de Junio y Julio 2025 (filename `*-2025-06-*` o `*-2025-07-*`)")
ml("")

ml("## Universo")
ml("")
ml("| Metrica | Valor |")
ml("|---|---|")
ml(f"| Gacetas Jun-Jul 2025 | 50 |")
ml(f"| Paginas totales | 712 |")
ml(f"| Chunks emitidos | {stats['chunks']} |")
ml(f"| Tokens de entrada estimados | {stats['tokens_total']:,} |")
ml(f"| **Tiempo total** | **{stats['wall_seconds']/60:.0f} min ({stats['wall_seconds']/3600:.1f} h)** |")
ml(f"| Personas devueltas por el modelo | {stats['personas_returned']} |")
ml(f"| Personas validadas (kept) | {stats['personas_kept']} |")
ml(f"| Personas nuevas creadas | {stats['personas_created']} |")
ml(f"| Personas pre-existentes actualizadas | {stats['personas_updated']} |")
ml(f"| Personas con conflicto detectado | {stats.get('personas_conflict_updated',0)} |")
ml(f"| Marcadas baja confianza | {stats.get('needs_review',0)} |")
ml("")

ml("## Filtrado anti-alucinacion")
ml("")
ml("| Categoria | Conteo |")
ml("|---|---:|")
ml(f"| Dropped sin cedula | {stats.get('dropped_no_cedula',0)} |")
ml(f"| Dropped no aparece en bloque | {stats.get('dropped_not_in_text',0)} |")
ml(f"| Dropped placeholder | {stats.get('dropped_placeholder',0)} |")
ml(f"| Dropped sin RIF | {stats.get('dropped_no_rif',0)} |")
ml(f"| **Total descartado** | **{stats.get('dropped_no_cedula',0)+stats.get('dropped_not_in_text',0)+stats.get('dropped_placeholder',0)+stats.get('dropped_no_rif',0)}** |")
total_descartado = stats.get('dropped_no_cedula',0)+stats.get('dropped_not_in_text',0)+stats.get('dropped_placeholder',0)+stats.get('dropped_no_rif',0)
rate = 100.0 * total_descartado / stats['personas_returned'] if stats['personas_returned'] else 0
ml(f"| % descartado del total | {rate:.1f}% |")
ml("")

ml("## Pre-existentes vs nuevas")
ml("")
ml("- **Personas unicas mencionadas en Jun-Jul 2025:** 1,001")
ml("- **Pre-existentes en BD revalidadas por gemma3:** 819")
ml("- **Nuevas aportadas por gemma3 (creadas con campo `tipo`):** 182")
ml("- De las 182 nuevas: 80 naturales, 98 organismos, 4 juridicas (RIF)")
ml("- 293 marcadas `por_verificar` (conflictos / baja confianza)")
ml("")

ml("## Personas por gaceta")
ml("")
ml("Top 25 gacetas por cantidad de personas distintas mencionadas:")
ml("")
ml("| Gaceta | Fecha | Personas | Paginas con personas |")
ml("|---|---|---:|---:|")
for g in por_gaceta[:25]:
    ml(f"| {g['numero_gaceta']} | {g['fecha']} | {g['personas']} | {g['paginas_con_personas']} |")
ml("")
ml(f"_Total gacetas con menciones: {len(por_gaceta)} / 50_")
ml("")

ml("## Personas por pagina (top 40 paginas con mas menciones)")
ml("")
page_counts = sorted(((k, len(v)) for k, v in pages_dict.items()), key=lambda x: -x[1])[:40]
ml("| Gaceta | Pagina | Personas en pagina |")
ml("|---|---:|---:|")
for (g, p), n in page_counts:
    ml(f"| {g} | {p} | {n} |")
ml("")

ml("## Personas detalle (etiquetadas)")
ml("")
ml("Etiquetas:")
ml("- :NEW: persona aportada por gemma3 (no existia antes)")
ml("- :OK: persona pre-existente en BD revalidada por gemma3")
ml("- :CONFLICT: marcada `por_verificar`")
ml("")
ml("Muestras (primeras 80 menciones ordenadas por gaceta y pagina):")
ml("")
ml("| Gaceta | Pag | Cedula | Nombre | Tipo | Etiqueta | Contexto |")
ml("|---|---:|---|---|---|---|---|")
sample = sorted(por_pagina, key=lambda r: (r.get('numero_gaceta') or '', r.get('pagina') if isinstance(r.get('pagina'), int) else 0))[:80]
for r in sample:
    etiqueta = ":NEW:" if is_nueva(r['cedula']) else ":OK:"
    if r.get('por_verificar'):
        etiqueta = ":CONFLICT:"
    nombre = (r.get('nombre') or '').replace('|', '/')[:50]
    contexto = (r.get('contexto') or '').replace('|', '/')[:70]
    ml(f"| {r.get('numero_gaceta','?')} | {r.get('pagina','?')} | {r.get('cedula','?')} | {nombre} | {r.get('tipo','natural')} | {etiqueta} | {contexto} |")
ml("")
ml(f"_Listado completo en `docs/personas_por_pagina_jun_jul_2025.json` (total: {len(por_pagina)} apariciones)_")
ml("")

with open(os.path.join(DOCS, "benchmark_jun_jul_2025.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))

# --- HTML ---
def tr(*cells):
    return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"

por_gaceta_rows = "\n".join(
    tr(html.escape(str(g['numero_gaceta'])), html.escape(str(g['fecha'])),
       f"<b>{g['personas']}</b>", str(g['paginas_con_personas']))
    for g in por_gaceta[:30]
)

page_rows = "\n".join(
    tr(html.escape(str(g)), str(p), f"<b>{n}</b>") for (g,p), n in page_counts
)

# Per gaceta with personas list (each person has label)
gacetas_with_details_rows = []
for g in por_gaceta[:15]:
    num = g['numero_gaceta']
    sample_rows = [r for r in por_pagina if r.get('numero_gaceta') == num]
    sample_rows.sort(key=lambda x: x.get('pagina') if isinstance(x.get('pagina'), int) else 0)
    inner = "<ul style='margin:4px 0;padding-left:18px;'>"
    for r in sample_rows[:12]:
        if r.get('por_verificar'):
            tag = '<span class="tag tag-bad">CONFLICT</span>'
        elif is_nueva(r['cedula']):
            tag = '<span class="tag tag-new">NUEVA</span>'
        else:
            tag = '<span class="tag tag-ok">YA-ESTABA</span>'
        inner += f"<li>{tag} <code>{html.escape(r['cedula'])}</code> p.{r.get('pagina','?')} &mdash; {html.escape((r.get('nombre') or '')[:55])} <span class='small'>({html.escape((r.get('contexto') or '')[:50])})</span></li>"
    inner += "</ul>"
    gacetas_with_details_rows.append(
        f"<tr><td><b>{html.escape(str(num))}</b><br><span class='small'>{html.escape(str(g['fecha']))}</span></td><td>{g['personas']} personas / {g['paginas_con_personas']} pags</td><td>{inner}</td></tr>"
    )

gacetas_details = "\n".join(gacetas_with_details_rows)

style = """
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 1200px; margin: 20px auto; padding: 20px; color: #222; background: #fff; }
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
  .tag { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 0.72em; font-weight: 700; margin-right: 4px; }
  .tag-ok { background: #dbeafe; color: #1e40af; }
  .tag-new { background: #d1fae5; color: #065f46; }
  .tag-bad { background: #fee2e2; color: #991b1b; }
  .small { font-size: 0.78em; color: #666; }
  code { background: #f1f5f9; padding: 1px 5px; border-radius: 3px; font-size: 0.85em; }
  @media print {
    body { max-width: 100%; margin: 0; padding: 8mm; font-size: 9pt; }
    h2 { page-break-after: avoid; }
    table { page-break-inside: auto; font-size: 8pt; }
    tr { page-break-inside: avoid; }
    .cards { display: block; }
    .card { display: inline-block; width: 23%; margin: 2px; padding: 8px; }
    .no-print { display: none; }
  }
  @page { size: A4; margin: 10mm; }
"""

flagged = stats.get('personas_conflict_updated',0) + stats.get('needs_review',0)

html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Benchmark Jun-Jul 2025 - Ollama gemma3:12b</title>
<style>{style}</style>
</head>
<body>

<h1>Benchmark Jun-Jul 2025 &mdash; <code>gemma3:12b-it-q4_K_M</code></h1>

<div class="meta">
  <b>Fecha:</b> 2026-05-20 &nbsp;|&nbsp;
  <b>Hardware:</b> RTX 3060 12GB &nbsp;|&nbsp;
  <b>Backend:</b> Ollama local &nbsp;|&nbsp;
  <b>Gacetas:</b> 50 (jun-jul 2025) &nbsp;|&nbsp;
  <b>Paginas:</b> 712
</div>

<div style="margin: 12px 0;">
  <span class="tag tag-new">NUEVA</span> = persona que el modelo aporto nueva &nbsp;
  <span class="tag tag-ok">YA-ESTABA</span> = persona pre-existente revalidada &nbsp;
  <span class="tag tag-bad">CONFLICT</span> = marcada `por_verificar`
</div>

<h2>Resumen ejecutivo</h2>
<div class="cards">
  <div class="card"><div class="num">{stats['wall_seconds']/60:.0f} min</div><div class="lbl">Tiempo total ({stats['wall_seconds']/3600:.1f} h)</div></div>
  <div class="card"><div class="num">{stats['personas_returned']}</div><div class="lbl">Devueltas por el modelo</div></div>
  <div class="card"><div class="num">{stats['personas_kept']}</div><div class="lbl">Validadas (kept)</div></div>
  <div class="card"><div class="num">{stats['personas_created']}</div><div class="lbl">Nuevas creadas</div></div>
  <div class="card"><div class="num">{stats['personas_updated']}</div><div class="lbl">Pre-existentes actualizadas</div></div>
  <div class="card"><div class="num">{flagged}</div><div class="lbl">Conflictos / baja confianza</div></div>
</div>

<h2>Pre-existentes vs nuevas (universo Jun-Jul 2025)</h2>
<table>
<tr><th>Categoria</th><th>Conteo</th></tr>
<tr><td>Personas unicas mencionadas en Jun-Jul 2025</td><td><b>1,001</b></td></tr>
<tr><td><span class="tag tag-ok">YA-ESTABA</span> Pre-existentes revalidadas por gemma3</td><td><b>819</b></td></tr>
<tr><td><span class="tag tag-new">NUEVA</span> Personas nuevas aportadas por gemma3</td><td><b>182</b></td></tr>
<tr><td>&nbsp;&nbsp;de los cuales naturales (V-/E-)</td><td>80</td></tr>
<tr><td>&nbsp;&nbsp;organismos (gobierno)</td><td>98</td></tr>
<tr><td>&nbsp;&nbsp;juridicas (RIF)</td><td>4</td></tr>
<tr><td><span class="tag tag-bad">CONFLICT</span> Marcadas <code>por_verificar</code></td><td>293</td></tr>
</table>

<h2>Personas por gaceta (top 30)</h2>
<table>
<tr><th>Gaceta</th><th>Fecha</th><th>Personas</th><th>Paginas con personas</th></tr>
{por_gaceta_rows}
</table>
<p class="small">Total gacetas con menciones: {len(por_gaceta)} / 50</p>

<h2>Personas por pagina (top 40 paginas con mas menciones)</h2>
<table>
<tr><th>Gaceta</th><th>Pagina</th><th>Personas en pagina</th></tr>
{page_rows}
</table>

<h2>Detalle por gaceta (top 15 con personas etiquetadas)</h2>
<table>
<tr><th>Gaceta</th><th>Conteo</th><th>Personas etiquetadas (primeras 12)</th></tr>
{gacetas_details}
</table>
<p class="small">Listado completo en <code>docs/personas_por_pagina_jun_jul_2025.json</code></p>

<h2>Comparativa vs run 2026</h2>
<table>
<tr><th>Metrica</th><th>2026 (59 gacetas)</th><th>Jun-Jul 2025 (50 gacetas)</th></tr>
<tr><td>Paginas</td><td>556</td><td>712</td></tr>
<tr><td>Chunks</td><td>92</td><td>{stats['chunks']}</td></tr>
<tr><td>Tiempo</td><td>3h 14m</td><td>{stats['wall_seconds']/3600:.1f}h</td></tr>
<tr><td>Devueltas</td><td>691</td><td>{stats['personas_returned']}</td></tr>
<tr><td>Validadas</td><td>554</td><td>{stats['personas_kept']}</td></tr>
<tr><td>Nuevas creadas</td><td>132</td><td>{stats['personas_created']}</td></tr>
<tr><td>Pre-existentes actualizadas</td><td>333</td><td>{stats['personas_updated']}</td></tr>
<tr><td>Conflictos detectados</td><td>96</td><td>{stats.get('personas_conflict_updated',0)+stats.get('needs_review',0)}</td></tr>
</table>

<p class="small no-print">Generado por <code>scripts/build_benchmark_jun_jul_2025.py</code></p>

</body></html>
"""

with open(os.path.join(DOCS, "benchmark_jun_jul_2025.html"), "w", encoding="utf-8") as f:
    f.write(html_doc)

print(f"Wrote benchmark_jun_jul_2025.md ({sum(len(l)+1 for l in md_lines)} chars) and .html ({len(html_doc)} chars)")
