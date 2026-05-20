"""Build docs/gaceta_43157_personas.html (printable A4) with all personas labeled."""
import json
import os
import html
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(REPO, "docs")

d = json.load(open(os.path.join(DOCS, "gaceta_43157_personas.json"), encoding="utf-8"))
gaceta = d.get("gaceta", {})
meta = d.get("meta", {})
personas = d.get("personas", [])

# Group by pagina
by_page = defaultdict(list)
for p in personas:
    by_page[p.get("pagina") if p.get("pagina") is not None else 0].append(p)

# Count source: "nueva" if tipo field is set explicitly, else "ya_estaba"
def label(p):
    if p.get("por_verificar"):
        return ("CONFLICT", "tag-bad")
    if p.get("has_tipo_field"):
        return ("NUEVA", "tag-new")
    return ("YA-ESTABA", "tag-ok")

def get_tipo(p):
    return p.get("tipo_value") or "natural"

count_nueva = sum(1 for p in personas if p.get("has_tipo_field") and not p.get("por_verificar"))
count_yaestaba = sum(1 for p in personas if not p.get("has_tipo_field") and not p.get("por_verificar"))
count_conflict = sum(1 for p in personas if p.get("por_verificar"))
count_natural = sum(1 for p in personas if get_tipo(p) == "natural")
count_organismo = sum(1 for p in personas if get_tipo(p) == "organismo")
count_juridica = sum(1 for p in personas if get_tipo(p) == "juridica")

style = """
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 1100px; margin: 20px auto; padding: 20px; color: #222; background: #fff; }
  h1 { border-bottom: 3px solid #003366; padding-bottom: 6px; color: #003366; }
  h2 { color: #003366; border-bottom: 1px solid #ccc; padding-bottom: 4px; margin-top: 24px; }
  h3 { color: #555; margin-top: 18px; background: #eff6ff; padding: 6px 10px; border-left: 3px solid #003366; }
  .meta { background: #f8f9fa; border-left: 4px solid #003366; padding: 10px 16px; margin: 16px 0; }
  .cards { display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0; }
  .card { flex: 1 1 160px; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px; }
  .card .num { font-size: 1.6em; font-weight: 700; color: #003366; }
  .card .lbl { font-size: 0.8em; color: #555; }
  table { border-collapse: collapse; width: 100%; font-size: 0.84em; margin: 8px 0; }
  th, td { border: 1px solid #ccc; padding: 4px 8px; text-align: left; vertical-align: top; }
  th { background: #e2e8f0; color: #003366; }
  tr:nth-child(even) { background: #f8fafc; }
  .tag { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 0.72em; font-weight: 700; }
  .tag-ok { background: #dbeafe; color: #1e40af; }
  .tag-new { background: #d1fae5; color: #065f46; }
  .tag-bad { background: #fee2e2; color: #991b1b; }
  .small { font-size: 0.78em; color: #666; }
  code { background: #f1f5f9; padding: 1px 5px; border-radius: 3px; font-size: 0.85em; }
  @media print {
    body { max-width: 100%; margin: 0; padding: 8mm; font-size: 9pt; }
    h2, h3 { page-break-after: avoid; }
    table { page-break-inside: auto; font-size: 8pt; }
    tr { page-break-inside: avoid; }
    .cards { display: block; }
    .card { display: inline-block; width: 23%; margin: 2px; padding: 6px; }
    .no-print { display: none; }
  }
  @page { size: A4; margin: 10mm; }
"""

def fmt_persona_row(p):
    lbl, klass = label(p)
    tag = f'<span class="tag {klass}">{lbl}</span>'
    ced = html.escape(p.get("cedula") or "")
    nom = html.escape((p.get("nombre") or "")[:80])
    tipo = html.escape(get_tipo(p))
    ctx = html.escape((p.get("contexto") or "")[:100])
    return f"<tr><td>{tag}</td><td><code>{ced}</code></td><td>{nom}</td><td>{tipo}</td><td>{ctx}</td></tr>"

# Build per-page sections
sections = []
for pag in sorted(by_page.keys()):
    grp = sorted(by_page[pag], key=lambda x: (label(x)[0], x.get("nombre") or ""))
    rows = "\n".join(fmt_persona_row(p) for p in grp)
    sections.append(f"""
<h3>Pagina {pag} — {len(grp)} persona(s)</h3>
<table>
<tr><th>Etiqueta</th><th>Cedula / ID</th><th>Nombre</th><th>Tipo</th><th>Contexto</th></tr>
{rows}
</table>""")

html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Gaceta {gaceta.get('numero_gaceta','?')} - Resumen de Personas</title>
<style>{style}</style>
</head>
<body>

<h1>Gaceta Oficial Nro. {gaceta.get('numero_gaceta','?')} — Resumen de personas mencionadas</h1>

<div class="meta">
  <b>Numero:</b> {html.escape(str(gaceta.get('numero_gaceta','?')))} &nbsp;|&nbsp;
  <b>Fecha:</b> {html.escape(str(gaceta.get('fecha','?')))} &nbsp;|&nbsp;
  <b>Archivo:</b> <code>{html.escape(str(gaceta.get('filename','?')))}</code> &nbsp;|&nbsp;
  <b>Total apariciones:</b> {len(personas)} &nbsp;|&nbsp;
  <b>Paginas con personas:</b> {len(by_page)}
</div>

<div style="margin: 10px 0;">
  <span class="tag tag-new">NUEVA</span> = persona aportada por gemma3 (creada en este run) &nbsp;
  <span class="tag tag-ok">YA-ESTABA</span> = persona pre-existente en BD &nbsp;
  <span class="tag tag-bad">CONFLICT</span> = marcada <code>por_verificar</code>
</div>

<h2>Resumen</h2>
<div class="cards">
  <div class="card"><div class="num">{len(personas)}</div><div class="lbl">Total apariciones</div></div>
  <div class="card"><div class="num">{count_yaestaba}</div><div class="lbl"><span class="tag tag-ok">YA-ESTABA</span></div></div>
  <div class="card"><div class="num">{count_nueva}</div><div class="lbl"><span class="tag tag-new">NUEVA</span></div></div>
  <div class="card"><div class="num">{count_conflict}</div><div class="lbl"><span class="tag tag-bad">CONFLICT</span></div></div>
  <div class="card"><div class="num">{count_natural}</div><div class="lbl">naturales (V-/E-)</div></div>
  <div class="card"><div class="num">{count_organismo}</div><div class="lbl">organismos</div></div>
  <div class="card"><div class="num">{count_juridica}</div><div class="lbl">juridicas (RIF)</div></div>
</div>

<h2>Personas agrupadas por pagina</h2>
{''.join(sections)}

<p class="small no-print" style="margin-top:30px;">Fuente: <code>gacetas_db.persona</code> + <code>persona_gaceta</code> + <code>gaceta</code>. Generado por <code>scripts/build_gaceta_43157_report.py</code>.</p>

</body></html>
"""

out_html = os.path.join(DOCS, "gaceta_43157_personas.html")
with open(out_html, "w", encoding="utf-8") as f:
    f.write(html_doc)
print(f"Wrote {out_html}: {len(html_doc)} bytes")
print(f"  total: {len(personas)} | nueva: {count_nueva} | ya_estaba: {count_yaestaba} | conflict: {count_conflict}")
