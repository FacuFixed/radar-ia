"""Radar IA de Fixed: pregunta a Claude, ChatGPT y Gemini y mide si recomiendan a Fixed.

Uso:
  python -m radar_ia check                          # valida keys y nombres de modelo
  python -m radar_ia run                            # corrida completa (entra en la serie histórica)
  python -m radar_ia run --prueba --limite 2 --corridas 1   # prueba chica: escribe en resultados/_prueba/
  python -m radar_ia run --simular                  # sin keys ni red, para probar el pipeline
  python -m radar_ia reprocesar 2026-11-17          # re-extrae (juez actual) sobre el crudo guardado, sin llamar a los asistentes
  python -m radar_ia auditar 2026-11-17 [--pct 10]  # exporta una muestra aleatoria para revisar a mano
  python -m radar_ia publicar                       # regenera HISTORIAL.md y el dashboard desde los JSON
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from .clientes import crear_clientes
from .extraer import Juez, procesar_fila
from .historial import cargar_semanas, generar_dashboard_html, generar_historial
from .metricas import agregar, comparar
from .reportes import exportar_auditoria, por_que_ganan_html, por_que_ganan_md

RAIZ = Path(__file__).resolve().parent.parent


def cargar(nombre: str):
    return yaml.safe_load((RAIZ / nombre).read_text(encoding="utf-8"))


def _cargar_env():
    p = RAIZ / ".env"
    if p.exists():
        for linea in p.read_text().splitlines():
            if "=" in linea and not linea.startswith("#"):
                k, v = linea.split("=", 1)
                if v.strip():
                    os.environ.setdefault(k.strip(), v.strip())


def cmd_check(cfg, simular):
    ok = True
    for c in crear_clientes(cfg, simular):
        try:
            r = c.preguntar("Respondé solo: ok", con_busqueda=False)
            print(f"[ok] {c.proveedor}: modelo {r['modelo']} -> {r['texto'][:40]!r}")
        except Exception as e:  # noqa: BLE001
            ok = False
            print(f"[ERROR] {c.proveedor} ({c.modelo}): {e}")
    return 0 if ok else 1


def _parametros(cfg: dict, proveedor: str, con_busqueda: bool) -> dict:
    p = {"max_tokens": cfg["max_tokens"] * (1 if proveedor == "anthropic" else 3), "temperatura": "default",
         "busqueda_web": con_busqueda}
    if con_busqueda:
        p["ubicacion"] = {"anthropic": "en el texto", "openai": "user_location", "gemini": "no soportada"}.get(proveedor)
        p["ciudad"], p["pais"] = cfg.get("ciudad"), cfg.get("pais")
        if proveedor == "anthropic":
            p["max_busquedas"] = cfg["max_busquedas_por_respuesta"]
    return p


def _imprimir_resumen(m: dict) -> None:
    p = m["principal"]
    if not p.get("n"):
        print("  (sin respuestas de descubrimiento con búsqueda)")
        return
    r = p["ranking"]
    print(f"\n{'─' * 60}\n  KPIs · descubrimiento con búsqueda (n={p['n']})")
    for k, nombre in (("menciona", "Menciona a Fixed"), ("top3", "Fixed en top 3"), ("top1", "Recomendado 1º"),
                      ("no_elige", "No elige ninguno"), ("sov", "Share of voice UY")):
        ic = p[k]["ic"]
        print(f"    {nombre:<20} {p[k]['pct']:5.1f}%   IC95 {ic[0]}–{ic[1]}%" if ic else f"    {nombre:<20} —")
    print(f"    Posición: #{r['pos']}/{r['total']}  (líder {r['lider']}, brecha {r['brecha_sov_pp']} pp de SoV)")
    f = m["fallas"]
    print(f"  Fallas: {f['total']}/{f['intentos']} llamadas")
    for k, v in f["por_asistente_modo"].items():
        if v["fallas"]:
            print(f"    {k}: {v['fallas']}/{v['intentos']} {v['causas']}")
    print(f"{'─' * 60}\n")


def armar_resumen(fecha: str, filas: list[dict], cfg: dict, proveedores: dict, extra: dict) -> dict:
    metricas = agregar(filas, proveedores)
    previos = sorted(p for p in glob.glob(str(RAIZ / "resultados" / "ia_llm__*.json")) if not p.endswith(f"{fecha}.json")
                     and p < str(RAIZ / "resultados" / f"ia_llm__{fecha}.json"))
    anterior = json.loads(Path(previos[-1]).read_text()) if previos else None
    return {
        "fecha": fecha,
        "nota": ("Respuestas obtenidas por API de cada asistente. KPIs principales = preguntas de descubrimiento "
                 "(sin marca) con búsqueda web. La API no es idéntica a la app de consumo (sin memoria ni personalización)."),
        **extra,
        "modelos_que_respondieron": sorted({f.get("modelo") for f in filas if f.get("modelo")}),
        "metricas": metricas,
        "vs_semana_anterior": comparar(metricas, anterior),
    }


def publicar(cfg: dict) -> Path:
    """Regenera HISTORIAL.md, el dashboard y el reporte 'por qué ganan otros' de la última semana."""
    semanas = cargar_semanas()
    historial_md = RAIZ / "resultados" / "HISTORIAL.md"
    historial_md.write_text(generar_historial(semanas), encoding="utf-8")
    docs = RAIZ / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.html").write_text(generar_dashboard_html(semanas), encoding="utf-8")
    if semanas:
        fecha = semanas[-1]["fecha"]
        filas = _leer_filas(RAIZ / "resultados" / fecha / "respuestas.jsonl")
        (docs / "por_que_ganan.html").write_text(por_que_ganan_html(filas, fecha), encoding="utf-8")
        (RAIZ / "resultados" / fecha / "por_que_ganan.md").write_text(por_que_ganan_md(filas, fecha), encoding="utf-8")
    print(f"  historial: {historial_md}\n  dashboard: {docs / 'index.html'}\n  reporte:   {docs / 'por_que_ganan.html'}")
    return historial_md


def _leer_filas(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _escribir_filas(p: Path, filas: list[dict]) -> None:
    with open(p, "w", encoding="utf-8") as fh:
        for f in filas:
            fh.write(json.dumps(f, ensure_ascii=False) + "\n")


def cmd_run(cfg, args):
    proveedores = cargar("proveedores.yaml")
    preguntas = cargar("preguntas.yaml")[: args.limite or None]
    corridas = args.corridas or cfg["corridas_por_pregunta"]
    modos = cfg["modos"]
    clientes = crear_clientes(cfg, args.simular)
    if not clientes:
        print("No hay ningún proveedor con API key. Cargá al menos una en .env o en los secrets.")
        return 1
    juez = None if args.sin_juez else Juez(cfg, proveedores, args.simular)
    fecha = args.fecha or dt.date.today().isoformat()
    base = "resultados"
    if args.simular:  # nunca mezclar resultados falsos o de prueba con la serie real
        base = "resultados/_simulado"
    elif args.prueba:
        base = "resultados/_prueba"
    salida = RAIZ / base / fecha
    salida.mkdir(parents=True, exist_ok=True)

    tareas = [(c, p, m, i) for c in clientes for p in preguntas for m in modos for i in range(1, corridas + 1)]
    print(f"{len(tareas)} llamadas: {len(clientes)} asistentes x {len(preguntas)} preguntas x {len(modos)} modos x {corridas} corridas")
    conc = cfg.get("concurrencia_por_proveedor") or {}
    sem = {c.proveedor: threading.Semaphore(conc.get(c.proveedor, cfg["concurrencia"])) for c in clientes}

    def una(t):
        c, p, modo, i = t
        con_b = modo == "con_busqueda"
        fila = {"fecha": fecha, "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "proveedor": c.proveedor, "modelo_pedido": c.modelo, "modo": modo, "corrida": i,
                "pregunta_id": p["id"], "intencion": p["intencion"], "pregunta": p["texto"],
                "parametros": _parametros(cfg, c.proveedor, con_b)}
        with sem[c.proveedor]:
            t0 = time.monotonic()
            try:
                r = c.preguntar(p["texto"], con_busqueda=con_b)
                fila.update(respuesta=r["texto"], citas=r["citas"], consultadas=r["consultadas"],
                            modelo=r["modelo"], uso=r["uso"], latencia_s=round(time.monotonic() - t0, 1))
            except Exception as e:  # noqa: BLE001 - se registra y se sigue con el resto
                fila.update(error=f"{type(e).__name__}: {e}"[:500], error_tipo=type(e).__name__,
                            latencia_s=round(time.monotonic() - t0, 1))
                return fila
        try:
            procesar_fila(fila, proveedores, juez)
        except Exception as e:  # noqa: BLE001 - la respuesta queda guardada aunque falle el juez
            fila["error_extraccion"] = f"{type(e).__name__}: {e}"[:300]
        return fila

    filas = []
    workers = sum(conc.get(c.proveedor, cfg["concurrencia"]) for c in clientes)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for n, f in enumerate(ex.map(una, tareas), 1):
            filas.append(f)
            if n % 20 == 0 or n == len(tareas):
                print(f"  {n}/{len(tareas)}")

    fallidas = [i for i, f in enumerate(filas) if f.get("error")]
    if fallidas and cfg.get("reintentar_fallas") and not args.simular:
        print(f"  reintentando {len(fallidas)} llamadas fallidas (secuencial)...")
        for i in fallidas:
            nueva = una(tareas[i])
            nueva["reintento"] = True
            if not nueva.get("error"):
                nueva["error_previo"] = filas[i]["error"]
            filas[i] = nueva

    _escribir_filas(salida / "respuestas.jsonl", filas)
    extra = {"simulado": bool(args.simular), "prueba": bool(args.prueba),
             "config": {"modelos": cfg["modelos"], "modos": modos, "corridas": corridas, "preguntas": len(preguntas),
                        "juez": cfg["juez"]["modelo"] if juez else None, "juez_version": juez.version if juez else None}}
    resumen = armar_resumen(fecha, filas, cfg, proveedores, extra)
    destino = RAIZ / base / f"ia_llm__{fecha}.json"
    destino.write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nListo: {destino}")
    _imprimir_resumen(resumen["metricas"])

    if args.simular or args.prueba:
        (salida / "por_que_ganan.md").write_text(por_que_ganan_md(filas, fecha), encoding="utf-8")
        return 0
    historial_md = publicar(cfg)
    if cfg.get("drive", {}).get("habilitado"):
        from .drive import subir, subir_historial

        carpeta = cfg["drive"]["carpeta_id"]
        try:  # una falla de Drive no puede impedir que el workflow commitee los resultados
            print("Drive JSON:", subir(destino, carpeta))
            print("Drive historial:", subir_historial(historial_md, carpeta))
        except Exception as e:  # noqa: BLE001
            print(f"[aviso] no se pudo subir a Drive ({type(e).__name__}: {e}). Revisá los secrets GOOGLE_OAUTH_*.")
    return 0


def cmd_reprocesar(cfg, args):
    """Re-extrae una corrida con el juez y los alias actuales, sobre el texto crudo guardado."""
    proveedores = cargar("proveedores.yaml")
    intencion = {p["id"]: p["intencion"] for p in cargar("preguntas.yaml")}
    carpeta = RAIZ / "resultados" / args.fecha_objetivo
    origen = carpeta / "respuestas.jsonl"
    respaldo = carpeta / "respuestas.original.jsonl"
    if not respaldo.exists():
        shutil.copy(origen, respaldo)
    filas = _leer_filas(respaldo)
    juez = None if args.sin_juez else Juez(cfg, proveedores, args.simular)

    def una(f):
        f = dict(f)
        f["intencion_original"] = f.get("intencion_original", f["intencion"])
        f["intencion"] = intencion.get(f["pregunta_id"], f["intencion"])
        if f.get("error"):
            f.setdefault("error_tipo", f["error"].split(":")[0])
            return f
        return procesar_fila(f, proveedores, juez)

    with ThreadPoolExecutor(max_workers=8) as ex:
        nuevas = list(ex.map(una, filas))
    _escribir_filas(origen, nuevas)

    viejo = json.loads((RAIZ / "resultados" / f"ia_llm__{args.fecha_objetivo}.json").read_text(encoding="utf-8"))
    cfg_viejo = viejo.get("config", {})
    extra = {"simulado": False, "prueba": False,
             "config": {**cfg_viejo, "juez": juez.modelo if juez else None, "juez_version": juez.version if juez else None},
             "reprocesado": {"fecha": dt.date.today().isoformat(), "motivo": "juez v2, alias fuertes/débiles, intenciones v2",
                             "respaldo": str(respaldo.relative_to(RAIZ))}}
    resumen = armar_resumen(args.fecha_objetivo, nuevas, cfg, proveedores, extra)
    destino = RAIZ / "resultados" / f"ia_llm__{args.fecha_objetivo}.json"
    destino.write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Reprocesado: {destino}")
    _imprimir_resumen(resumen["metricas"])
    publicar(cfg)
    return 0


def cmd_auditar(cfg, args):
    carpeta = RAIZ / "resultados" / args.fecha_objetivo
    filas = _leer_filas(carpeta / "respuestas.jsonl")
    p = exportar_auditoria(filas, carpeta / "auditoria.csv", args.pct, args.semilla)
    print(f"Muestra para revisar a mano: {p}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="radar_ia")
    ap.add_argument("comando", choices=["run", "check", "reprocesar", "auditar", "publicar"])
    ap.add_argument("fecha_objetivo", nargs="?", help="para reprocesar/auditar: fecha de la corrida (AAAA-MM-DD)")
    ap.add_argument("--simular", action="store_true", help="sin keys ni red")
    ap.add_argument("--prueba", action="store_true", help="corrida de prueba: no entra en la serie ni en el dashboard")
    ap.add_argument("--limite", type=int, help="usar solo las primeras N preguntas")
    ap.add_argument("--corridas", type=int, help="sobrescribe corridas_por_pregunta")
    ap.add_argument("--sin-juez", action="store_true", help="no usar el juez LLM (solo alias)")
    ap.add_argument("--fecha", help="fecha a usar en los archivos (AAAA-MM-DD)")
    ap.add_argument("--pct", type=float, default=10, help="auditar: porcentaje de respuestas a muestrear")
    ap.add_argument("--semilla", type=int, help="auditar: semilla para repetir la misma muestra")
    args = ap.parse_args(argv)
    _cargar_env()
    cfg = cargar("config.yaml")
    if args.comando in ("reprocesar", "auditar") and not args.fecha_objetivo:
        ap.error(f"{args.comando} necesita la fecha de la corrida")
    return {"check": lambda: cmd_check(cfg, args.simular), "run": lambda: cmd_run(cfg, args),
            "reprocesar": lambda: cmd_reprocesar(cfg, args), "auditar": lambda: cmd_auditar(cfg, args),
            "publicar": lambda: (publicar(cfg), 0)[1]}[args.comando]()


if __name__ == "__main__":
    sys.exit(main())
