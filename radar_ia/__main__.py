"""Radar IA de Fixed: pregunta a Claude, ChatGPT y Gemini y mide si recomiendan a Fixed.

Uso:
  python -m radar_ia check                 # valida keys y nombres de modelo (1 llamada corta por proveedor)
  python -m radar_ia run                   # corrida completa
  python -m radar_ia run --limite 2 --corridas 1   # prueba barata: 2 preguntas, 1 corrida
  python -m radar_ia run --simular         # sin keys ni red, para probar el pipeline
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from .clientes import crear_clientes
from .extraer import Juez, detectar_por_alias, dominios_citados
from .historial import _cargar_semanas, generar_historial, generar_dashboard_html
from .metricas import agregar, comparar

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


def _imprimir_resumen(g: dict, metricas: dict) -> None:
    menciones = g.get("menciones_uy", {})
    total = sum(menciones.values())
    ranking = sorted(menciones.items(), key=lambda x: -x[1])
    pos_fixed = next((i + 1 for i, (k, _) in enumerate(ranking) if k == "fixed"), None)
    fixed_n = menciones.get("fixed", 0)

    print(f"\n{'─'*48}")
    print(f"  Fixed: menciona {g.get('pct_menciona_fixed')}% | "
          f"top 1: {g.get('pct_fixed_recomendado_principal')}% | "
          f"SoV UY: {g.get('share_of_voice_fixed_uy')}%")
    if pos_fixed:
        lider_n = ranking[0][1] if ranking else 0
        brecha = lider_n - fixed_n
        signo = "=" if brecha == 0 else (f"-{brecha}" if brecha > 0 else f"+{abs(brecha)}")
        print(f"  Posición en ranking UY: #{pos_fixed} de {len(ranking)}  ({fixed_n} menciones, {signo} vs líder)")

    print(f"\n  Ranking proveedores UY ({total} menciones totales):")
    for i, (k, n) in enumerate(ranking, 1):
        pct = round(100 * n / total, 1) if total else 0
        marca = " ← Fixed" if k == "fixed" else ""
        print(f"    {i:2}. {k:<20} {n:3} menciones  {pct:5.1f}%{marca}")

    rec = g.get("recomendado_principal", {})
    if rec:
        print(f"\n  Recomendado como 1º (todas las respuestas):")
        for k, n in sorted(rec.items(), key=lambda x: -x[1]):
            marca = " ← Fixed" if k == "fixed" else ""
            print(f"      {k:<20} {n:3} veces{marca}")

    por_modelo = metricas.get("por_modelo_y_modo", {})
    if por_modelo:
        print(f"\n  Desglose por asistente (menciona % | top1 % | SoV %):")
        for clave, s in sorted(por_modelo.items()):
            proveedor = clave.split("|")[0]
            print(f"    {proveedor:<12} {s.get('pct_menciona_fixed'):5.1f}%  |  "
                  f"{s.get('pct_fixed_recomendado_principal'):5.1f}%  |  "
                  f"{s.get('share_of_voice_fixed_uy'):5.1f}%")
    print(f"{'─'*48}\n")


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
    if args.simular:  # nunca mezclar resultados falsos con la serie real
        cfg = {**cfg, "carpeta_resultados": cfg["carpeta_resultados"] + "/_simulado"}
    salida = RAIZ / cfg["carpeta_resultados"] / fecha
    salida.mkdir(parents=True, exist_ok=True)

    tareas = [(c, p, m, i) for c in clientes for p in preguntas for m in modos for i in range(1, corridas + 1)]
    print(f"{len(tareas)} llamadas: {len(clientes)} asistentes x {len(preguntas)} preguntas x {len(modos)} modos x {corridas} corridas")

    def una(t):
        c, p, modo, i = t
        fila = {"fecha": fecha, "proveedor": c.proveedor, "modelo_pedido": c.modelo, "modo": modo, "corrida": i,
                "pregunta_id": p["id"], "intencion": p["intencion"], "pregunta": p["texto"]}
        try:
            r = c.preguntar(p["texto"], con_busqueda=(modo == "con_busqueda"))
            fila.update(respuesta=r["texto"], citas=r["citas"], consultadas=r["consultadas"],
                        modelo=r["modelo"], uso=r["uso"])
            fila["alias"] = detectar_por_alias(r["texto"], proveedores)
            fila["citas_por_proveedor"] = dominios_citados(r["citas"], proveedores)
            fila["juez"] = juez.evaluar(p["texto"], r["texto"]) if juez else None
        except Exception as e:  # noqa: BLE001 - se registra y se sigue con el resto
            fila["error"] = f"{type(e).__name__}: {e}"[:500]
        return fila

    filas = []
    with ThreadPoolExecutor(max_workers=cfg["concurrencia"] * len(clientes)) as ex:
        for n, f in enumerate(ex.map(una, tareas), 1):
            filas.append(f)
            if n % 20 == 0 or n == len(tareas):
                print(f"  {n}/{len(tareas)}")

    with open(salida / "respuestas.jsonl", "w", encoding="utf-8") as fh:
        for f in filas:
            fh.write(json.dumps(f, ensure_ascii=False) + "\n")

    metricas = agregar(filas, proveedores)
    previos = sorted(p for p in glob.glob(str(RAIZ / cfg["carpeta_resultados"] / "ia_llm__*.json"))
                     if not p.endswith(f"{fecha}.json"))
    anterior = json.loads(Path(previos[-1]).read_text()) if previos else None
    resumen = {
        "fecha": fecha,
        "nota": ("Respuestas obtenidas por API de cada asistente. Modo con_busqueda usa la búsqueda web del "
                 "proveedor con ubicación Uruguay (OpenAI y Anthropic; Gemini sin ubicación). La API no es idéntica "
                 "a la app de consumo (sin memoria ni personalización). Métricas generales excluyen preguntas de marca."),
        "simulado": bool(args.simular),
        "config": {"modelos": cfg["modelos"], "modos": modos, "corridas": corridas, "preguntas": len(preguntas),
                   "juez": cfg["juez"]["modelo"] if juez else None},
        "modelos_que_respondieron": sorted({f.get("modelo") for f in filas if f.get("modelo")}),
        "metricas": metricas,
        "vs_semana_anterior": comparar(metricas, anterior),
    }
    destino = RAIZ / cfg["carpeta_resultados"] / f"ia_llm__{fecha}.json"
    destino.write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
    g = metricas["general_sin_marca"]
    print(f"\nListo: {destino}")
    _imprimir_resumen(g, metricas)

    if not args.simular:
        semanas = _cargar_semanas()
        historial_md = RAIZ / "resultados" / "HISTORIAL.md"
        historial_md.write_text(generar_historial(semanas), encoding="utf-8")
        docs = RAIZ / "docs"
        docs.mkdir(exist_ok=True)
        (docs / "index.html").write_text(generar_dashboard_html(semanas), encoding="utf-8")
        print(f"  historial: {historial_md}")
        print(f"  dashboard: {docs / 'index.html'}")

    if cfg.get("drive", {}).get("habilitado") and not args.simular:
        from .drive import subir

        print("Drive:", subir(destino, cfg["drive"]["carpeta_id"]))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="radar_ia")
    ap.add_argument("comando", choices=["run", "check"])
    ap.add_argument("--simular", action="store_true", help="sin keys ni red")
    ap.add_argument("--limite", type=int, help="usar solo las primeras N preguntas")
    ap.add_argument("--corridas", type=int, help="sobrescribe corridas_por_pregunta")
    ap.add_argument("--sin-juez", action="store_true", help="no usar el juez LLM (solo alias)")
    ap.add_argument("--fecha", help="fecha a usar en los archivos (AAAA-MM-DD)")
    args = ap.parse_args(argv)
    _cargar_env()
    cfg = cargar("config.yaml")
    return cmd_check(cfg, args.simular) if args.comando == "check" else cmd_run(cfg, args)


if __name__ == "__main__":
    sys.exit(main())
