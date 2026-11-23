# Radar IA · Fixed — Historial

Evolución semanal de la visibilidad de Fixed en Claude, ChatGPT y Gemini. Generado automáticamente.

**Cómo leerlo.** KPIs principales = preguntas de *descubrimiento* (sin nombrar a Fixed) con búsqueda web, sumando los tres asistentes. Entre paréntesis, intervalo de confianza de Wilson al 95%: dos semanas cuyos intervalos se superponen no son distintas con certeza. Mirá promedios de 3–4 semanas, no una sola.

---

## 2026-11-23

**Descubrimiento con búsqueda (n=66)** · posición **#2/11** · líder facturando · brecha 4.9 pp de SoV (11 menciones)

| Métrica | Valor (IC 95%) |
|---|---|
| Menciona a Fixed | 66.7% (54.7–76.8) |
| Fixed en top 3 | 63.6% (51.6–74.2) |
| Recomendado 1º | 20.3% (12.3–31.7) |
| No elige ninguno | 67.2% (55.0–77.4) |
| Share of voice UY | 19.6% (15.0–25.3) |
| Puntaje por posición (0–100) | 53.6 |

Por corrida: #1: menciona 72.7%, SoV 19.4% · #2: menciona 60.6%, SoV 20.0%

**Ranking con búsqueda:** 1. facturando 55 (25%) · **2. fixed 44 (20%)** · 3. biller 33 (15%) · 4. sicfe 18 (8%) · 5. pymo 16 (7%) · 6. feu 15 (7%) · 7. uruware 15 (7%) · 8. efactura_uy 11 (5%) · 9. zeta 9 (4%) · 10. zureo 5 (2%) · 11. memory 3 (1%)

**Ranking sin búsqueda (memoria del modelo), Fixed #— (no aparece):** 1. uruware 39 (22%) · 2. memory 39 (22%) · 3. biller 35 (20%) · 4. zureo 28 (16%) · 5. sicfe 25 (14%) · 6. zeta 5 (3%) · 7. factura_express 1 (1%) · 8. efactura_uy 1 (1%) · 9. facturando 1 (1%)

**Por intención (con búsqueda):**

| Intención | n | Menciona | Top 3 | Top 1 | No elige | SoV | Posición |
|---|---|---|---|---|---|---|---|
| Descubrimiento | 66 | 66.7% | 63.6% | 20.3% | 67.2% | 19.6% | #2/11 |
| Comparación | 18 | 72.2% | 72.2% | 21.4% | 57.1% | 30.2% | #1/8 |
| Técnico | 30 | 33.3% | 30.0% | 3.3% | 70.0% | 12.2% | #3/14 |
| Precio | 12 | 83.3% | 75.0% | 0.0% | 54.5% | 19.2% | #2/11 |
| Marca | 12 | 100.0% | 100.0% | 58.3% | 41.7% | 80.0% | #1/2 |
| Todas sin marca | 126 | 61.1% | 57.9% | 14.3% | 65.5% | 19.2% | #2/14 |

**Por asistente (descubrimiento):**

| Asistente | Modo | n | Menciona | Top 3 | Top 1 | SoV |
|---|---|---|---|---|---|---|
| Claude | con busqueda | 22 | 95.5% (78.2–99.2) | 95.5% | 23.8% | 23.6% |
| Gemini | con busqueda | 22 | 31.8% (16.4–52.7) | 22.7% | 4.5% | 9.0% |
| ChatGPT | con busqueda | 22 | 72.7% (51.8–86.8) | 72.7% | 33.3% | 28.1% |
| Claude | sin busqueda | 22 | 0.0% (0.0–14.9) | 0.0% | 0.0% | 0.0% |
| Gemini | sin busqueda | 22 | 0.0% (0.0–14.9) | 0.0% | 0.0% | 0.0% |
| ChatGPT | sin busqueda | 22 | 0.0% (0.0–14.9) | 0.0% | 0.0% | 0.0% |

**Fuentes citadas (todas sin marca, con búsqueda):** 119 respuestas con citas; citan un dominio de Fixed: 63.0%. Por tipo: tercero 680, competidor 364, propio 173, oficial 93

