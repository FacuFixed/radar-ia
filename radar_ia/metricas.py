"""Agregación semanal de las respuestas en métricas comparables."""
from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean


def _grupo(filas: list[dict], proveedores: dict) -> dict:
    uy = {k for k, v in proveedores.items() if v.get("uy_cfe")}
    n = len(filas)
    if not n:
        return {"n": 0}
    menciona = [f for f in filas if any(d["clave"] == "fixed" for d in f["alias"])]
    posiciones = [d["posicion"] for f in menciona for d in f["alias"] if d["clave"] == "fixed"]
    top1 = [f for f in filas if (f.get("juez") or {}).get("recomendado_principal") == "fixed"]
    menciones_uy = Counter(d["clave"] for f in filas for d in f["alias"] if d["clave"] in uy)
    total_uy = sum(menciones_uy.values())
    citas_fixed = [f for f in filas if f["citas_por_proveedor"].get("fixed")]
    con_citas = [f for f in filas if f["citas"]]
    errores = [e for f in filas for e in ((f.get("juez") or {}).get("fixed") or {}).get("errores", [])]
    terceros = Counter(d["clave"] for f in filas for d in f["alias"] if d["clave"] not in uy)
    recomendados = Counter((f.get("juez") or {}).get("recomendado_principal") for f in filas)
    recomendados.pop(None, None)
    dominios = Counter(k.removeprefix("_otros:") if k.startswith("_otros:") else k
                       for f in filas for k, v in f["citas_por_proveedor"].items() for _ in range(v))
    return {
        "n": n,
        "pct_menciona_fixed": round(100 * len(menciona) / n, 1),
        "pct_fixed_recomendado_principal": round(100 * len(top1) / n, 1),
        "posicion_media_fixed": round(mean(posiciones), 2) if posiciones else None,
        "share_of_voice_fixed_uy": round(100 * menciones_uy["fixed"] / total_uy, 1) if total_uy else 0.0,
        "pct_cita_dominio_fixed": round(100 * len(citas_fixed) / len(con_citas), 1) if con_citas else None,
        "menciones_uy": dict(menciones_uy.most_common()),
        "recomendado_principal": dict(recomendados.most_common()),
        "menciones_terceros": dict(terceros.most_common()),
        "dominios_citados_top": dict(dominios.most_common(10)),
        "errores_sobre_fixed": errores[:20],
    }


def agregar(filas: list[dict], proveedores: dict) -> dict:
    ok = [f for f in filas if not f.get("error")]
    sin_marca = [f for f in ok if f["intencion"] != "marca"]
    marca = [f for f in ok if f["intencion"] == "marca"]
    por = defaultdict(list)
    for f in sin_marca:
        por[("modelo", f"{f['proveedor']}|{f['modo']}")].append(f)
        por[("intencion", f["intencion"])].append(f)
        por[("modo", f["modo"])].append(f)
    return {
        "general_sin_marca": _grupo(sin_marca, proveedores),
        "por_modelo_y_modo": {k: _grupo(v, proveedores) for (t, k), v in sorted(por.items()) if t == "modelo"},
        "por_intencion": {k: _grupo(v, proveedores) for (t, k), v in sorted(por.items()) if t == "intencion"},
        "por_modo": {k: _grupo(v, proveedores) for (t, k), v in sorted(por.items()) if t == "modo"},
        "preguntas_de_marca": _grupo(marca, proveedores),
        "errores_de_llamada": [{"proveedor": f["proveedor"], "pregunta": f["pregunta_id"], "error": f["error"]}
                               for f in filas if f.get("error")],
    }


def comparar(actual: dict, anterior: dict | None) -> dict | None:
    if not anterior:
        return None
    claves = ["pct_menciona_fixed", "pct_fixed_recomendado_principal", "share_of_voice_fixed_uy", "pct_cita_dominio_fixed"]
    a, b = actual["general_sin_marca"], anterior.get("metricas", {}).get("general_sin_marca", {})
    return {k: {"antes": b.get(k), "ahora": a.get(k)} for k in claves}
