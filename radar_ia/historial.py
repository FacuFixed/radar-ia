"""Genera HISTORIAL.md (contexto para Claude) y docs/index.html (dashboard) desde los JSON semanales."""
from __future__ import annotations

import glob
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

SEGMENTOS = [("descubrimiento", "Descubrimiento"), ("comparacion", "Comparación"), ("tecnico", "Técnico"),
             ("precio", "Precio"), ("marca", "Marca"), ("todas_sin_marca", "Todas sin marca")]
ASIST = {"anthropic": "Claude", "openai": "ChatGPT", "gemini": "Gemini"}


def cargar_semanas() -> list[dict]:
    """JSON semanales de la serie real, en orden cronológico (excluye simulados, pruebas y formato viejo)."""
    semanas = []
    for p in sorted(glob.glob(str(RAIZ / "resultados" / "ia_llm__*.json"))):
        try:
            d = json.loads(Path(p).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if d.get("simulado") or d.get("prueba"):
            continue
        if "segmentos" not in d.get("metricas", {}):
            print(f"[aviso] {Path(p).name} tiene formato viejo: corré `python -m radar_ia reprocesar {d.get('fecha')}`")
            continue
        semanas.append(d)
    return semanas


def _p(m: dict | None, ic: bool = True) -> str:
    if not m or m.get("pct") is None:
        return "—"
    s = f"{m['pct']}%"
    if ic and m.get("ic"):
        s += f" ({m['ic'][0]}–{m['ic'][1]})"
    return s


def _seg(s: dict, seg: str, modo: str) -> dict:
    return s["metricas"]["segmentos"].get(seg, {}).get(modo, {})


def _ranking_txt(g: dict) -> str:
    mu = g.get("menciones_uy", {})
    tot = sum(mu.values()) or 1
    return " · ".join(f"{'**' if k == 'fixed' else ''}{i}. {k} {n} ({100 * n / tot:.0f}%){'**' if k == 'fixed' else ''}"
                      for i, (k, n) in enumerate(mu.items(), 1))


def generar_historial(semanas: list[dict]) -> str:
    L = ["# Radar IA · Fixed — Historial", "",
         "Evolución semanal de la visibilidad de Fixed en Claude, ChatGPT y Gemini. Generado automáticamente.",
         "",
         "**Cómo leerlo.** KPIs principales = preguntas de *descubrimiento* (sin nombrar a Fixed) con búsqueda web, "
         "sumando los tres asistentes. Entre paréntesis, intervalo de confianza de Wilson al 95%: dos semanas cuyos "
         "intervalos se superponen no son distintas con certeza. Mirá promedios de 3–4 semanas, no una sola.",
         "", "---", ""]
    for s in reversed(semanas):
        m = s["metricas"]
        p = m["principal"]
        r = p.get("ranking", {})
        cfg = s.get("config", {})
        L += [f"## {s['fecha']}", ""]
        if s.get("reprocesado"):
            L += [f"_Reprocesada el {s['reprocesado']['fecha']} ({s['reprocesado']['motivo']}). "
                  f"Respuestas originales en `{s['reprocesado']['respaldo']}`._", ""]
        L += [f"**Descubrimiento con búsqueda (n={p.get('n', 0)})** · posición **#{r.get('pos') or '—'}/{r.get('total', 0)}** · "
              f"líder {r.get('lider')} · brecha {r.get('brecha_sov_pp')} pp de SoV ({r.get('brecha_menciones')} menciones)", "",
              "| Métrica | Valor (IC 95%) |", "|---|---|",
              f"| Menciona a Fixed | {_p(p.get('menciona'))} |",
              f"| Fixed en top 3 | {_p(p.get('top3'))} |",
              f"| Recomendado 1º | {_p(p.get('top1'))} |",
              f"| No elige ninguno | {_p(p.get('no_elige'))} |",
              f"| Share of voice UY | {_p(p.get('sov'))} |",
              f"| Puntaje por posición (0–100) | {p.get('puntaje_posicion', '—')} |", ""]
        corr = _seg(s, "descubrimiento", "con_busqueda").get("corridas", {})
        if len(corr) > 1:
            L += ["Por corrida: " + " · ".join(f"#{i}: menciona {v['menciona']}%, SoV {v['sov']}%" for i, v in corr.items()), ""]

        con, sin = _seg(s, "descubrimiento", "con_busqueda"), _seg(s, "descubrimiento", "sin_busqueda")
        if con:
            L += ["**Ranking con búsqueda:** " + _ranking_txt(con["total"]), ""]
        if sin:
            rs = sin["total"].get("ranking", {})
            L += [f"**Ranking sin búsqueda (memoria del modelo), Fixed #{rs.get('pos') or '— (no aparece)'}:** "
                  + _ranking_txt(sin["total"]), ""]

        L += ["**Por intención (con búsqueda):**", "",
              "| Intención | n | Menciona | Top 3 | Top 1 | No elige | SoV | Posición |", "|---|---|---|---|---|---|---|---|"]
        for seg, nombre in SEGMENTOS:
            g = _seg(s, seg, "con_busqueda").get("total")
            if g and g.get("n"):
                rr = g["ranking"]
                L.append(f"| {nombre} | {g['n']} | {_p(g['menciona'], False)} | {_p(g['top3'], False)} | {_p(g['top1'], False)} | "
                         f"{_p(g['no_elige'], False)} | {_p(g['sov'], False)} | #{rr['pos'] or '—'}/{rr['total']} |")
        L += ["", "**Por asistente (descubrimiento):**", "",
              "| Asistente | Modo | n | Menciona | Top 3 | Top 1 | SoV |", "|---|---|---|---|---|---|---|"]
        for modo in ("con_busqueda", "sin_busqueda"):
            for a, g in _seg(s, "descubrimiento", modo).get("asistentes", {}).items():
                L.append(f"| {ASIST.get(a, a)} | {modo.replace('_', ' ')} | {g['n']} | {_p(g['menciona'])} | "
                         f"{_p(g['top3'], False)} | {_p(g['top1'], False)} | {_p(g['sov'], False)} |")
        L.append("")

        t = _seg(s, "todas_sin_marca", "con_busqueda").get("total", {})
        c = t.get("citas", {})
        if c:
            L += [f"**Fuentes citadas (todas sin marca, con búsqueda):** {c.get('respuestas_con_citas')} respuestas con citas; "
                  f"citan un dominio de Fixed: {_p(c.get('cita_dominio_fixed'), False)}. Por tipo: "
                  + ", ".join(f"{k} {v}" for k, v in c.get("por_tipo", {}).items()), ""]
            if c.get("urls_fixed"):
                L += ["URLs de Fixed citadas: " + " · ".join(f"{u} ({n})" for u, n in c["urls_fixed"].items()), ""]

        ex = _seg(s, "todas_sin_marca", "con_busqueda").get("total", {}).get("exactitud_fixed", {})
        exm = (m["segmentos"].get("marca", {}).get("con_busqueda", {}).get("total") or {}).get("exactitud_fixed", {})
        for nombre, e in (("sin marca", ex), ("preguntas de marca", exm)):
            if e and e.get("respuestas_con_fixed"):
                cnt = e["conteo"]
                L.append(f"**Exactitud sobre Fixed ({nombre}, {e['respuestas_con_fixed']} respuestas que lo nombran):** "
                         f"incorrecto {cnt.get('incorrecto', 0)} · correcto no registrado {cnt.get('correcto_no_registrado', 0)} · "
                         f"no verificable {cnt.get('no_verificable', 0)}")
                for err in e["errores"].get("incorrecto", [])[:8]:
                    L.append(f"- ❌ ({ASIST.get(err['asistente'], err['asistente'])}, {err['pregunta']}) {err['texto']}")
                if e.get("omisiones"):
                    L.append("Omisiones más frecuentes: " + ", ".join(f"{k} ({v})" for k, v in list(e["omisiones"].items())[:6]))
                L.append("")

        f = m.get("fallas", {})
        if f.get("total"):
            L.append(f"⚠ **Fallas:** {f['total']}/{f['intentos']} llamadas — " + "; ".join(
                f"{k} {v['fallas']}/{v['intentos']} {v['causas']}" for k, v in f["por_asistente_modo"].items() if v["fallas"]))
            L.append("")
        L += [f"_Config: {cfg.get('preguntas')} preguntas, {cfg.get('corridas')} corridas, modos {', '.join(cfg.get('modos', []))}, "
              f"juez {cfg.get('juez')} v{cfg.get('juez_version')}. Modelos: {', '.join(s.get('modelos_que_respondieron', []))}._", ""]
        notas = RAIZ / "resultados" / f"notas_{s['fecha']}.md"
        if notas.exists():
            L += ["**Notas / acciones esa semana:**", notas.read_text(encoding="utf-8").strip(), ""]
        L += ["---", ""]
    return "\n".join(L)


def generar_dashboard_html(semanas: list[dict]) -> str:
    datos = [{"fecha": s["fecha"], "config": s.get("config", {}), "reprocesado": s.get("reprocesado"),
              "segmentos": s["metricas"]["segmentos"],
              "fallas": {k: v for k, v in s["metricas"].get("fallas", {}).items() if k != "detalle"}} for s in semanas]
    data_js = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
    segs_js = json.dumps(SEGMENTOS, ensure_ascii=False)
    return _PLANTILLA.replace("__DATOS__", data_js).replace("__SEGMENTOS__", segs_js)


_PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Radar IA · Fixed</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap">
<style>
:root{--bg:#0d1117;--surface:#161b22;--surface2:#1c2128;--border:#21262d;--fg:#e6edf3;--fg2:#adbac7;--muted:#768390;
--fixed:#2dd4bf;--fixed-bg:#0d2e2b;--comp:#6e7bfa;--warn:#f0a020;--danger:#e05252;--good:#3fb950;color-scheme:dark}
@media (prefers-color-scheme:light){:root:not([data-theme="dark"]){--bg:#f6f8fa;--surface:#fff;--surface2:#f0f3f6;--border:#d0d7de;
--fg:#1f2328;--fg2:#3d444d;--muted:#59636e;--fixed:#0d7a6e;--fixed-bg:#d3f5f1;--comp:#4255c4;--warn:#9a6700;--danger:#c0392b;--good:#1a7f37;color-scheme:light}}
:root[data-theme="light"]{--bg:#f6f8fa;--surface:#fff;--surface2:#f0f3f6;--border:#d0d7de;--fg:#1f2328;--fg2:#3d444d;--muted:#59636e;
--fixed:#0d7a6e;--fixed-bg:#d3f5f1;--comp:#4255c4;--warn:#9a6700;--danger:#c0392b;--good:#1a7f37;color-scheme:light}
*,*::before,*::after{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 'Inter',system-ui,sans-serif;padding:24px 16px;max-width:1200px;margin:0 auto}
h1{font-family:'Space Grotesk',sans-serif;font-size:20px;margin:0 0 4px}h1 span{color:var(--muted);font-weight:500}
a{color:var(--fixed)}
.subtitle{font-size:13px;color:var(--muted);margin-bottom:18px}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.tab{font:500 12px 'Space Grotesk',sans-serif;padding:5px 12px;border-radius:20px;border:1px solid var(--border);background:var(--surface2);color:var(--muted);cursor:pointer}
.tab:hover{color:var(--fg);border-color:var(--fixed)}.tab.active{background:var(--fixed-bg);border-color:var(--fixed);color:var(--fixed)}
.tab small{opacity:.7;margin-left:4px}
.scope{font-size:12px;color:var(--fg2);margin:14px 0 10px}.scope b{color:var(--fixed)}
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:20px}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 16px}
.kpi.featured{border-color:var(--fixed);box-shadow:inset 0 3px 0 var(--fixed)}
.kpi-label{font-size:11px;font-weight:500;color:var(--muted);letter-spacing:.5px;text-transform:uppercase;margin-bottom:6px}
.kpi-val{font:700 30px/1 'Space Grotesk',sans-serif;letter-spacing:-1px;font-variant-numeric:tabular-nums}
.kpi-val.accent{color:var(--fixed)}.kpi-val small{font-size:15px;color:var(--muted);letter-spacing:0}
.kpi-sub{font-size:11px;color:var(--muted);margin-top:6px}
.section{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:18px 20px;margin-bottom:16px}
.section-title{font:600 11px 'Space Grotesk',sans-serif;color:var(--fg2);letter-spacing:.8px;text-transform:uppercase;margin:0 0 14px}
.hint{text-transform:none;letter-spacing:0;font-weight:400;color:var(--muted);margin-left:6px;font-family:'Inter',sans-serif}
.two-col{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px}
.rank-row{display:grid;grid-template-columns:22px minmax(80px,120px) 1fr 70px;align-items:center;gap:8px;margin-bottom:6px}
.rank-num{font-size:11px;color:var(--muted);text-align:right}
.rank-name{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.rank-name.fixed{color:var(--fixed);font-weight:700}
.rank-track{height:16px;background:var(--surface2);border-radius:4px;overflow:hidden}
.rank-fill{height:100%;background:var(--comp)}.rank-fill.fixed{background:var(--fixed)}
.rank-pct{font:12px 'Space Grotesk',sans-serif;color:var(--muted);text-align:right;font-variant-numeric:tabular-nums}.rank-pct.fixed{color:var(--fixed);font-weight:600}
.asist-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.asist-card{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:14px}
.asist-name{font:600 14px 'Space Grotesk',sans-serif;display:flex;align-items:center;gap:7px;margin-bottom:6px}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block}
.stat{display:flex;justify-content:space-between;gap:8px;font-size:12px;padding:4px 0;border-bottom:1px solid var(--border)}
.stat:last-child{border-bottom:none}.stat-l{color:var(--fg2)}.stat-v{font:600 12px 'Space Grotesk',sans-serif;font-variant-numeric:tabular-nums;text-align:right}
.stat-v small{color:var(--muted);font-weight:400}
.mode-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;margin:10px 0 4px}
.mode-label.con{color:var(--fixed)}.mode-label.sin{color:var(--muted)}
.good{color:var(--good)}.mid{color:var(--warn)}.zero{color:var(--muted)}.bad{color:var(--danger)}
.tbl-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;padding:6px 8px;border-bottom:1px solid var(--border)}
td{padding:6px 8px;border-bottom:1px solid var(--border);font-variant-numeric:tabular-nums;vertical-align:top}
td.n{text-align:right}td.u{word-break:break-all}
.note{font-size:11px;color:var(--muted);margin-top:10px}.empty{color:var(--muted);font-size:13px}
ul.errs{margin:6px 0 12px;padding-left:18px;font-size:12px}ul.errs li{margin:3px 0}
.chip{display:inline-block;font-size:11px;border:1px solid var(--border);border-radius:10px;padding:1px 8px;margin:2px 4px 2px 0;color:var(--fg2)}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:11px;color:var(--fg2);margin-bottom:6px}
.legend i{display:inline-block;width:10px;height:3px;border-radius:2px;margin-right:5px;vertical-align:middle}
footer{margin-top:24px;font-size:11px;color:var(--muted);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
</style>
</head>
<body>
<h1>Radar IA <span>· Fixed</span></h1>
<div class="subtitle">Visibilidad de Fixed en Claude, ChatGPT y Gemini · actualización semanal · <a href="por_que_ganan.html">Por qué ganan otros →</a></div>

<div class="tabs" id="seg-tabs"></div>
<div class="tabs" id="week-tabs"></div>
<div class="scope" id="scope"></div>

<div class="kpi-grid" id="kpis"></div>

<div class="section">
  <div class="section-title">Evolución semanal <span class="hint">con búsqueda · mismo segmento y métricas que los KPIs</span></div>
  <div class="legend" id="legend"></div>
  <div id="chart"></div>
</div>

<div class="section">
  <div class="two-col">
    <div><div class="section-title">Ranking con búsqueda web <span class="hint">competencia real</span></div><div id="rank-con"></div></div>
    <div><div class="section-title">Ranking sin búsqueda <span class="hint">memoria del modelo</span></div><div id="rank-sin"></div></div>
  </div>
  <div class="note">Share of voice = menciones del proveedor / menciones de todos los proveedores UY, en el segmento elegido. Se listan todos los proveedores detectados.</div>
</div>

<div class="section">
  <div class="section-title">Por asistente</div>
  <div class="asist-grid" id="asist"></div>
</div>

<div class="section">
  <div class="section-title">Por intención <span class="hint">con búsqueda · todas las intenciones</span></div>
  <div class="tbl-wrap"><table id="tbl-int"></table></div>
</div>

<div class="section">
  <div class="two-col">
    <div><div class="section-title">Fuentes citadas <span class="hint">con búsqueda</span></div><div id="fuentes"></div></div>
    <div><div class="section-title">URLs de Fixed citadas</div><div id="urls-fixed"></div></div>
  </div>
</div>

<div class="section">
  <div class="section-title">Exactitud sobre Fixed <span class="hint">según datos de referencia</span></div>
  <div id="exactitud"></div>
</div>

<div class="section">
  <div class="section-title">Fallas de llamadas</div>
  <div id="fallas"></div>
</div>

<footer><span id="foot-l"></span><span id="foot-r"></span></footer>

<script>
const SEMANAS = __DATOS__;
const SEGS = __SEGMENTOS__;
const ASIST = {anthropic:['Claude','#cc785c'], openai:['ChatGPT','#6e7bfa'], gemini:['Gemini','#f0a020']};
const NOMBRES = {fixed:'Fixed',facturando:'Facturando',biller:'Biller',uruware:'Uruware',pymo:'pymo',zureo:'Zureo',memory:'Siigo Memory',
  sicfe:'Sicfe',efactura_uy:'eFactura',feu:'FEU',zeta:'Zeta Software',pfacturas:'pFacturas',facturalo:'facturalo.uy',factura_express:'Factura Express'};
let seg = 'descubrimiento', wi = SEMANAS.length - 1;

const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const nom = k => NOMBRES[k] || k;
const pct = m => m && m.pct != null ? m.pct + '%' : '—';
const ic = m => m && m.ic ? `IC95 ${m.ic[0]}–${m.ic[1]}%` : '';
const cls = v => v == null ? '' : v === 0 ? 'zero' : v >= 50 ? 'good' : 'mid';
const get = (s, sg, modo) => (((s || {}).segmentos || {})[sg] || {})[modo] || {};

function renderTabs() {
  const s = SEMANAS[wi];
  document.getElementById('seg-tabs').innerHTML = SEGS.map(([k, n]) => {
    const nn = (get(s, k, 'con_busqueda').total || {}).n;
    return `<button class="tab ${k === seg ? 'active' : ''}" data-seg="${k}">${n}${nn ? `<small>n=${nn}</small>` : ''}</button>`;
  }).join('');
  document.getElementById('week-tabs').innerHTML = SEMANAS.map((w, i) =>
    `<button class="tab ${i === wi ? 'active' : ''}" data-w="${i}">${w.fecha}</button>`).join('');
  document.querySelectorAll('[data-seg]').forEach(b => b.onclick = () => { seg = b.dataset.seg; render(); });
  document.querySelectorAll('[data-w]').forEach(b => b.onclick = () => { wi = +b.dataset.w; render(); });
}

function renderKpis(s) {
  const g = get(s, seg, 'con_busqueda').total || {};
  const segNom = (SEGS.find(x => x[0] === seg) || [, seg])[1];
  document.getElementById('scope').innerHTML = `KPIs: <b>con búsqueda web</b> · segmento <b>${esc(segNom)}</b>${seg === 'descubrimiento' ? ' (sin marca)' : ''} · ${g.n || 0} respuestas de los 3 asistentes`;
  if (!g.n) { document.getElementById('kpis').innerHTML = '<p class="empty">Sin datos para este segmento.</p>'; return; }
  const r = g.ranking || {};
  const brecha = r.lider === 'fixed'
    ? `líder · +${r.vs_siguiente_sov_pp} pp de SoV vs ${esc(nom(r.vs_siguiente))}`
    : `−${r.brecha_sov_pp} pp de SoV vs ${esc(nom(r.lider))} (${r.brecha_menciones} menciones menos)`;
  const k = (lab, val, sub, feat) => `<div class="kpi ${feat ? 'featured' : ''}"><div class="kpi-label">${lab}</div><div class="kpi-val ${feat ? 'accent' : ''}">${val}</div><div class="kpi-sub">${sub}</div></div>`;
  document.getElementById('kpis').innerHTML =
    k('Posición (con búsqueda)', `#${r.pos ?? '—'}<small>/${r.total}</small>`, brecha, true) +
    k('Menciona a Fixed', pct(g.menciona), ic(g.menciona)) +
    k('Fixed en top 3', pct(g.top3), ic(g.top3)) +
    k('Recomendado 1º', pct(g.top1), ic(g.top1)) +
    k('No elige ninguno', pct(g.no_elige), ic(g.no_elige) + ' · sin recomendado claro') +
    k('Share of voice UY', pct(g.sov), ic(g.sov)) +
    k('Puntaje por posición', g.puntaje_posicion ?? '—', '100 = siempre 1º · 0 = nunca aparece');
}

function rankHtml(g) {
  const items = Object.entries((g || {}).menciones_uy || {});
  if (!items.length) return '<p class="empty">Sin datos</p>';
  const tot = items.reduce((a, [, n]) => a + n, 0), max = items[0][1];
  const fx = items.some(([k]) => k === 'fixed');
  return (fx ? '' : '<p class="note" style="margin:0 0 8px">Fixed: 0 menciones</p>') + items.map(([k, n], i) => {
    const f = k === 'fixed' ? 'fixed' : '';
    return `<div class="rank-row"><div class="rank-num">${i + 1}</div><div class="rank-name ${f}">${esc(nom(k))}</div>
      <div class="rank-track"><div class="rank-fill ${f}" style="width:${Math.round(n / max * 100)}%"></div></div>
      <div class="rank-pct ${f}">${n} · ${(n / tot * 100).toFixed(1)}%</div></div>`;
  }).join('');
}

function renderRankings(s) {
  document.getElementById('rank-con').innerHTML = rankHtml(get(s, seg, 'con_busqueda').total);
  document.getElementById('rank-sin').innerHTML = rankHtml(get(s, seg, 'sin_busqueda').total);
}

function renderAsist(s) {
  const con = get(s, seg, 'con_busqueda').asistentes || {}, sin = get(s, seg, 'sin_busqueda').asistentes || {};
  const provs = [...new Set([...Object.keys(con), ...Object.keys(sin)])];
  const st = (l, m, extra) => `<div class="stat"><span class="stat-l">${l}</span><span class="stat-v ${cls(m && m.pct)}">${pct(m)}${extra ? ` <small>${extra}</small>` : ''}</span></div>`;
  document.getElementById('asist').innerHTML = provs.length ? provs.map(p => {
    const c = con[p] || {}, w = sin[p] || {};
    const [n, col] = ASIST[p] || [p, '#888'];
    return `<div class="asist-card"><div class="asist-name"><span class="dot" style="background:${col}"></span>${n}</div>
      <div class="mode-label con">Con búsqueda · n=${c.n || 0}</div>
      ${st('Menciona', c.menciona, c.menciona && c.menciona.ic ? `${c.menciona.ic[0]}–${c.menciona.ic[1]}` : '')}
      ${st('Top 3', c.top3)}${st('Recomendado 1º', c.top1)}${st('No elige', c.no_elige)}${st('SoV UY', c.sov)}
      <div class="mode-label sin">Sin búsqueda · n=${w.n || 0}</div>
      ${st('Menciona', w.menciona)}${st('SoV UY', w.sov)}</div>`;
  }).join('') : '<p class="empty">Sin datos</p>';
}

function renderIntencion(s) {
  const rows = SEGS.map(([k, n]) => [k, n, get(s, k, 'con_busqueda').total]).filter(x => x[2] && x[2].n);
  document.getElementById('tbl-int').innerHTML = '<tr><th>Intención</th><th>n</th><th>Menciona</th><th>Top 3</th><th>Top 1</th><th>No elige</th><th>SoV</th><th>Posición</th></tr>' +
    rows.map(([k, n, g]) => `<tr style="${k === seg ? 'background:var(--fixed-bg)' : ''}"><td>${n}</td><td class="n">${g.n}</td>
      <td class="n ${cls(g.menciona.pct)}">${pct(g.menciona)}</td><td class="n">${pct(g.top3)}</td><td class="n">${pct(g.top1)}</td>
      <td class="n">${pct(g.no_elige)}</td><td class="n">${pct(g.sov)}</td><td class="n">#${g.ranking.pos ?? '—'}/${g.ranking.total}</td></tr>`).join('') +
    '<tr><td colspan="8" class="note">Marca y comparación nombran a Fixed en la pregunta: inflan las menciones, por eso los KPIs usan descubrimiento.</td></tr>';
}

function renderFuentes(s) {
  const c = (get(s, seg, 'con_busqueda').total || {}).citas;
  if (!c) { document.getElementById('fuentes').innerHTML = document.getElementById('urls-fixed').innerHTML = '<p class="empty">Sin datos</p>'; return; }
  const tipos = Object.entries(c.por_tipo || {}), tot = tipos.reduce((a, [, n]) => a + n, 0) || 1;
  const nombreTipo = {propio: 'Propio (Fixed)', competidor: 'Competidor', oficial: 'Oficial (DGI, gub.uy)', tercero: 'Comparador / tercero'};
  document.getElementById('fuentes').innerHTML =
    `<p class="note" style="margin-top:0">${c.respuestas_con_citas} respuestas con citas · ${pct(c.cita_dominio_fixed)} citan un dominio de Fixed</p>` +
    tipos.map(([k, n]) => `<div class="rank-row"><div class="rank-num"></div><div class="rank-name ${k === 'propio' ? 'fixed' : ''}">${esc(nombreTipo[k] || k)}</div>
      <div class="rank-track"><div class="rank-fill ${k === 'propio' ? 'fixed' : ''}" style="width:${Math.round(n / tot * 100)}%"></div></div><div class="rank-pct">${n}</div></div>`).join('') +
    '<div class="section-title" style="margin-top:16px">Dominios más citados</div><table>' +
    Object.entries(c.dominios_top || {}).slice(0, 10).map(([d, n]) => `<tr><td class="u">${esc(d)}</td><td class="n">${n}</td></tr>`).join('') + '</table>';
  const u = Object.entries(c.urls_fixed || {});
  document.getElementById('urls-fixed').innerHTML = u.length
    ? '<table>' + u.map(([x, n]) => `<tr><td class="u">${esc(x)}</td><td class="n">${n}</td></tr>`).join('') + '</table><p class="note">Gemini solo informa el dominio, no la URL exacta.</p>'
    : '<p class="empty">Ninguna respuesta citó una URL de Fixed en este segmento.</p>';
}

function renderExactitud(s) {
  const bloques = [['Este segmento', (get(s, seg, 'con_busqueda').total || {}).exactitud_fixed],
                   ['Preguntas de marca', (get(s, 'marca', 'con_busqueda').total || {}).exactitud_fixed]];
  const cat = [['incorrecto', 'Incorrecto', 'bad'], ['correcto_no_registrado', 'Correcto pero no registrado', 'good'], ['no_verificable', 'No verificable', 'mid']];
  document.getElementById('exactitud').innerHTML = '<div class="two-col">' + bloques.map(([t, e]) => {
    if (!e || !e.respuestas_con_fixed) return `<div><b>${t}</b><p class="empty">Ninguna respuesta nombra a Fixed.</p></div>`;
    return `<div><b>${t}</b> <span class="note">${e.respuestas_con_fixed} respuestas nombran a Fixed</span>` +
      cat.map(([k, n, c]) => {
        const l = (e.errores || {})[k] || [];
        return `<div class="stat"><span class="stat-l">${n}</span><span class="stat-v ${c}">${(e.conteo || {})[k] || 0}</span></div>` +
          (l.length ? '<ul class="errs">' + l.slice(0, 6).map(x => `<li>${esc(x.texto)} <span class="note">· ${esc((ASIST[x.asistente] || [x.asistente])[0])}, ${esc(x.pregunta)}</span></li>`).join('') + '</ul>' : '');
      }).join('') +
      (Object.keys(e.omisiones || {}).length ? '<div class="section-title" style="margin-top:14px">Omisiones (diferenciadores que faltan)</div>' +
        Object.entries(e.omisiones).map(([k, n]) => `<span class="chip">${esc(k)} · ${n}</span>`).join('') : '') + '</div>';
  }).join('') + '</div>';
}

function renderFallas(s) {
  const f = s.fallas || {};
  const rows = Object.entries(f.por_asistente_modo || {});
  document.getElementById('fallas').innerHTML = `<p class="note" style="margin-top:0">${f.total || 0} de ${f.intentos || 0} llamadas fallaron (se excluyen de las métricas).</p>` +
    '<table><tr><th>Asistente</th><th>Modo</th><th>Intentos</th><th>Fallas</th><th>Causa</th></tr>' +
    rows.map(([k, v]) => { const [p, m] = k.split('|'); return `<tr><td>${esc((ASIST[p] || [p])[0])}</td><td>${esc(m.replace('_', ' '))}</td>
      <td class="n">${v.intentos}</td><td class="n ${v.fallas ? 'bad' : 'zero'}">${v.fallas}</td><td>${esc(Object.entries(v.causas || {}).map(([c, n]) => c + ' ×' + n).join(', ') || '—')}</td></tr>`; }).join('') + '</table>';
}

function renderChart() {
  const el = document.getElementById('chart');
  const series = [['menciona', 'Menciona %', 'var(--fixed)'], ['top3', 'Top 3 %', 'var(--comp)'], ['sov', 'SoV UY %', 'var(--warn)'], ['top1', 'Recomendado 1º %', 'var(--danger)']];
  document.getElementById('legend').innerHTML = series.map(([, l, c]) => `<span><i style="background:${c}"></i>${l}</span>`).join('');
  const W = Math.max(el.offsetWidth || 600, 280), H = 210, P = {t: 12, r: 16, b: 26, l: 34}, w = W - P.l - P.r, h = H - P.t - P.b;
  const val = (s, k) => ((get(s, seg, 'con_busqueda').total || {})[k] || {}).pct;
  const x = i => P.l + (SEMANAS.length > 1 ? i / (SEMANAS.length - 1) : .5) * w, y = v => P.t + h - v / 100 * h;
  let svg = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="Evolución semanal">`;
  [0, 25, 50, 75, 100].forEach(v => svg += `<line x1="${P.l}" x2="${P.l + w}" y1="${y(v)}" y2="${y(v)}" stroke="var(--border)"/><text x="${P.l - 6}" y="${y(v) + 4}" text-anchor="end" font-size="10" fill="var(--muted)">${v}</text>`);
  SEMANAS.forEach((s, i) => svg += `<text x="${x(i)}" y="${H - 6}" text-anchor="middle" font-size="10" fill="${i === wi ? 'var(--fg)' : 'var(--muted)'}">${s.fecha.slice(5)}</text>`);
  series.forEach(([k, l, c]) => {
    const pts = SEMANAS.map((s, i) => [i, val(s, k)]).filter(p => p[1] != null);
    if (pts.length > 1) svg += `<polyline points="${pts.map(([i, v]) => x(i) + ',' + y(v)).join(' ')}" fill="none" stroke="${c}" stroke-width="2" stroke-linejoin="round"/>`;
    pts.forEach(([i, v]) => svg += `<circle cx="${x(i)}" cy="${y(v)}" r="4" fill="${c}" stroke="var(--surface)" stroke-width="2"><title>${l}: ${v}%</title></circle>`);
  });
  el.innerHTML = svg + '</svg>' + (SEMANAS.length < 2 ? '<p class="note">Con una sola semana no hay tendencia todavía. Leé promedios de 3–4 semanas: cambios dentro del IC son ruido.</p>' : '');
}

function render() {
  const s = SEMANAS[wi];
  if (!s) { document.body.insertAdjacentHTML('beforeend', '<p class="empty">Sin semanas cargadas.</p>'); return; }
  renderTabs(); renderKpis(s); renderChart(); renderRankings(s); renderAsist(s); renderIntencion(s);
  renderFuentes(s); renderExactitud(s); renderFallas(s);
  const c = s.config || {};
  document.getElementById('foot-l').textContent = `Radar IA · Fixed · ${s.fecha}${s.reprocesado ? ' · reprocesada ' + s.reprocesado.fecha : ''}`;
  document.getElementById('foot-r').textContent = `${c.preguntas} preguntas · ${c.corridas} corridas · juez ${c.juez} v${c.juez_version}`;
}
render();
window.addEventListener('resize', renderChart);
</script>
</body>
</html>"""