URLs de Fixed citadas: fixed.uy/facturarConAPI (82) · fixed.uy (59) · developers.fixed.uy (25) · developers.fixed.uy/referencia/ventas/crear-venta (3) · developers.fixed.uy/referencia/otros/crear-empresa-prueba (2) · developers.fixed.uy/primeros-pasos (1) · developers.fixed.uy/conceptos/ambientes (1)

**Exactitud sobre Fixed (sin marca, 75 respuestas que lo nombran):** incorrecto 16 · correcto no registrado 68 · no verificable 44
- ❌ (Claude, cat_02) La API no requiere webhooks para funcionar, sin notificaciones push de estado
- ❌ (Claude, cat_04) Cada CFE excedente cuesta $0,1 (la referencia indica $0,1 por factura excedente, pero la respuesta afirma por CFE excedente — concordancia de terminología, no contradicción de dato)
- ❌ (Claude, int_04) Fixed se presenta como servicio de sistema en el que la homologación DGI está a cargo del proveedor, pero el dominio citado es fixed.uy, no fixed.uy como dato verificado; la URL de referencia es developers.fixed.uy.
- ❌ (Claude, dev_03) El plan API incluye hasta 30.000 facturas mensuales, $0,1 por factura excedente, sandbox y homologación DGI incluida (el precio de $0,1 por factura excedente coincide, pero la respuesta no da el precio base; ver nota)
- ❌ (Gemini, pru_01) La respuesta lo presenta como 'Facture ERP / Fixed' y 'Facture (anteriormente vinculado al sistema Fixed)', afirmando un cambio de nombre que contradice que Fixed es la empresa uruguaya de facturación electrónica
- ❌ (Gemini, pre_01) Los planes con API parten desde $514 UYU / mes (con beneficio fiscal) hasta tramos de $1.200 a $1.500 UYU + IVA / mes
- ❌ (Gemini, pre_02) Precio de la API de ~$1.480 UYU / mes + IVA coincide, pero el excedente de $0.10 se presenta en UYU (dato de referencia es $0,1 sin moneda explícita)
- ❌ (Gemini, pre_02) La respuesta ubica a Fixed como de 'entorno Sandbox muy completo', lo que no contradice pero sí afirma que el sandbox valida sin afectar la operativa real
Omisiones más frecuentes: lider (74), idempotencia (62), documentacion (48), precio (36), sandbox (34), homologacion (30)

**Exactitud sobre Fixed (preguntas de marca, 12 respuestas que lo nombran):** incorrecto 2 · correcto no registrado 26 · no verificable 22
- ❌ (Gemini, mar_01) Precio con beneficio fiscal de $966 / mes, que no aparece en los datos de referencia y se presenta como precio vigente
- ❌ (Gemini, mar_01) Precio con beneficio fiscal (DGI) de $966 UYU por mes
Omisiones más frecuentes: lider (12), documentacion (10), idempotencia (10), sandbox (7), precio (4), homologacion (3)

_Config: 23 preguntas, 2 corridas, modos con_busqueda, sin_busqueda, juez claude-haiku-5-5 v2. Modelos: claude-sonnet-5-5, gemini-3.6-flash, gpt-5.5-2026-04-23._

---

## 2026-11-18

**Descubrimiento con búsqueda (n=66)** · posición **#2/11** · líder facturando · brecha 5.3 pp de SoV (12 menciones)

| Métrica | Valor (IC 95%) |
|---|---|
| Menciona a Fixed | 66.7% (54.7–76.8) |
| Fixed en top 3 | 60.6% (48.5–71.5) |
| Recomendado 1º | 15.6% (8.7–26.4) |
| No elige ninguno | 60.9% (48.7–71.9) |
| Share of voice UY | 19.6% (14.9–25.2) |
| Puntaje por posición (0–100) | 47.7 |

Por corrida: #1: menciona 60.6%, SoV 17.5% · #2: menciona 72.7%, SoV 21.6%

**Ranking con búsqueda:** 1. facturando 56 (25%) · **2. fixed 44 (20%)** · 3. biller 30 (13%) · 4. uruware 18 (8%) · 5. pymo 16 (7%) · 6. efactura_uy 16 (7%) · 7. feu 15 (7%) · 8. sicfe 12 (5%) · 9. zureo 7 (3%) · 10. memory 6 (3%) · 11. zeta 5 (2%)

