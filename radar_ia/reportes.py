"""Reportes derivados de las respuestas crudas: 'por qué ganan otros' y muestra de auditoría."""
from __future__ import annotations

import csv
import html
import json
import random
from collections import Counter
from pathlib import Path

from .metricas import _url_limpia

NOMBRE_ASIST = {"anthropic": "Claude", "openai": "ChatGPT", "gemini": "Gemini"}


def _ganadas_por_otros(filas: list[dict]) -> list[dict]:
    out = []
    for f in filas:
        rec = (f.get("juez") or {}).get("recomendado_principal")
        if f.get("error") or not rec or rec == "fixed":
            continue
        out.append(f)
    orden = {"descubrimiento": 0, "comparacion": 1, "tecnico": 2, "precio": 3, "marca": 4}
    out.sort(key=lambda f: (orden.get(f["intencion"], 9), f["modo"], f["juez"]["recomendado_principal"], f["proveedor"]))
    return out


def _urls(f: dict) -> list[str]:
    vistos = []
    for c in f.get("citas") or []:
        u = _url_limpia(c)
        if u and u not in vistos:
            vistos.append(u)
    return vistos


def _resumen(filas: list[dict]):
    ganadas = _ganadas_por_otros(filas)
    ok = [f for f in filas if not f.get("error")]
    sin_ganador = sum(1 for f in ok if not (f.get("juez") or {}).get("recomendado_principal"))
    gana_fixed = sum(1 for f in ok if (f.get("juez") or {}).get("recomendado_principal") == "fixed")
    ganadores = Counter(f["juez"]["recomendado_principal"] for f in ganadas)
    por_cruce = Counter((f["juez"]["recomendado_principal"], NOMBRE_ASIST.get(f["proveedor"], f["proveedor"]),
                         f["intencion"], f["modo"]) for f in ganadas)
    urls = Counter(u for f in ganadas for u in _urls(f))
    return ganadas, len(ok), sin_ganador, gana_fixed, ganadores, por_cruce, urls


