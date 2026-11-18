# Radar IA · Fixed — Historial

Evolución semanal de la visibilidad de Fixed en Claude, ChatGPT y Gemini. Generado automáticamente.

**Cómo leerlo.** KPIs principales = preguntas de *descubrimiento* (sin nombrar a Fixed) con búsqueda web, sumando los tres asistentes. Entre paréntesis, intervalo de confianza de Wilson al 95%: dos semanas cuyos intervalos se superponen no son distintas con certeza. Mirá promedios de 3–4 semanas, no una sola.

---

## 2026-11-17

_Reprocesada el 2026-11-18 (juez v2, alias fuertes/débiles, intenciones v2). Respuestas originales en `resultados/2026-11-17/respuestas.original.jsonl`._

**Descubrimiento con búsqueda (n=43)** · posición **#1/12** · líder fixed · brecha 0.0 pp de SoV (0 menciones)

| Métrica | Valor (IC 95%) |
|---|---|
| Menciona a Fixed | 86.0% (72.7–93.4) |
| Fixed en top 3 | 79.1% (64.8–88.6) |
| Recomendado 1º | 9.3% (3.7–21.6) |
| No elige ninguno | 65.1% (50.2–77.6) |
| Share of voice UY | 24.2% (18.1–31.5) |
| Puntaje por posición (0–100) | 59.4 |

Por corrida: #1: menciona 86.4%, SoV 23.8% · #2: menciona 85.7%, SoV 24.7%

**Ranking con búsqueda:** **1. fixed 37 (24%)** · 2. facturando 34 (22%) · 3. biller 21 (14%) · 4. pymo 13 (8%) · 5. uruware 12 (8%) · 6. feu 11 (7%) · 7. efactura_uy 7 (5%) · 8. sicfe 7 (5%) · 9. zureo 5 (3%) · 10. memory 4 (3%) · 11. zeta 1 (1%) · 12. facturalo 1 (1%)

**Ranking sin búsqueda (memoria del modelo), Fixed #— (no aparece):** 1. uruware 32 (28%) · 2. biller 31 (27%) · 3. memory 20 (17%) · 4. zureo 16 (14%) · 5. sicfe 14 (12%) · 6. zeta 1 (1%) · 7. feu 1 (1%)

**Por intención (con búsqueda):**

| Intención | n | Menciona | Top 3 | Top 1 | No elige | SoV | Posición |
|---|---|---|---|---|---|---|---|
| Descubrimiento | 43 | 86.0% | 79.1% | 9.3% | 65.1% | 24.2% | #1/12 |
| Comparación | 16 | 87.5% | 87.5% | 21.4% | 71.4% | 35.9% | #1/8 |
| Técnico | 30 | 43.3% | 40.0% | 0.0% | 60.0% | 14.1% | #2/14 |
| Precio | 11 | 81.8% | 81.8% | 0.0% | 45.5% | 16.1% | #2/10 |
| Marca | 12 | 100.0% | 100.0% | 54.5% | 45.5% | 85.7% | #1/2 |
| Todas sin marca | 100 | 73.0% | 69.0% | 7.1% | 62.2% | 21.5% | #2/14 |

**Por asistente (descubrimiento):**

| Asistente | Modo | n | Menciona | Top 3 | Top 1 | SoV |
|---|---|---|---|---|---|---|
| Claude | con busqueda | 16 | 100.0% (80.6–100.0) | 87.5% | 12.5% | 22.5% |
| Gemini | con busqueda | 16 | 87.5% (64.0–96.5) | 81.2% | 12.5% | 24.6% |
| ChatGPT | con busqueda | 11 | 63.6% (35.4–84.8) | 63.6% | 0.0% | 28.0% |
| Claude | sin busqueda | 16 | 0.0% (0.0–19.4) | 0.0% | 0.0% | 0.0% |
| Gemini | sin busqueda | 16 | 0.0% (0.0–19.4) | 0.0% | 0.0% | 0.0% |
| ChatGPT | sin busqueda | 16 | 0.0% (0.0–19.4) | 0.0% | 0.0% | 0.0% |

**Fuentes citadas (todas sin marca, con búsqueda):** 97 respuestas con citas; citan un dominio de Fixed: 71.1%. Por tipo: tercero 516, competidor 314, propio 154, oficial 54

URLs de Fixed citadas: fixed.uy (73) · fixed.uy/facturarConAPI (50) · developers.fixed.uy (26) · fixed.uy/&gsessionid=x4CjSc3otVJ5yr6JvNFq2bPj4Tni7vTSeztNynTcUqgKD0kkOA5E6w (2) · developers.fixed.uy/conceptos/ambientes (1) · developers.fixed.uy/conceptos/idempotencia (1) · developers.fixed.uy/primeros-pasos/primera-factura (1)

**Exactitud sobre Fixed (sin marca, 73 respuestas que lo nombran):** incorrecto 11 · correcto no registrado 62 · no verificable 75
- ❌ (Claude, cat_01) Cobra $0,1 por CFE excedente sin mencionar precio base de $1.480
- ❌ (Claude, cat_02) No soporta webhooks.
- ❌ (Claude, cat_03) Cobra $0,1 por factura excedente en el plan API.
- ❌ (Claude, cat_03) Su API no usa webhooks.
- ❌ (Gemini, cat_05) Dice que el precio es de ~$1.480 UYU, lo cual coincide con el dato de referencia, pero la moneda se indica como UYU en lugar de $ genérico (sin contradicción relevante)
- ❌ (Gemini, cat_05) $ 0.10 por comprobante adicional, cuando el dato de referencia es $0,1 por factura excedente (coincide, por lo que no es error)
- ❌ (Gemini, pru_03) El sandbox es idéntico a producción, sin cambios al pasar a live (los datos de referencia no establecen esto; se considera no contradicho, ver no_verificable)
- ❌ (Gemini, mar_02) Fixed tiene un sandbox que no impacta la operativa ni emite a DGI, sin mencionar que se crea por autoservicio
Omisiones más frecuentes: lider (73), documentacion (56), idempotencia (48), precio (46), sandbox (38), homologacion (36)

**Exactitud sobre Fixed (preguntas de marca, 11 respuestas que lo nombran):** incorrecto 0 · correcto no registrado 27 · no verificable 21
Omisiones más frecuentes: lider (10), idempotencia (10), documentacion (6), precio (5), homologacion (3), sandbox (1)

⚠ **Fallas:** 8/240 llamadas — openai|con_busqueda 8/40 {'RateLimitError': 8}

_Config: 20 preguntas, 2 corridas, modos con_busqueda, sin_busqueda, juez claude-haiku-5-5 v2. Modelos: claude-sonnet-5-5, gemini-3.6-flash, gpt-5.5-2026-04-23._

---