**Ranking sin búsqueda (memoria del modelo), Fixed #— (no aparece):** 1. uruware 43 (28%) · 2. biller 39 (25%) · 3. memory 28 (18%) · 4. sicfe 21 (14%) · 5. zureo 15 (10%) · 6. zeta 6 (4%) · 7. efactura_uy 1 (1%) · 8. feu 1 (1%)

**Por intención (con búsqueda):**

| Intención | n | Menciona | Top 3 | Top 1 | No elige | SoV | Posición |
|---|---|---|---|---|---|---|---|
| Descubrimiento | 66 | 66.7% | 60.6% | 15.6% | 60.9% | 19.6% | #2/11 |
| Comparación | 18 | 83.3% | 77.8% | 26.7% | 60.0% | 31.9% | #1/8 |
| Técnico | 30 | 36.7% | 30.0% | 0.0% | 60.0% | 10.4% | #4/14 |
| Precio | 12 | 75.0% | 75.0% | 0.0% | 54.5% | 18.0% | #2/11 |
| Marca | 12 | 100.0% | 100.0% | 58.3% | 41.7% | 85.7% | #1/2 |
| Todas sin marca | 126 | 62.7% | 57.1% | 11.7% | 60.0% | 18.5% | #2/14 |

**Por asistente (descubrimiento):**

| Asistente | Modo | n | Menciona | Top 3 | Top 1 | SoV |
|---|---|---|---|---|---|---|
| Claude | con busqueda | 22 | 90.9% (72.2–97.5) | 86.4% | 20.0% | 22.0% |
| Gemini | con busqueda | 22 | 36.4% (19.7–57.0) | 27.3% | 0.0% | 10.3% |
| ChatGPT | con busqueda | 22 | 72.7% (51.8–86.8) | 68.2% | 27.3% | 28.6% |
| Claude | sin busqueda | 22 | 0.0% (0.0–14.9) | 0.0% | 0.0% | 0.0% |
| Gemini | sin busqueda | 22 | 0.0% (0.0–14.9) | 0.0% | 0.0% | 0.0% |
| ChatGPT | sin busqueda | 22 | 0.0% (0.0–14.9) | 0.0% | 0.0% | 0.0% |

**Fuentes citadas (todas sin marca, con búsqueda):** 119 respuestas con citas; citan un dominio de Fixed: 65.5%. Por tipo: tercero 639, competidor 418, propio 181, oficial 104

URLs de Fixed citadas: fixed.uy (75) · fixed.uy/facturarConAPI (60) · developers.fixed.uy (31) · developers.fixed.uy/referencia/ventas/crear-venta (5) · developers.fixed.uy/referencia/otros/crear-empresa-prueba (4) · developers.fixed.uy/conceptos/ambientes (2) · fixed.uy/&gsessionid=x4CjSc3otVJ5yr6JvNFq2bPj4Tni7vTSeztNynTcUqgKD0kkOA5E6w (1) · developers.fixed.uy/primeros-pasos (1) · developers.fixed.uy/conceptos/idempotencia (1) · developers.fixed.uy/referencia (1)

**Exactitud sobre Fixed (sin marca, 78 respuestas que lo nombran):** incorrecto 8 · correcto no registrado 59 · no verificable 60
- ❌ (Claude, ia_01) Plan API de $1.480 por mes sin contradicción directa; la respuesta atribuye $890/mes a Facturando, no a Fixed
- ❌ (Claude, dev_03) El plan API figura a $ 1.626/mes.
- ❌ (Gemini, cat_05) Costo adicional por factura excedente en el plan de Fixed es un dato correcto pero el resto no se contradice; no se detecta contradicción explícita
- ❌ (Gemini, pru_01) Afirma que ofrece webhooks para recibir estados de CFE, pero Fixed no tiene webhooks.
- ❌ (Gemini, pre_01) Sus planes de facturación general parten en los $514 UYU/mes
- ❌ (Gemini, pre_01) El Plan Ilimitado cuesta ~$980 UYU + IVA / mes
- ❌ (Gemini, mar_03) Fixed tiene un ambiente de pruebas fácil de migrar a producción, sin sandbox de autoservicio como dato de referencia.
- ❌ (Gemini, mar_03) Fixed está homologada por la DGI pero no se menciona homologación incluida como diferenciador (esto es omisión, no error)
Omisiones más frecuentes: lider (76), idempotencia (58), sandbox (51), precio (45), documentacion (42), homologacion (39)

