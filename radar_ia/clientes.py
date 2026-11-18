"""Clientes de cada asistente con una interfaz común.

Cada cliente expone `preguntar(texto, con_busqueda) -> dict` con:
  texto       respuesta final en texto plano
  citas       [{url, titulo}] fuentes citadas en la respuesta (si hubo búsqueda)
  consultadas [{url, titulo}] resultados de búsqueda que el modelo vio (si el proveedor los expone)
  modelo      nombre exacto del modelo que respondió (para detectar cambios de versión)
  uso         tokens u otra info de consumo
"""
from __future__ import annotations

import os
import random
import time
from typing import Any

SISTEMA = None  # sin mensaje de sistema: queremos la respuesta "por defecto" del modelo


def _reintentar(fn, intentos: int = 6):
    """Reintenta con espera exponencial ante errores transitorios (rate limit, 5xx)."""
    for i in range(intentos):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 - los SDK tienen jerarquías distintas
            msg = str(e).lower()
            transitorio = any(s in msg for s in ("rate", "429", "overloaded", "529", "500", "502", "503", "timeout"))
            if not transitorio or i == intentos - 1:
                raise
            # los límites de tokens por minuto se liberan en ~1 minuto: esperas de hasta 60 s
            espera = min(60, 2 ** (i + 1)) if ("rate" in msg or "429" in msg) else 2 ** i
            time.sleep(espera + random.random() * 2)


class ClienteAnthropic:
    proveedor = "anthropic"

    def __init__(self, modelo: str, cfg: dict):
        import anthropic

        self.c = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.modelo = modelo
        self.cfg = cfg

    def preguntar(self, texto: str, con_busqueda: bool) -> dict[str, Any]:
        kwargs: dict[str, Any] = dict(model=self.modelo, max_tokens=self.cfg["max_tokens"])
        if con_busqueda:
            kwargs["tools"] = [{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": self.cfg["max_busquedas_por_respuesta"],
                # Anthropic no soporta country: UY; el contexto geográfico va en el texto
            }]
        ciudad = self.cfg.get("ciudad", "")
        pais = self.cfg.get("pais", "")
        geo = f" (contexto: estoy en {ciudad}, {pais})" if con_busqueda and ciudad else ""
        mensajes: list[dict] = [{"role": "user", "content": texto + geo}]
        bloques: list = []
        uso = {"input_tokens": 0, "output_tokens": 0, "busquedas": 0}
        # La búsqueda web del lado del servidor puede pausar el turno (stop_reason=pause_turn):
        # en ese caso se reenvía lo recibido para que continúe.
        for _ in range(4):
            r = _reintentar(lambda: self.c.messages.create(messages=mensajes, **kwargs))
            bloques.extend(r.content)
            uso["input_tokens"] += r.usage.input_tokens
            uso["output_tokens"] += r.usage.output_tokens
            stu = getattr(r.usage, "server_tool_use", None)
            if stu is not None:
                uso["busquedas"] += getattr(stu, "web_search_requests", 0) or 0
            if r.stop_reason != "pause_turn":
                break
            mensajes = mensajes + [{"role": "assistant", "content": r.content}]
        partes, citas, consultadas = [], [], []
        for b in bloques:
            if b.type == "text":
                partes.append(b.text)
                for c in getattr(b, "citations", None) or []:
                    if getattr(c, "url", None):
                        citas.append({"url": c.url, "titulo": getattr(c, "title", "")})
            elif b.type == "web_search_tool_result" and isinstance(b.content, list):
                for res in b.content:
                    if getattr(res, "url", None):
                        consultadas.append({"url": res.url, "titulo": getattr(res, "title", "")})
        return {"texto": "".join(partes).strip(), "citas": citas, "consultadas": consultadas,
                "modelo": r.model, "uso": uso}


