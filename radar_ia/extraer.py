"""Extracción de menciones de cada respuesta.

Dos capas:
  1. Detección por alias (determinística, barata, siempre corre).
  2. Juez LLM con salida JSON (orden, recomendación principal, exactitud sobre Fixed). Opcional.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from urllib.parse import urlparse


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def detectar_por_alias(texto: str, proveedores: dict) -> list[dict]:
    """Devuelve [{clave, posicion}] ordenado por primera aparición en el texto."""
    t = _norm(texto)
    encontrados = []
    for clave, p in proveedores.items():
        primera = None
        for alias in p["alias"]:
            a = _norm(alias)
            # palabra completa; para "fixed" exige que no sea parte de otra palabra
            m = re.search(r"(?<![\w.-])" + re.escape(a) + r"(?![\w-])", t)
            if m and (primera is None or m.start() < primera):
                primera = m.start()
        if primera is not None:
            encontrados.append({"clave": clave, "pos_char": primera})
    encontrados.sort(key=lambda x: x["pos_char"])
    for i, e in enumerate(encontrados, 1):
        e["posicion"] = i
    return encontrados


def dominios_citados(citas: list[dict], proveedores: dict) -> dict[str, int]:
    """Cuenta citas por proveedor según el dominio de la URL (o el dominio informado por Gemini)."""
    conteo: dict[str, int] = {}
    for c in citas:
        host = (c.get("dominio") or urlparse(c.get("url", "")).netloc or "").lower().removeprefix("www.")
        for clave, p in proveedores.items():
            if any(host == d or host.endswith("." + d) for d in p.get("dominios", [])):
                conteo[clave] = conteo.get(clave, 0) + 1
                break
        else:
            conteo["_otros:" + host] = conteo.get("_otros:" + host, 0) + 1
    return conteo


PROMPT_JUEZ = """Analizá la respuesta de un asistente de IA a una pregunta sobre facturación electrónica en Uruguay.
Devolvé SOLO un objeto JSON válido, sin texto antes ni después, con esta forma:
{{
  "proveedores_en_orden": [claves de la lista en el orden en que la respuesta los presenta; solo los que menciona],
  "recomendado_principal": clave del proveedor que la respuesta recomienda como primera opción, o null si no recomienda uno,
  "otros_no_listados": [nombres de proveedores o productos de facturación mencionados que no están en la lista],
  "fixed": {{
    "mencionado": true/false,
    "recomendado": true/false (si lo presenta como opción recomendada, no solo lo nombra),
    "tono": "positivo" | "neutro" | "negativo" | "no_aplica",
    "datos_correctos": [datos sobre Fixed en la respuesta que coinciden con los datos de referencia],
    "errores": [afirmaciones sobre Fixed que contradicen los datos de referencia o son inventadas]
  }}
}}

Lista de proveedores (clave: nombre):
{lista}

Datos de referencia sobre Fixed (verdaderos a la fecha):
{datos_fixed}

Pregunta:
{pregunta}

Respuesta del asistente:
{respuesta}
"""


class Juez:
    def __init__(self, cfg: dict, proveedores: dict, simular: bool = False):
        self.simular = simular
        self.modelo = cfg["juez"]["modelo"]
        self.proveedores = proveedores
        self.lista = "\n".join(f"- {k}: {v['nombre']}" for k, v in proveedores.items())
        self.datos_fixed = "\n".join("- " + d for d in proveedores["fixed"].get("datos_clave", []))
        if not simular:
            import anthropic

            self.c = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def evaluar(self, pregunta: str, respuesta: str) -> dict | None:
        if not respuesta:
            return None
        if self.simular:
            claves = [d["clave"] for d in detectar_por_alias(respuesta, self.proveedores)]
            return {"proveedores_en_orden": claves, "recomendado_principal": claves[0] if claves else None,
                    "otros_no_listados": [], "fixed": {"mencionado": "fixed" in claves, "recomendado": claves[:1] == ["fixed"],
                                                       "tono": "neutro", "datos_correctos": [], "errores": []}}
        from .clientes import _reintentar

        prompt = PROMPT_JUEZ.format(lista=self.lista, datos_fixed=self.datos_fixed, pregunta=pregunta, respuesta=respuesta)
        r = _reintentar(lambda: self.c.messages.create(model=self.modelo, max_tokens=1200,
                                                       messages=[{"role": "user", "content": prompt}]))
        txt = "".join(b.text for b in r.content if b.type == "text")
        m = re.search(r"\{.*\}", txt, re.S)
        try:
            return json.loads(m.group(0)) if m else None
        except json.JSONDecodeError:
            return {"_error": "json_invalido", "_crudo": txt[:2000]}
