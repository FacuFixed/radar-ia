"""Genera HISTORIAL.md y docs/index.html a partir de todos los JSONs de resultados."""
from __future__ import annotations

import json
import glob
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _cargar_semanas() -> list[dict]:
    """Carga todos los JSONs de resultados en orden cronológico."""
    archivos = sorted(glob.glob(str(RAIZ / "resultados" / "ia_llm__*.json")))
    semanas = []
    for p in archivos:
        try:
            data = json.loads(Path(p).read_text(encoding="utf-8"))
            if not data.get("simulado"):
                semanas.append(data)
        except Exception:
            pass
    return semanas


def _ranking_pos(menciones_uy: dict) -> tuple[int, int]:
    ranking = sorted(menciones_uy.items(), key=lambda x: -x[1])
    pos = next((i + 1 for i, (k, _) in enumerate(ranking) if k == "fixed"), None)
    return pos, len(ranking)


def generar_historial(semanas: list[dict]) -> str:
    lines = [
        "# Radar IA · Fixed — Historial",
        "",
        "Evolución semanal de visibilidad de Fixed en Claude, ChatGPT y Gemini.",
        "Generado automáticamente por `python -m radar_ia run`.",
        "",
        "---",
        "",
    ]
    for s in reversed(semanas):
        fecha = s["fecha"]
        g = s["metricas"]["general_sin_marca"]
        pos, total = _ranking_pos(g.get("menciones_uy", {}))
        menciones_uy = g.get("menciones_uy", {})
        total_m = sum(menciones_uy.values())
        fixed_m = menciones_uy.get("fixed", 0)
        lider = next(iter(menciones_uy), "—")
        lider_m = menciones_uy.get(lider, 0)
        brecha = lider_m - fixed_m

        por_modelo = s["metricas"].get("por_modelo_y_modo", {})
        con_busqueda = {k.split("|")[0]: v for k, v in por_modelo.items() if "con_busqueda" in k}
        sin_busqueda = {k.split("|")[0]: v for k, v in por_modelo.items() if "sin_busqueda" in k}

        errores = len(s["metricas"].get("errores_de_llamada", []))
        config = s.get("config", {})

        lines += [
            f"## {fecha}",
            "",
            f"**Posición:** #{pos}/{total}  |  "
            f"**SoV UY:** {g.get('share_of_voice_fixed_uy')}%  |  "
            f"**Menciona:** {g.get('pct_menciona_fixed')}%  |  "
            f"**Top 1:** {g.get('pct_fixed_recomendado_principal')}%",
            "",
            f"Brecha vs líder ({lider}): −{brecha} menciones ({fixed_m} vs {lider_m})",
            f"Menciones totales UY: {total_m}  |  Preguntas: {config.get('preguntas', '?')}  |  "
            f"Corridas: {config.get('corridas', '?')}  |  Modos: {', '.join(config.get('modos', []))}",
            "",
        ]

        if con_busqueda:
            lines.append("**Con búsqueda web:**")
            for prov, stats in sorted(con_busqueda.items()):
                lines.append(
                    f"- {prov}: menciona {stats.get('pct_menciona_fixed')}% | "
                    f"top1 {stats.get('pct_fixed_recomendado_principal')}% | "
                    f"SoV {stats.get('share_of_voice_fixed_uy')}%"
                )
            lines.append("")

        if sin_busqueda:
            vals = [v.get("pct_menciona_fixed", 0) for v in sin_busqueda.values()]
            if all(v == 0 for v in vals):
                lines.append("**Sin búsqueda web:** 0% en todos los modelos — Fixed no está en memoria de entrenamiento.")
            else:
                lines.append("**Sin búsqueda web:**")
                for prov, stats in sorted(sin_busqueda.items()):
                    lines.append(f"- {prov}: menciona {stats.get('pct_menciona_fixed')}%")
            lines.append("")

        ranking_top5 = list(menciones_uy.items())[:6]
        lines.append("**Ranking UY (top 6):** " + " · ".join(
            f"{'**' if k == 'fixed' else ''}{k} {n}{'**' if k == 'fixed' else ''}"
            for k, n in ranking_top5
        ))
        lines.append("")

        if errores:
            lines.append(f"⚠ {errores} llamadas con error")
            lines.append("")

        notas_path = RAIZ / "resultados" / f"notas_{fecha}.md"
        if notas_path.exists():
            lines.append("**Notas / acciones esa semana:**")
            lines.append(notas_path.read_text(encoding="utf-8").strip())
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def generar_dashboard_html(semanas: list[dict]) -> str:
    """Genera el HTML del dashboard histórico con datos embebidos."""
    series = []
    for s in semanas:
        g = s["metricas"]["general_sin_marca"]
        pos, total = _ranking_pos(g.get("menciones_uy", {}))
        menciones_uy = g.get("menciones_uy", {})
        lider = next(iter(menciones_uy), None)
        lider_m = menciones_uy.get(lider, 0) if lider else 0
        fixed_m = menciones_uy.get("fixed", 0)

        por_modelo = s["metricas"].get("por_modelo_y_modo", {})
        por_asistente = {}
        for k, v in por_modelo.items():
            prov, modo = k.split("|")
            if prov not in por_asistente:
                por_asistente[prov] = {}
            por_asistente[prov][modo] = v

        series.append({
            "fecha": s["fecha"],
            "pos": pos,
            "total_provs": total,
            "sov": g.get("share_of_voice_fixed_uy"),
            "menciona": g.get("pct_menciona_fixed"),
            "top1": g.get("pct_fixed_recomendado_principal"),
            "pos_media": g.get("posicion_media_fixed"),
            "lider": lider,
            "lider_m": lider_m,
            "fixed_m": fixed_m,
            "brecha": lider_m - fixed_m,
            "ranking": dict(list(menciones_uy.items())[:8]),
            "por_asistente": por_asistente,
        })

    data_js = json.dumps(series, ensure_ascii=False)

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Radar IA · Fixed</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500&display=swap">
<style>
:root {{
  --bg: #0d1117; --surface: #161b22; --surface2: #1c2128; --border: #21262d;
  --fg: #e6edf3; --fg2: #adbac7; --muted: #768390;
  --fixed: #2dd4bf; --fixed-bg: #0d2e2b;
  --comp: #6e7bfa; --warn: #f0a020; --danger: #e05252; --good: #3fb950;
  color-scheme: dark;
}}
@media (prefers-color-scheme: light) {{ :root:not([data-theme="dark"]) {{
  --bg: #f6f8fa; --surface: #fff; --surface2: #f0f3f6; --border: #d0d7de;
  --fg: #1f2328; --fg2: #3d444d; --muted: #59636e;
  --fixed: #0d7a6e; --fixed-bg: #d3f5f1; --comp: #4255c4;
  --warn: #9a6700; --danger: #c0392b; --good: #1a7f37; color-scheme: light;
}} }}
:root[data-theme="light"] {{
  --bg: #f6f8fa; --surface: #fff; --surface2: #f0f3f6; --border: #d0d7de;
  --fg: #1f2328; --fg2: #3d444d; --muted: #59636e;
  --fixed: #0d7a6e; --fixed-bg: #d3f5f1; --comp: #4255c4;
  --warn: #9a6700; --danger: #c0392b; --good: #1a7f37; color-scheme: light;
}}
*, *::before, *::after {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--bg); color: var(--fg);
  font-family: 'Inter', system-ui, sans-serif; font-size: 14px; line-height: 1.5;
  padding: 24px max(16px, env(safe-area-inset-left,0px));
  padding-right: max(16px, env(safe-area-inset-right,0px));
}}
h1 {{ font-family:'Space Grotesk',sans-serif; font-size:20px; font-weight:700; margin:0 0 4px; letter-spacing:-0.3px; }}
h1 span {{ color:var(--muted); font-weight:500; }}
.subtitle {{ font-size:13px; color:var(--muted); margin-bottom:28px; }}
.kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-bottom:28px; }}
.kpi {{ background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:16px 18px; }}
.kpi.featured {{ border-color:var(--fixed); position:relative; overflow:hidden; }}
.kpi.featured::before {{ content:''; position:absolute; top:0; left:0; right:0; height:3px; background:var(--fixed); }}
.kpi-label {{ font-size:11px; font-weight:500; color:var(--muted); letter-spacing:.5px; text-transform:uppercase; margin-bottom:6px; }}
.kpi-val {{ font-family:'Space Grotesk',sans-serif; font-size:32px; font-weight:700; line-height:1; letter-spacing:-1px; font-variant-numeric:tabular-nums; }}
.kpi-val.accent {{ color:var(--fixed); }}
.kpi-sub {{ font-size:11px; color:var(--muted); margin-top:5px; }}
.kpi-sub strong {{ color:var(--warn); }}
.section {{ background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:20px 24px; margin-bottom:16px; }}
.section-title {{ font-family:'Space Grotesk',sans-serif; font-size:11px; font-weight:600; color:var(--fg2); letter-spacing:.8px; text-transform:uppercase; margin:0 0 18px; }}
/* Chart */
.chart-wrap {{ overflow-x:auto; }}
svg text {{ font-family:'Space Grotesk',sans-serif; }}
/* Week selector */
.week-tabs {{ display:flex; gap:6px; flex-wrap:wrap; margin-bottom:20px; }}
.week-tab {{ font-size:12px; font-family:'Space Grotesk',sans-serif; font-weight:500;
  padding:5px 12px; border-radius:20px; border:1px solid var(--border);
  background:var(--surface2); color:var(--muted); cursor:pointer; transition:.15s; }}
