"""Agregación semanal de las respuestas en métricas comparables.

Estructura de salida (ver README):
  principal   -> descubrimiento + con_busqueda, todos los asistentes: base de los KPIs
  segmentos   -> {intencion|"todas_sin_marca"}{modo}{"total", "asistentes", "corridas"}
  fallas      -> llamadas que fallaron, por asistente y modo, con causa
"""
from __future__ import annotations

from collections import Counter, defaultdict
from math import sqrt
from statistics import mean
from urllib.parse import urlparse

from .extraer import _host, errores_v1_a_v2, tipo_dominio

MODOS = ("con_busqueda", "sin_busqueda")
SEGMENTO_PRINCIPAL = "descubrimiento"


def wilson(k: int, n: int, z: float = 1.96) -> list[float] | None:
    """Intervalo de confianza de Wilson al 95%, en porcentaje."""
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * max(0.0, c - h), 1), round(100 * min(1.0, c + h), 1)]


def _pct(k: int, n: int) -> dict:
    return {"k": k, "n": n, "pct": round(100 * k / n, 1) if n else 0.0, "ic": wilson(k, n)}


def _menciones(f: dict) -> list[dict]:
    return f.get("menciones", f.get("alias", []))


def _url_limpia(c: dict) -> str:
    u = urlparse(c.get("url", ""))
    if "vertexaisearch" in u.netloc or "grounding-api-redirect" in u.path:
        return _host(c)  # Gemini devuelve redirects: solo se conoce el dominio
    return (u.netloc.removeprefix("www.") + u.path).rstrip("/")


def _grupo(filas: list[dict], proveedores: dict) -> dict:
    uy = {k for k, v in proveedores.items() if v.get("uy_cfe")}
    n = len(filas)
    if not n:
        return {"n": 0}
    pos_fixed = {}
    for i, f in enumerate(filas):
        p = next((d["posicion"] for d in _menciones(f) if d["clave"] == "fixed"), None)
        if p:
            pos_fixed[i] = p
    jueces = [f.get("juez") or {} for f in filas]
    juzgadas = [j for j in jueces if j and not j.get("_error")]  # un juez fallido no es "no elige"
    recs = [j.get("recomendado_principal") for j in juzgadas]
    menciones_uy = Counter(d["clave"] for f in filas for d in _menciones(f) if d["clave"] in uy)
    total_uy = sum(menciones_uy.values())
    ranking = menciones_uy.most_common()
    pos_rank = next((i + 1 for i, (k, _) in enumerate(ranking) if k == "fixed"), None)
    lider, lider_n = ranking[0] if ranking else (None, 0)
    sov = 100 * menciones_uy["fixed"] / total_uy if total_uy else 0.0
    sov_lider = 100 * lider_n / total_uy if total_uy else 0.0
    segundo = next(((k, c) for k, c in ranking if k != "fixed"), (None, 0))

    # Citas
    con_citas = [f for f in filas if f.get("citas")]
    tipos, dominios, urls_fixed = Counter(), Counter(), Counter()
    for f in filas:
        for c in f.get("citas") or []:
            h = _host(c)
            t = tipo_dominio(h, proveedores)
            tipos[t] += 1
            dominios[h] += 1
            if t == "propio":
                urls_fixed[_url_limpia(c)] += 1
    cita_fixed = sum(1 for f in con_citas if (f.get("citas_por_proveedor") or {}).get("fixed"))

    # Exactitud sobre Fixed
    errores = {"incorrecto": [], "correcto_no_registrado": [], "no_verificable": []}
    omisiones, tono = Counter(), Counter()
    con_fixed = 0
    for f, j in zip(filas, jueces):
        fx = j.get("fixed") or {}
        for cat, lst in errores_v1_a_v2(fx).items():
            errores.setdefault(cat, []).extend({"texto": e, "asistente": f["proveedor"], "pregunta": f.get("pregunta_id")}
                                               for e in lst or [])
        if fx.get("mencionado"):
            con_fixed += 1
            omisiones.update(fx.get("omisiones") or [])
            tono[fx.get("tono") or "no_aplica"] += 1

    return {
        "n": n,
        "menciona": _pct(len(pos_fixed), n),
        "top1": _pct(sum(1 for r in recs if r == "fixed"), len(recs)),
        "top3": _pct(sum(1 for p in pos_fixed.values() if p <= 3), n),
        "no_elige": _pct(sum(1 for r in recs if not r), len(recs)),
        "juez_fallido": n - len(juzgadas),
        "puntaje_posicion": round(100 * sum(1 / p for p in pos_fixed.values()) / n, 1),
        "posicion_media": round(mean(pos_fixed.values()), 2) if pos_fixed else None,
        "sov": {"k": menciones_uy["fixed"], "n": total_uy, "pct": round(sov, 1), "ic": wilson(menciones_uy["fixed"], total_uy)},
        "ranking": {"pos": pos_rank, "total": len(ranking), "lider": lider, "lider_menciones": lider_n,
                    "brecha_menciones": lider_n - menciones_uy["fixed"],
                    "brecha_sov_pp": round(sov_lider - sov, 1),
                    "vs_siguiente": segundo[0], "vs_siguiente_sov_pp": round(sov - (100 * segundo[1] / total_uy if total_uy else 0), 1)},
        "menciones_uy": dict(ranking),
        "recomendado_principal": dict(Counter(r for r in recs if r).most_common()),
        "menciones_terceros": dict(Counter(d["clave"] for f in filas for d in _menciones(f) if d["clave"] not in uy).most_common()),
        "citas": {"respuestas_con_citas": len(con_citas), "cita_dominio_fixed": _pct(cita_fixed, len(con_citas)),
                  "por_tipo": dict(tipos.most_common()), "dominios_top": dict(dominios.most_common(15)),
                  "urls_fixed": dict(urls_fixed.most_common())},
        "exactitud_fixed": {"respuestas_con_fixed": con_fixed,
                            "conteo": {k: len(v) for k, v in errores.items()},
                            "errores": {k: v[:25] for k, v in errores.items()},
                            "omisiones": dict(omisiones.most_common()), "tono": dict(tono)},
    }