**Exactitud sobre Fixed (preguntas de marca, 12 respuestas que lo nombran):** incorrecto 3 · correcto no registrado 30 · no verificable 20
- ❌ (Gemini, mar_01) Precio estándar de $1.480 UYU / mes (el dato de referencia dice $1.480 por mes + IVA, la moneda y la ausencia de IVA no coinciden)
- ❌ (Gemini, mar_01) Costo por excedente de $0,10 UYU (la referencia dice $0,1 sin especificar moneda, pero el IVA no se menciona; se contradice al omitir el + IVA)
- ❌ (Gemini, mar_01) Precio mensual estándar de $1.480 UYU / mes: el dato de referencia dice $1.480 + IVA, la respuesta omite el IVA pero el monto coincide
Omisiones más frecuentes: idempotencia (12), lider (12), documentacion (7), sandbox (6), homologacion (5), precio (4)

_Config: 23 preguntas, 2 corridas, modos con_busqueda, sin_busqueda, juez claude-haiku-5-5 v2. Modelos: claude-sonnet-5-5, gemini-3.6-flash, gpt-5.5-2026-04-23._

---

## 2026-11-17

_Reprocesada el 2026-11-18 (juez v2, alias fuertes/débiles, intenciones v2). Respuestas originales en `resultados/2026-11-17/respuestas.original.jsonl`._

**Descubrimiento con búsqueda (n=43)** · posición **#1/12** · líder fixed · brecha 0.0 pp de SoV (0 menciones)

| Métrica | Valor (IC 95%) |
|---|---|
| Menciona a Fixed | 86.0% (72.7–93.4) |
| Fixed en top 3 | 79.1% (64.8–88.6) |
| Recomendado 1º | 16.7% (8.3–30.6) |
| No elige ninguno | 59.5% (44.5–73.0) |
| Share of voice UY | 24.2% (18.1–31.5) |
| Puntaje por posición (0–100) | 59.4 |

Por corrida: #1: menciona 86.4%, SoV 23.8% · #2: menciona 85.7%, SoV 24.7%

**Ranking con búsqueda:** **1. fixed 37 (24%)** · 2. facturando 34 (22%) · 3. biller 21 (14%) · 4. pymo 13 (8%) · 5. uruware 12 (8%) · 6. feu 11 (7%) · 7. efactura_uy 7 (5%) · 8. sicfe 7 (5%) · 9. zureo 5 (3%) · 10. memory 4 (3%) · 11. zeta 1 (1%) · 12. facturalo 1 (1%)

**Ranking sin búsqueda (memoria del modelo), Fixed #— (no aparece):** 1. uruware 32 (28%) · 2. biller 31 (27%) · 3. memory 19 (17%) · 4. zureo 16 (14%) · 5. sicfe 14 (12%) · 6. zeta 1 (1%) · 7. feu 1 (1%)

**Por intención (con búsqueda):**

| Intención | n | Menciona | Top 3 | Top 1 | No elige | SoV | Posición |
|---|---|---|---|---|---|---|---|
| Descubrimiento | 43 | 86.0% | 79.1% | 16.7% | 59.5% | 24.2% | #1/12 |
| Comparación | 16 | 87.5% | 87.5% | 14.3% | 78.6% | 35.9% | #1/8 |
| Técnico | 30 | 43.3% | 40.0% | 0.0% | 62.1% | 14.1% | #2/14 |
| Precio | 11 | 81.8% | 81.8% | 0.0% | 45.5% | 16.4% | #2/10 |
| Marca | 12 | 100.0% | 100.0% | 50.0% | 50.0% | 85.7% | #1/2 |
| Todas sin marca | 100 | 73.0% | 69.0% | 9.4% | 61.5% | 21.5% | #2/14 |

**Por asistente (descubrimiento):**