.week-tab:hover {{ border-color:var(--fixed); color:var(--fg); }}
.week-tab.active {{ background:var(--fixed-bg); border-color:var(--fixed); color:var(--fixed); }}
/* Ranking bars */
.rank-row {{ display:grid; grid-template-columns:20px 110px 1fr 48px; align-items:center; gap:8px; margin-bottom:8px; }}
.rank-num {{ font-size:11px; color:var(--muted); text-align:right; font-family:'Space Grotesk',sans-serif; font-variant-numeric:tabular-nums; }}
.rank-name {{ font-size:13px; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.rank-name.fixed {{ color:var(--fixed); font-weight:700; }}
.rank-track {{ height:18px; background:var(--surface2); border-radius:4px; overflow:hidden; min-width:0; }}
.rank-fill {{ height:100%; border-radius:4px; background:var(--comp); }}
.rank-fill.fixed {{ background:var(--fixed); }}
.rank-pct {{ font-size:12px; font-variant-numeric:tabular-nums; color:var(--muted); text-align:right; font-family:'Space Grotesk',sans-serif; }}
.rank-pct.fixed {{ color:var(--fixed); font-weight:600; }}
/* Asistentes */
.asist-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:12px; }}
.asist-card {{ background:var(--surface2); border:1px solid var(--border); border-radius:8px; padding:14px; }}
.asist-name {{ font-family:'Space Grotesk',sans-serif; font-weight:600; font-size:14px; display:flex; align-items:center; gap:7px; margin-bottom:12px; }}
.dot {{ width:8px; height:8px; border-radius:50%; display:inline-block; flex-shrink:0; }}
.stat {{ display:flex; justify-content:space-between; font-size:12px; padding:5px 0; border-bottom:1px solid var(--border); }}
.stat:last-child {{ border-bottom:none; }}
.stat-l {{ color:var(--fg2); }}
.stat-v {{ font-family:'Space Grotesk',sans-serif; font-weight:600; font-variant-numeric:tabular-nums; }}
.stat-v.good {{ color:var(--good); }} .stat-v.zero {{ color:var(--muted); }} .stat-v.mid {{ color:var(--warn); }}
.mode-label {{ font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.6px; margin:10px 0 6px; }}
.mode-label.con {{ color:var(--fixed); }} .mode-label.sin {{ color:var(--muted); }}
footer {{ margin-top:24px; font-size:11px; color:var(--muted); display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; }}
</style>
</head>
<body>
<h1>Radar IA <span>· Fixed</span></h1>
<div class="subtitle">Visibilidad en Claude, ChatGPT y Gemini · Actualización semanal automática</div>