def por_que_ganan_md(filas: list[dict], fecha: str) -> str:
    ganadas, n, sin_ganador, gana_fixed, ganadores, por_cruce, urls = _resumen(filas)
    L = [f"# Por qué ganan otros · {fecha}", "",
         f"De {n} respuestas válidas: **{len(ganadas)}** recomiendan a otro proveedor como primera opción, "
         f"**{gana_fixed}** a Fixed y **{sin_ganador}** no eligen ninguno.", "",
         "## Ganadores", "", "| Proveedor | Veces |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in ganadores.most_common()]
    L += ["", "## Dónde gana cada uno", "", "| Ganador | Asistente | Intención | Modo | Veces |", "|---|---|---|---|---|"]
    L += [f"| {g} | {a} | {i} | {m} | {v} |" for (g, a, i, m), v in por_cruce.most_common()]
    L += ["", "## Respuestas", ""]
    for f in ganadas:
        j = f["juez"]
        L += [f"### {j['recomendado_principal']} · {NOMBRE_ASIST.get(f['proveedor'], f['proveedor'])} · {f['intencion']} · {f['modo']}",
              f"**Pregunta ({f['pregunta_id']}):** {f['pregunta']}", "",
              f"> {(j.get('justificacion_recomendado') or '(el juez no extrajo fragmento)').strip()}", ""]
        u = _urls(f)
        if u:
            L.append("URLs citadas: " + " · ".join(u))
        L.append("")
    L += ["## URLs a superar", "", "Más citadas en las respuestas donde gana otro proveedor.", "",
          "| # | URL | Citas |", "|---|---|---|"]
    L += [f"| {i} | {u} | {c} |" for i, (u, c) in enumerate(urls.most_common(30), 1)]
    return "\n".join(L) + "\n"


def por_que_ganan_html(filas: list[dict], fecha: str) -> str:
    ganadas, n, sin_ganador, gana_fixed, ganadores, por_cruce, urls = _resumen(filas)
    e = html.escape
    maxg = max(ganadores.values(), default=1)
    filas_g = "".join(f'<div class="bar"><span>{e(k)}</span><div class="t"><div class="f" style="width:{100 * v / maxg:.0f}%"></div></div><b>{v}</b></div>'
                      for k, v in ganadores.most_common())
    cruce = "".join(f"<tr><td>{e(g)}</td><td>{e(a)}</td><td>{e(i)}</td><td>{e(m.replace('_', ' '))}</td><td class=n>{v}</td></tr>"
                    for (g, a, i, m), v in por_cruce.most_common())
    cards = []
    for f in ganadas:
        j = f["juez"]
        links = "".join(f'<li>{e(u)}</li>' for u in _urls(f))
        cards.append(f"""<details data-int="{e(f['intencion'])}"><summary><b>{e(j['recomendado_principal'])}</b>
<span class=tag>{e(NOMBRE_ASIST.get(f['proveedor'], f['proveedor']))}</span><span class=tag>{e(f['intencion'])}</span>
<span class=tag>{e(f['modo'].replace('_', ' '))}</span><span class=q>{e(f['pregunta'])}</span></summary>
<blockquote>{e((j.get('justificacion_recomendado') or '(sin fragmento)').strip())}</blockquote>
{f'<ul class=urls>{links}</ul>' if links else '<p class=muted>Sin URLs citadas</p>'}</details>""")
    url_rows = "".join(f"<tr><td class=n>{i}</td><td class=u>{e(u)}</td><td class=n>{c}</td></tr>"
                       for i, (u, c) in enumerate(urls.most_common(30), 1))
    intents = sorted({f["intencion"] for f in ganadas})
    botones = '<button class="on" data-f="">Todas</button>' + "".join(f'<button data-f="{e(i)}">{e(i)}</button>' for i in intents)
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Por qué ganan otros</title>
<style>
:root{{--bg:#0d1117;--s:#161b22;--s2:#1c2128;--b:#21262d;--fg:#e6edf3;--m:#768390;--a:#2dd4bf;--c:#6e7bfa;color-scheme:dark}}
@media (prefers-color-scheme:light){{:root:not([data-theme="dark"]){{--bg:#f6f8fa;--s:#fff;--s2:#f0f3f6;--b:#d0d7de;--fg:#1f2328;--m:#59636e;--a:#0d7a6e;--c:#4255c4;color-scheme:light}}}}
:root[data-theme="light"]{{--bg:#f6f8fa;--s:#fff;--s2:#f0f3f6;--b:#d0d7de;--fg:#1f2328;--m:#59636e;--a:#0d7a6e;--c:#4255c4;color-scheme:light}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,sans-serif;padding:24px 16px;max-width:1000px;margin:auto}}
a{{color:var(--a)}}h1{{font-size:20px;margin:0 0 4px}}h2{{font-size:12px;text-transform:uppercase;letter-spacing:.7px;color:var(--m);margin:0 0 14px}}
.sec{{background:var(--s);border:1px solid var(--b);border-radius:10px;padding:18px 20px;margin:16px 0}}
.muted{{color:var(--m)}}.bar{{display:grid;grid-template-columns:110px 1fr 36px;gap:8px;align-items:center;margin:6px 0}}
.t{{height:14px;background:var(--s2);border-radius:4px;overflow:hidden}}.f{{height:100%;background:var(--c)}}
table{{width:100%;border-collapse:collapse;font-size:13px}}td,th{{padding:6px 8px;border-bottom:1px solid var(--b);text-align:left}}
.n{{text-align:right;font-variant-numeric:tabular-nums}}.u{{word-break:break-all}}.tbl{{overflow-x:auto}}
details{{border-bottom:1px solid var(--b);padding:8px 0}}summary{{cursor:pointer}}.tag{{font-size:11px;border:1px solid var(--b);border-radius:10px;padding:1px 8px;margin-left:6px;color:var(--m)}}
.q{{display:block;color:var(--m);font-size:12px;margin-top:2px}}blockquote{{border-left:3px solid var(--a);margin:10px 0;padding:4px 12px;color:var(--fg)}}
.urls{{font-size:12px;color:var(--m);word-break:break-all}}button{{background:var(--s2);color:var(--m);border:1px solid var(--b);border-radius:14px;padding:4px 12px;margin:0 6px 8px 0;cursor:pointer}}
button.on{{color:var(--a);border-color:var(--a)}}
</style></head><body>
<p><a href="index.html">← Radar IA</a></p>
<h1>Por qué ganan otros · {e(fecha)}</h1>
<p class=muted>De {n} respuestas válidas: <b>{len(ganadas)}</b> recomiendan a otro proveedor como primera opción, <b>{gana_fixed}</b> a Fixed y <b>{sin_ganador}</b> no eligen ninguno.</p>
<div class=sec><h2>Ganadores</h2>{filas_g or '<p class=muted>Ninguno</p>'}</div>
<div class=sec><h2>Dónde gana cada uno</h2><div class=tbl><table><tr><th>Ganador</th><th>Asistente</th><th>Intención</th><th>Modo</th><th class=n>Veces</th></tr>{cruce}</table></div></div>
<div class=sec><h2>URLs a superar</h2><p class=muted>Más citadas en las respuestas donde gana otro proveedor. Gemini solo informa el dominio.</p>
<div class=tbl><table><tr><th class=n>#</th><th>URL</th><th class=n>Citas</th></tr>{url_rows}</table></div></div>
<div class=sec><h2>Respuestas ({len(ganadas)})</h2><div id=fil>{botones}</div>{''.join(cards)}</div>
<script>
document.querySelectorAll('#fil button').forEach(b=>b.onclick=()=>{{
 document.querySelectorAll('#fil button').forEach(x=>x.classList.toggle('on',x===b));
 document.querySelectorAll('details').forEach(d=>d.style.display=(!b.dataset.f||d.dataset.int===b.dataset.f)?'':'none');}});
</script></body></html>"""


def exportar_auditoria(filas: list[dict], destino: Path, pct: float = 10, semilla: int | None = None) -> Path:
    """Muestra aleatoria de respuestas con lo extraído y columnas vacías para que un humano marque si está bien."""
    validas = [(i, f) for i, f in enumerate(filas) if not f.get("error")]
    if semilla is None:
        semilla = random.randrange(10 ** 6)
    k = max(1, round(len(validas) * pct / 100))
    muestra = sorted(random.Random(semilla).sample(validas, min(k, len(validas))), key=lambda x: x[0])
    cols = ["fila", "asistente", "modo", "intencion", "pregunta_id", "pregunta", "respuesta", "urls_citadas",
            "menciones_contadas", "alias_debiles_descartados", "recomendado_juez", "justificacion_juez", "fixed_juez",
            "REVISOR_menciones_ok", "REVISOR_faltan", "REVISOR_sobran", "REVISOR_recomendado_ok", "REVISOR_errores_ok", "REVISOR_notas"]
    with open(destino, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([f"# semilla={semilla} pct={pct} n={len(muestra)}/{len(validas)}"])
        w.writerow(cols)
        for i, f in muestra:
            j = f.get("juez") or {}
            contadas = [d["clave"] for d in f.get("menciones", [])]
            descartadas = [d["clave"] for d in f.get("alias", []) if d["clave"] not in contadas]
            w.writerow([i, f["proveedor"], f["modo"], f["intencion"], f["pregunta_id"], f["pregunta"], f.get("respuesta", ""),
                        " ".join(_urls(f)), ", ".join(contadas), ", ".join(descartadas), j.get("recomendado_principal") or "",
                        j.get("justificacion_recomendado") or "", json.dumps(j.get("fixed") or {}, ensure_ascii=False),
                        "", "", "", "", "", ""])
    return destino