| Asistente | Modo | n | Menciona | Top 3 | Top 1 | SoV |
|---|---|---|---|---|---|---|
| Claude | con busqueda | 16 | 100.0% (80.6–100.0) | 87.5% | 26.7% | 22.5% |
| Gemini | con busqueda | 16 | 87.5% (64.0–96.5) | 81.2% | 18.8% | 24.6% |
| ChatGPT | con busqueda | 11 | 63.6% (35.4–84.8) | 63.6% | 0.0% | 28.0% |
| Claude | sin busqueda | 16 | 0.0% (0.0–19.4) | 0.0% | 0.0% | 0.0% |
| Gemini | sin busqueda | 16 | 0.0% (0.0–19.4) | 0.0% | 0.0% | 0.0% |
| ChatGPT | sin busqueda | 16 | 0.0% (0.0–19.4) | 0.0% | 0.0% | 0.0% |

**Fuentes citadas (todas sin marca, con búsqueda):** 97 respuestas con citas; citan un dominio de Fixed: 71.1%. Por tipo: tercero 516, competidor 314, propio 154, oficial 54

URLs de Fixed citadas: fixed.uy (73) · fixed.uy/facturarConAPI (50) · developers.fixed.uy (26) · fixed.uy/&gsessionid=x4CjSc3otVJ5yr6JvNFq2bPj4Tni7vTSeztNynTcUqgKD0kkOA5E6w (2) · developers.fixed.uy/conceptos/ambientes (1) · developers.fixed.uy/conceptos/idempotencia (1) · developers.fixed.uy/primeros-pasos/primera-factura (1)

**Exactitud sobre Fixed (sin marca, 71 respuestas que lo nombran):** incorrecto 9 · correcto no registrado 55 · no verificable 46
- ❌ (Claude, pru_01) El plan API figura en $966/mes con beneficio fiscal
- ❌ (Claude, mar_02) El excedente se cobra sobre 30.000 facturas por mes
- ❌ (ChatGPT, mar_03) Fixed publica precio de $ 1.480/mes + IVA hasta 30.000 facturas mensuales, con excedente a $ 0,1 por factura (dato correcto en el texto de precios, no contradicho)
- ❌ (Gemini, cat_01) Sandbox 'sin costo' no contradice datos; no aplica como error
- ❌ (Gemini, cat_04) Ofrece webhooks para notificaciones de cambio de estado de comprobantes
- ❌ (Gemini, pru_03) El sandbox es idéntico a producción y lo que se prueba pasa sin cambios a live
- ❌ (Gemini, pre_02) Para 50.000 CFE/mes el costo de Fixed sería $3.480 + IVA (según la tabla de referencia, 30.000 incluidos + 20.000 extra a $0,10 da $3.480, lo cual es consistente; no contradice la referencia)
- ❌ (Gemini, mar_02) El sandbox de Fixed no impacta la operativa ni emite a DGI, lo que es consistente con el dato de referencia de ambiente de prueba, pero la respuesta no contradice nada explícitamente
Omisiones más frecuentes: lider (69), documentacion (55), precio (49), idempotencia (49), sandbox (35), homologacion (35)

**Exactitud sobre Fixed (preguntas de marca, 12 respuestas que lo nombran):** incorrecto 2 · correcto no registrado 34 · no verificable 18
- ❌ (Claude, mar_04) La respuesta indica que la activación inmediata es para clientes actuales, lo que sugiere necesitar cuenta, mientras la referencia dice que la empresa de prueba se crea con una request sin hablar con ventas
- ❌ (Gemini, mar_01) Precio con beneficio fiscal DGI de $966 aprox. para contribuyentes elegibles, no está en los datos de referencia pero contradice el precio único publicado
Omisiones más frecuentes: lider (12), idempotencia (10), documentacion (7), precio (6), sandbox (4), homologacion (4)

⚠ **Fallas:** 8/240 llamadas — openai|con_busqueda 8/40 {'RateLimitError': 8}

_Config: 20 preguntas, 2 corridas, modos con_busqueda, sin_busqueda, juez claude-haiku-5-5 v2. Modelos: claude-sonnet-5-5, gemini-3.6-flash, gpt-5.5-2026-04-23._

---