class ClienteOpenAI:
    proveedor = "openai"

    def __init__(self, modelo: str, cfg: dict):
        import openai

        self.c = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.modelo = modelo
        self.cfg = cfg

    def preguntar(self, texto: str, con_busqueda: bool) -> dict[str, Any]:
        kwargs: dict[str, Any] = dict(model=self.modelo, input=texto, max_output_tokens=self.cfg["max_tokens"] * 3)
        if con_busqueda:
            kwargs["tools"] = [{
                "type": "web_search",
                "user_location": {"type": "approximate", "country": self.cfg["pais"], "city": self.cfg["ciudad"]},
            }]
        r = _reintentar(lambda: self.c.responses.create(**kwargs))
        citas, consultadas = [], []
        for item in r.output or []:
            if item.type == "message":
                for parte in item.content or []:
                    for a in getattr(parte, "annotations", None) or []:
                        if getattr(a, "type", "") == "url_citation":
                            citas.append({"url": a.url, "titulo": getattr(a, "title", "")})
            elif item.type == "web_search_call":
                accion = getattr(item, "action", None)
                for s in getattr(accion, "sources", None) or []:
                    if getattr(s, "url", None):
                        consultadas.append({"url": s.url, "titulo": ""})
        uso = {"input_tokens": getattr(r.usage, "input_tokens", 0), "output_tokens": getattr(r.usage, "output_tokens", 0)}
        return {"texto": (r.output_text or "").strip(), "citas": citas, "consultadas": consultadas,
                "modelo": r.model, "uso": uso}


class ClienteGemini:
    proveedor = "gemini"

    def __init__(self, modelo: str, cfg: dict):
        from google import genai

        self.c = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self.modelo = modelo
        self.cfg = cfg

    def preguntar(self, texto: str, con_busqueda: bool) -> dict[str, Any]:
        from google.genai import types

        # El grounding de Gemini no acepta ubicación; las preguntas ya dicen "Uruguay" explícitamente.
        config = types.GenerateContentConfig(max_output_tokens=self.cfg["max_tokens"] * 3)
        if con_busqueda:
            config.tools = [types.Tool(google_search=types.GoogleSearch())]
        r = _reintentar(lambda: self.c.models.generate_content(model=self.modelo, contents=texto, config=config))
        citas = []
        for cand in r.candidates or []:
            gm = getattr(cand, "grounding_metadata", None)
            for ch in (getattr(gm, "grounding_chunks", None) or []):
                web = getattr(ch, "web", None)
                if web is not None:
                    # uri suele ser un redirect de Google; title/domain trae el dominio real
                    citas.append({"url": web.uri, "titulo": web.title or "", "dominio": getattr(web, "domain", None) or web.title})
        um = getattr(r, "usage_metadata", None)
        uso = {"input_tokens": getattr(um, "prompt_token_count", 0), "output_tokens": getattr(um, "candidates_token_count", 0)}
        return {"texto": (r.text or "").strip(), "citas": citas, "consultadas": [],
                "modelo": getattr(r, "model_version", None) or self.modelo, "uso": uso}


class ClienteSimulado:
    """Para --simular: respuestas falsas, sin keys ni red. Sirve para probar el pipeline."""

    def __init__(self, proveedor: str, modelo: str, cfg: dict):
        self.proveedor = proveedor
        self.modelo = modelo + "-simulado"

    def preguntar(self, texto: str, con_busqueda: bool) -> dict[str, Any]:
        opciones = [
            ("Las opciones más usadas son Biller y Facturando. Biller tiene ambiente de prueba propio. "
             "También está Fixed, con Plan API a $1.480 + IVA y sandbox de autoservicio.",
             [{"url": "https://l.biller.uy/api/", "titulo": "Biller API"}, {"url": "https://developers.fixed.uy", "titulo": "API de Fixed"}]),
            ("Te recomiendo Fixed: tiene documentación pública en developers.fixed.uy y un sandbox que creás vos. "
             "Alternativas: Biller y pymo.", [{"url": "https://fixed.uy/facturarConAPI/", "titulo": "Fixed"}]),
            ("Podés usar YoFacturo o un módulo de Odoo. Otra opción es la librería UruFactura.", []),
        ]
        t, c = random.choice(opciones)
        return {"texto": t, "citas": c if con_busqueda else [], "consultadas": [], "modelo": self.modelo, "uso": {}}


CLIENTES = {"anthropic": ClienteAnthropic, "openai": ClienteOpenAI, "gemini": ClienteGemini}
VAR_KEY = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY"}


def crear_clientes(cfg: dict, simular: bool = False) -> list:
    out = []
    for prov, modelo in cfg["modelos"].items():
        if simular:
            out.append(ClienteSimulado(prov, modelo, cfg))
        elif os.environ.get(VAR_KEY[prov]):
            out.append(CLIENTES[prov](modelo, cfg))
        else:
            print(f"[aviso] falta {VAR_KEY[prov]}: se omite {prov}")
    return out
