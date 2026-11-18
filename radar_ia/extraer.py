"""Extracción de menciones de cada respuesta.

Tres capas:
  1. Detección por alias (determinística): alias fuertes (dominio o contexto de marca) y débiles (palabra común).
  2. Juez LLM con salida JSON: orden, recomendado principal, justificación, exactitud y omisiones sobre Fixed.
  3. `consolidar_menciones`: un alias fuerte cuenta solo; uno débil solo si el juez lo confirma
     o si la respuesta cita un dominio de ese proveedor.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from urllib.parse import urlparse

JUEZ_VERSION = 2


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _buscar(t: str, alias: str) -> int | None:
    m = re.search(r"(?<![\w.-])" + re.escape(_norm(alias)) + r"(?![\w-])", t)
    return m.start() if m else None


def detectar_por_alias(texto: str, proveedores: dict) -> list[dict]:
    """Devuelve [{clave, pos_char, posicion, fuerte}] ordenado por primera aparición en el texto."""
    t = _norm(texto)
    encontrados = []
    for clave, p in proveedores.items():
        primera, fuerte = None, False
        for alias, es_fuerte in [(a, True) for a in p.get("alias", [])] + [(a, False) for a in p.get("alias_debiles", [])]:
            pos = _buscar(t, alias)
            if pos is not None:
                fuerte = fuerte or es_fuerte
                if primera is None or pos < primera:
                    primera = pos
        if primera is not None:
            encontrados.append({"clave": clave, "pos_char": primera, "fuerte": fuerte})
    encontrados.sort(key=lambda x: x["pos_char"])
    for i, e in enumerate(encontrados, 1):
        e["posicion"] = i
    return encontrados


def _host(c: dict) -> str:
    return (c.get("dominio") or urlparse(c.get("url", "")).netloc or "").lower().removeprefix("www.")


def proveedor_de_host(host: str, proveedores: dict) -> str | None:
    for clave, p in proveedores.items():
        if any(host == d or host.endswith("." + d) for d in p.get("dominios", [])):
            return clave
    return None


def dominios_citados(citas: list[dict], proveedores: dict) -> dict[str, int]:
    """Cuenta citas por proveedor según el dominio de la URL (o el dominio informado por Gemini)."""
    conteo: dict[str, int] = {}
    for c in citas:
        host = _host(c)
        k = proveedor_de_host(host, proveedores) or "_otros:" + host
        conteo[k] = conteo.get(k, 0) + 1
    return conteo


def tipo_dominio(host: str, proveedores: dict) -> str:
    """propio | competidor | oficial | tercero (comparadores, blogs, foros, etc.)."""
    k = proveedor_de_host(host, proveedores)
    if k:
        p = proveedores[k]
        if p.get("propio"):
            return "propio"
        if p.get("uy_cfe"):
            return "competidor"
        return p.get("tipo", "tercero")
    if host.endswith("gub.uy"):
        return "oficial"
    return "tercero"


def consolidar_menciones(alias: list[dict], juez: dict | None, citas_por_proveedor: dict) -> list[dict]:
    """Menciones válidas: fuertes siempre; débiles solo con confirmación del juez o dominio citado."""
    confirmados = set((juez or {}).get("proveedores_en_orden") or [])
    if ((juez or {}).get("fixed") or {}).get("mencionado"):
        confirmados.add("fixed")
    out = [dict(d) for d in alias if d.get("fuerte", True) or d["clave"] in confirmados or citas_por_proveedor.get(d["clave"])]
    for i, d in enumerate(out, 1):
        d["posicion"] = i
    return out


PROMPT_JUEZ = """Analizá la respuesta de un asistente de IA a una pregunta sobre facturación electrónica en Uruguay.
Devolvé SOLO un objeto JSON válido, sin texto antes ni después, con esta forma:
{{
  "proveedores_en_orden": [claves de la lista en el orden en que la respuesta los presenta; solo los que menciona como empresa/producto. Ojo: "fixed", "memory" o "zeta" usados como palabra común (ej. "precio fixed", "memory leak") NO cuentan],
  "recomendado_principal": clave del proveedor que la respuesta recomienda claramente como primera opción, o null si no elige uno (lista opciones sin preferir, dice "depende", etc.),
  "justificacion_recomendado": fragmento textual (copiado literal, máx. 300 caracteres) donde la respuesta justifica al recomendado principal, o null,
  "otros_no_listados": [nombres de proveedores o productos de facturación mencionados que no están en la lista],
  "fixed": {{
    "mencionado": true/false (Fixed, la empresa uruguaya de facturación electrónica),
    "recomendado": true/false (si lo presenta como opción recomendada, no solo lo nombra),
    "tono": "positivo" | "neutro" | "negativo" | "no_aplica",
    "datos_correctos": [afirmaciones sobre Fixed que coinciden con los datos de referencia],
    "errores": {{
      "incorrecto": [afirmaciones sobre Fixed que CONTRADICEN los datos de referencia],
      "correcto_no_registrado": [afirmaciones sobre Fixed que no están en los datos de referencia pero son plausibles y consistentes con ellos],
      "no_verificable": [afirmaciones sobre Fixed que no se pueden confirmar ni descartar con los datos de referencia, o que tocan datos pendientes]
    }},
    "omisiones": [ids (solo el id, ej. "precio") de los diferenciadores que NO aparecen en la respuesta; solo si Fixed fue mencionado, si no lista vacía]
  }}
}}