def _fallas(filas: list[dict]) -> dict:
    por = defaultdict(lambda: {"intentos": 0, "fallas": 0, "causas": Counter()})
    for f in filas:
        k = f"{f['proveedor']}|{f['modo']}"
        por[k]["intentos"] += 1
        if f.get("error"):
            por[k]["fallas"] += 1
            por[k]["causas"][f.get("error_tipo") or f["error"].split(":")[0]] += 1
    detalle = [{"asistente": f["proveedor"], "modo": f["modo"], "pregunta": f["pregunta_id"], "corrida": f.get("corrida"),
                "error": f["error"][:300]} for f in filas if f.get("error")]
    return {"total": len(detalle), "intentos": len(filas),
            "por_asistente_modo": {k: {**v, "causas": dict(v["causas"])} for k, v in sorted(por.items())},
            "detalle": detalle}


def agregar(filas: list[dict], proveedores: dict) -> dict:
    ok = [f for f in filas if not f.get("error")]
    segs: dict[str, list] = defaultdict(list)
    for f in ok:
        segs[f["intencion"]].append(f)
        if f["intencion"] != "marca":
            segs["todas_sin_marca"].append(f)

    segmentos = {}
    for seg, fs in sorted(segs.items()):
        segmentos[seg] = {}
        for modo in MODOS:
            fm = [f for f in fs if f["modo"] == modo]
            if not fm:
                continue
            asist, corr = defaultdict(list), defaultdict(list)
            for f in fm:
                asist[f["proveedor"]].append(f)
                corr[str(f.get("corrida", 1))].append(f)
            segmentos[seg][modo] = {
                "total": _grupo(fm, proveedores),
                "asistentes": {p: _grupo(v, proveedores) for p, v in sorted(asist.items())},
                "corridas": {i: {k: _grupo(v, proveedores)[k]["pct"] for k in ("menciona", "sov", "top1")}
                             for i, v in sorted(corr.items())},
            }
    principal = (segmentos.get(SEGMENTO_PRINCIPAL) or {}).get("con_busqueda", {}).get("total", {"n": 0})
    return {
        "segmento_principal": f"{SEGMENTO_PRINCIPAL}|con_busqueda",
        "principal": principal,
        "segmentos": segmentos,
        "preguntas_por_intencion": dict(Counter(f["intencion"] for f in filas)),
        "fallas": _fallas(filas),
    }


def comparar(actual: dict, anterior: dict | None) -> dict | None:
    if not anterior or "principal" not in anterior.get("metricas", {}):
        return None
    a, b = actual["principal"], anterior["metricas"]["principal"]
    claves = ["menciona", "top1", "top3", "sov", "no_elige"]
    return {k: {"antes": (b.get(k) or {}).get("pct"), "ahora": (a.get(k) or {}).get("pct")} for k in claves}