<div class="kpi-grid">
  <div class="kpi featured"><div class="kpi-label">Posición UY</div><div class="kpi-val accent" id="k-pos"></div><div class="kpi-sub" id="k-pos-sub"></div></div>
  <div class="kpi"><div class="kpi-label">Menciona (con búsqueda)</div><div class="kpi-val" id="k-menciona"></div><div class="kpi-sub">promedio 3 asistentes</div></div>
  <div class="kpi"><div class="kpi-label">Recomendado 1º</div><div class="kpi-val" id="k-top1"></div><div class="kpi-sub">de las respuestas</div></div>
  <div class="kpi"><div class="kpi-label">Share of voice UY</div><div class="kpi-val" id="k-sov"></div><div class="kpi-sub">menciones totales UY</div></div>
</div>

<div class="section">
  <div class="section-title">Evolución semanal</div>
  <div class="chart-wrap"><svg id="chart-svg" width="100%" height="200"></svg></div>
</div>

<div class="section">
  <div class="section-title">Semana seleccionada</div>
  <div class="week-tabs" id="week-tabs"></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;flex-wrap:wrap">
    <div>
      <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);margin-bottom:12px">Ranking UY</div>
      <div id="ranking-chart"></div>
    </div>
    <div>
      <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);margin-bottom:12px">Por asistente</div>
      <div class="asist-grid" id="asist-cards"></div>
    </div>
  </div>