Reglas para clasificar afirmaciones sobre Fixed:
- "incorrecto" SOLO si la afirmación contradice explícitamente un dato de referencia (ej. otro precio, "no tiene sandbox").
- Cualquier afirmación sobre un dato pendiente (ej. webhooks, a favor o en contra) va en "no_verificable", nunca en "incorrecto".
- Lo que la respuesta NO dice (precio omitido, homologación no mencionada) es una omisión: va en "omisiones", nunca en "errores".
- Una afirmación que coincide con un dato de referencia va en "datos_correctos", no en "errores".
- Cada afirmación va en una sola categoría. Escribí cada una en una frase corta, sin explicar tu razonamiento.

Lista de proveedores (clave: nombre):
{lista}

Datos de referencia sobre Fixed (verdaderos a la fecha):
{datos_fixed}

Datos pendientes de confirmar (tratar como no_verificable):
{pendientes}

Diferenciadores de Fixed (para detectar omisiones):
{diferenciadores}

Pregunta:
{pregunta}

Respuesta del asistente:
{respuesta}
"""


def errores_v1_a_v2(fixed: dict) -> dict:
    """Normaliza el formato viejo (errores = lista) al nuevo (tres categorías)."""
    e = fixed.get("errores")
    if isinstance(e, list):
        return {"incorrecto": [], "correcto_no_registrado": [], "no_verificable": e}
    return e or {"incorrecto": [], "correcto_no_registrado": [], "no_verificable": []}


class Juez:
    def __init__(self, cfg: dict, proveedores: dict, simular: bool = False):
        self.simular = simular
        self.modelo = cfg["juez"]["modelo"]
        self.version = JUEZ_VERSION
        self.proveedores = proveedores
        f = proveedores["fixed"]
        self.lista = "\n".join(f"- {k}: {v['nombre']}" for k, v in proveedores.items())
        self.datos_fixed = "\n".join("- " + d for d in f.get("datos_clave", []))
        self.pendientes = "\n".join("- " + d for d in f.get("datos_pendientes", [])) or "- (ninguno)"
        self.ids_dif = set(f.get("diferenciadores", {}))
        self.diferenciadores = "\n".join(f"- {k}: {v}" for k, v in f.get("diferenciadores", {}).items())
        if not simular:
            import anthropic

            self.c = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def evaluar(self, pregunta: str, respuesta: str) -> dict | None:
        if not respuesta:
            return None
        if self.simular:
            claves = [d["clave"] for d in detectar_por_alias(respuesta, self.proveedores)]
            return {"proveedores_en_orden": claves, "recomendado_principal": claves[0] if claves else None,
                    "justificacion_recomendado": respuesta[:120] if claves else None, "otros_no_listados": [],
                    "fixed": {"mencionado": "fixed" in claves, "recomendado": claves[:1] == ["fixed"], "tono": "neutro",
                              "datos_correctos": [], "omisiones": ["idempotencia"] if "fixed" in claves else [],
                              "errores": {"incorrecto": [], "correcto_no_registrado": [], "no_verificable": []}}}
        from .clientes import _reintentar

        prompt = PROMPT_JUEZ.format(lista=self.lista, datos_fixed=self.datos_fixed, pendientes=self.pendientes,
                                    diferenciadores=self.diferenciadores, pregunta=pregunta, respuesta=respuesta)
        # Haiku 5.5 razona por defecto y puede gastar todo max_tokens pensando sin emitir el JSON.
        r = _reintentar(lambda: self.c.messages.create(model=self.modelo, max_tokens=4000,
                                                       thinking={"type": "disabled"}, output_config={"effort": "low"},
                                                       messages=[{"role": "user", "content": prompt}]))
        txt = "".join(b.text for b in r.content if b.type == "text")
        m = re.search(r"\{.*\}", txt, re.S)
        try:
            out = json.loads(m.group(0)) if m else {"_error": "sin_json", "_crudo": txt[:2000]}
        except json.JSONDecodeError:
            return {"_error": "json_invalido", "_crudo": txt[:2000]}
        fx = out.get("fixed")
        if isinstance(fx, dict):
            fx["omisiones"] = [o for o in fx.get("omisiones") or [] if o in self.ids_dif]
        return out


def procesar_fila(fila: dict, proveedores: dict, juez: Juez | None) -> dict:
    """Extracción completa sobre una fila con `respuesta` y `citas`. Sirve para corridas nuevas y para reprocesar."""
    fila["alias"] = detectar_por_alias(fila["respuesta"], proveedores)
    fila["citas_por_proveedor"] = dominios_citados(fila["citas"], proveedores)
    if juez:
        fila["juez"] = juez.evaluar(fila["pregunta"], fila["respuesta"])
        fila["juez_modelo"], fila["juez_version"] = juez.modelo, juez.version
    # Sin juez, los alias débiles solo cuentan si hay dominio citado.
    fila["menciones"] = consolidar_menciones(fila["alias"], fila.get("juez") if juez else None,
                                             fila["citas_por_proveedor"])
    return fila