</div>

<footer>
  <span>Radar IA · Fixed · <span id="footer-fecha"></span></span>
  <span id="footer-config"></span>
</footer>

<script>
const SEMANAS = {data_js};
let selIdx = SEMANAS.length - 1;

const COLORES = {{ anthropic: '#cc785c', openai: '#6e7bfa', gemini: '#f0a020' }};

function fmt(v, suf='%') {{ return v == null ? '—' : v + suf; }}
function cls(v) {{ return v === 0 ? 'zero' : v >= 15 ? 'good' : v > 0 ? 'mid' : ''; }}

function renderKpis(s) {{
  document.getElementById('k-pos').innerHTML = `#${{s.pos}}<span style="font-size:16px;color:var(--muted)">/${{s.total_provs}}</span>`;
  const signo = s.brecha === 0 ? '= líder' : `−${{s.brecha}} vs ${{s.lider}}`;
  document.getElementById('k-pos-sub').innerHTML = `<strong>${{signo}}</strong>`;
  const conPcts = Object.values(s.por_asistente).map(a => (a.con_busqueda||{{}}).pct_menciona_fixed||0);
  const avg = conPcts.length ? Math.round(conPcts.reduce((a,b)=>a+b,0)/conPcts.length*10)/10 : s.menciona;
  document.getElementById('k-menciona').textContent = avg + '%';
  document.getElementById('k-top1').textContent = fmt(s.top1);
  document.getElementById('k-sov').textContent = fmt(s.sov);
  document.getElementById('footer-fecha').textContent = s.fecha;
}}

function renderRanking(s) {{
  const items = Object.entries(s.ranking);
  const maxN = items[0]?.[1] || 1;
  const total = items.reduce((a,[,n]) => a+n, 0);
  document.getElementById('ranking-chart').innerHTML = items.map(([k,n],i) => {{
    const pct = total ? (n/total*100).toFixed(1) : 0;
    const w = Math.round(n/maxN*100);
    const isF = k === 'fixed';
    return `<div class="rank-row">
      <div class="rank-num">${{i+1}}</div>
      <div class="rank-name ${{isF?'fixed':''}}">${{k.replace('_',' ')}}</div>
      <div class="rank-track"><div class="rank-fill ${{isF?'fixed':''}}" style="width:${{w}}%"></div></div>
      <div class="rank-pct ${{isF?'fixed':''}}">${{pct}}%</div>
    </div>`;
  }}).join('');
}}

function renderAsistentes(s) {{
  const provs = Object.entries(s.por_asistente);
  if (!provs.length) {{ document.getElementById('asist-cards').innerHTML = '<p style="color:var(--muted);font-size:13px">Sin datos por asistente</p>'; return; }}
  document.getElementById('asist-cards').innerHTML = provs.map(([prov, modos]) => {{
    const con = modos.con_busqueda || {{}};
    const sin = modos.sin_busqueda || {{}};
    const color = COLORES[prov] || '#888';
    const nombre = prov === 'anthropic' ? 'Claude' : prov === 'openai' ? 'ChatGPT' : 'Gemini';
    return `<div class="asist-card">
      <div class="asist-name"><span class="dot" style="background:${{color}}"></span>${{nombre}}</div>
      <div class="mode-label con">Con búsqueda</div>
      <div class="stat"><span class="stat-l">Menciona</span><span class="stat-v ${{cls(con.pct_menciona_fixed)}}">${{fmt(con.pct_menciona_fixed)}}</span></div>
      <div class="stat"><span class="stat-l">Top 1</span><span class="stat-v ${{cls(con.pct_fixed_recomendado_principal)}}">${{fmt(con.pct_fixed_recomendado_principal)}}</span></div>
      <div class="stat"><span class="stat-l">SoV UY</span><span class="stat-v ${{cls(con.share_of_voice_fixed_uy)}}">${{fmt(con.share_of_voice_fixed_uy)}}</span></div>
      <div class="mode-label sin">Sin búsqueda</div>
      <div class="stat"><span class="stat-l">Menciona</span><span class="stat-v ${{(sin.pct_menciona_fixed||0)===0?'zero':'good'}}">${{(sin.pct_menciona_fixed||0)===0?'0% — no está en memoria':fmt(sin.pct_menciona_fixed)}}</span></div>
    </div>`;
  }}).join('');
}}

function renderWeekTabs() {{
  document.getElementById('week-tabs').innerHTML = SEMANAS.map((s,i) =>
    `<button class="week-tab ${{i===selIdx?'active':''}}" onclick="selectWeek(${{i}})">${{s.fecha}}</button>`
  ).join('');
}}

function selectWeek(i) {{
  selIdx = i;
  const s = SEMANAS[i];
  renderKpis(s);
  renderRanking(s);
  renderAsistentes(s);
  renderWeekTabs();
}}

function renderChart() {{
  if (SEMANAS.length < 2) return;
  const svg = document.getElementById('chart-svg');
  const W = svg.parentElement.offsetWidth || 600;
  const H = 200;
  const PAD = {{ top:20, right:20, bottom:30, left:40 }};
  const W2 = W - PAD.left - PAD.right;
  const H2 = H - PAD.top - PAD.bottom;

  const metrics = [
    {{ key:'sov',     label:'SoV UY %',  color:'var(--fixed)',   vals: SEMANAS.map(s=>s.sov) }},
    {{ key:'menciona',label:'Menciona %', color:'var(--comp)',    vals: SEMANAS.map(s=>s.menciona) }},
    {{ key:'top1',    label:'Top 1 %',    color:'var(--warn)',    vals: SEMANAS.map(s=>s.top1) }},
  ];
  const allVals = metrics.flatMap(m=>m.vals).filter(v=>v!=null);
  const minV = 0;
  const maxV = Math.max(...allVals, 10);
  const xScale = i => PAD.left + (SEMANAS.length > 1 ? i/(SEMANAS.length-1) : 0.5) * W2;
  const yScale = v => PAD.top + H2 - ((v-minV)/(maxV-minV)) * H2;

  // grid lines
  let svgStr = `<svg width="${{W}}" height="${{H}}" viewBox="0 0 ${{W}} ${{H}}" xmlns="http://www.w3.org/2000/svg">`;
  [0,25,50,75,100].filter(v=>v<=maxV+5).forEach(v => {{
    const y = yScale(v);
    if (y >= PAD.top && y <= PAD.top+H2) {{
      svgStr += `<line x1="${{PAD.left}}" y1="${{y}}" x2="${{PAD.left+W2}}" y2="${{y}}" stroke="var(--border)" stroke-width="1"/>`;
      svgStr += `<text x="${{PAD.left-4}}" y="${{y+4}}" text-anchor="end" font-size="10" fill="var(--muted)">${{v}}</text>`;
    }}
  }});

  // x labels
  SEMANAS.forEach((s,i) => {{
    svgStr += `<text x="${{xScale(i)}}" y="${{PAD.top+H2+18}}" text-anchor="middle" font-size="10" fill="var(--muted)">${{s.fecha.slice(5)}}</text>`;
  }});

  // lines
  metrics.forEach(m => {{
    const pts = SEMANAS.map((s,i) => `${{xScale(i)}},${{yScale(m.vals[i]??0)}}`).join(' ');
    svgStr += `<polyline points="${{pts}}" fill="none" stroke="${{m.color}}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`;
    SEMANAS.forEach((s,i) => {{
      svgStr += `<circle cx="${{xScale(i)}}" cy="${{yScale(m.vals[i]??0)}}" r="4" fill="${{m.color}}" stroke="var(--surface)" stroke-width="2"/>`;
    }});
  }});

  // legend
  let lx = PAD.left;
  metrics.forEach(m => {{
    svgStr += `<circle cx="${{lx+5}}" cy="${{PAD.top-8}}" r="4" fill="${{m.color}}"/>`;
    svgStr += `<text x="${{lx+13}}" y="${{PAD.top-4}}" font-size="10" fill="var(--fg2)">${{m.label}}</text>`;
    lx += 90;
  }});

  svgStr += '</svg>';
  svg.outerHTML = svgStr;
}}

// init
selectWeek(selIdx);
renderWeekTabs();
renderChart();
window.addEventListener('resize', renderChart);
</script>
</body>
</html>"""
