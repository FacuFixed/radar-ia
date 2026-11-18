# Radar IA de Fixed

Cada lunes les hace las mismas preguntas de desarrollador a Claude, ChatGPT y Gemini, por API, y mide si mencionan y recomiendan a Fixed frente a los otros proveedores uruguayos de facturación electrónica.

Dashboard: `docs/index.html` (GitHub Pages). Contexto para Claude: `resultados/HISTORIAL.md`. Reporte de competencia: `docs/por_que_ganan.html`.

## Cómo funciona

1. **Prompts** (`preguntas.yaml`): preguntas fijas, cada una con `id` e `intencion`.
2. **Llamadas** (`radar_ia/clientes.py`): asistente × pregunta × modo × corrida. **con_busqueda** usa la búsqueda web de cada proveedor y es lo más parecido al uso real. **sin_busqueda** mide la memoria del modelo.
3. **Extracción** (`radar_ia/extraer.py`): detección por alias + juez LLM (`claude-haiku`) + consolidación.
4. **Agregación** (`radar_ia/metricas.py`): métricas por intención × modo × asistente × corrida.
5. **Publicación** (`radar_ia/historial.py`, `radar_ia/reportes.py`): `HISTORIAL.md`, dashboard y reporte "por qué ganan otros".

## Intenciones

| Intención | Qué mide | ¿Entra en los KPIs? |
|---|---|---|
| `descubrimiento` | "¿Qué proveedor/API uso?" sin nombrar a Fixed. Es la visibilidad real. | **Sí** |
| `comparacion` | Compara proveedores (con o sin nombrar a Fixed) | No, pestaña aparte |
| `tecnico` | Integraciones (WooCommerce, Odoo, n8n…) y decisiones técnicas | No, pestaña aparte |
| `precio` | Precios y planes | No, pestaña aparte |
| `marca` | Pregunta directamente por Fixed. Infla menciones. | No, pestaña aparte |

**Los KPIs principales = descubrimiento + con búsqueda, sumando los tres asistentes.** "Todas sin marca" agrega todo menos marca.

## Métricas

Todos los porcentajes llevan **intervalo de confianza de Wilson al 95%** (`ic`). Con n≈30 el margen es de ±15 puntos: dos semanas con intervalos superpuestos no son distintas con certeza. Leé promedios de 3–4 semanas.

| Métrica | Cálculo |
|---|---|
| `menciona` | respuestas que nombran a Fixed / respuestas del segmento |
| `top1` | respuestas donde el juez marca a Fixed como recomendado principal / respuestas |
| `top3` | respuestas donde Fixed aparece entre los 3 primeros proveedores mencionados / respuestas |
| `no_elige` | respuestas sin recomendado principal claro ("depende", lista sin preferencia) / respuestas |
| `puntaje_posicion` | promedio de 1/posición de Fixed (0 si no aparece) × 100. 100 = siempre primero |
| `posicion_media` | orden promedio de Fixed cuando aparece |
| `sov` (share of voice) | menciones de Fixed / menciones de todos los proveedores UY de CFE (`uy_cfe: true`) |
| `ranking` | posición de Fixed por menciones; `brecha_sov_pp` = SoV del líder − SoV de Fixed, en puntos porcentuales; `brecha_menciones` = diferencia absoluta |
| `citas.por_tipo` | dominios citados clasificados: **propio** (Fixed), **competidor** (otro `uy_cfe`), **oficial** (DGI, `*.gub.uy`), **tercero** (comparadores, blogs, foros) |
| `citas.urls_fixed` | URLs exactas de Fixed citadas (Gemini solo informa el dominio) |
| `exactitud_fixed` | afirmaciones sobre Fixed en tres categorías: **incorrecto** (contradice los datos de referencia), **correcto_no_registrado** (plausible, no está en la referencia), **no_verificable**; más **omisiones** (diferenciadores que deberían aparecer y no aparecen) |
| `fallas` | llamadas que fallaron, por asistente y modo, con causa. Se excluyen de las métricas y se reportan aparte |
| `corridas` | menciona/SoV/top1 por corrida, para ver cuánto varía una misma semana |

## Detección de marcas

En `proveedores.yaml`, cada proveedor tiene:
- `alias`: **fuertes** (dominio o contexto de marca: `fixed.uy`, "Fixed Uruguay", "Siigo Memory"). Cuentan siempre.
- `alias_debiles`: palabras comunes ("Fixed", "Memory", "Zeta"). **Solo cuentan si el juez confirma** que es la empresa, o si la respuesta cita un dominio de ese proveedor.
- `dominios`: para clasificar citas.
- `tipo` (terceros): `oficial` | `comparador` | `tercero`.

**Agregar un proveedor o alias:** sumá la entrada en `proveedores.yaml`. No hace falta tocar código. Si cambia algo que afecta semanas pasadas, reprocesalas (ver abajo).

**Datos de referencia de Fixed:** `datos_clave` (verdades), `datos_pendientes` (se tratan como no verificables) y `diferenciadores` (para omisiones), en `proveedores.yaml`.

## Agregar prompts

Sumá una entrada en `preguntas.yaml` con un `id` nuevo, `intencion` y `texto`. **Nunca edites el texto de una pregunta existente**: si cambia, cambiale el `id`, porque si no se rompe la serie.

## Comandos

```bash
python -m pytest -q
python -m radar_ia check                                   # valida keys y modelos
python -m radar_ia run --simular --limite 2 --corridas 1   # sin keys; escribe en resultados/_simulado/
python -m radar_ia run --prueba --limite 2 --corridas 1    # prueba real chica; escribe en resultados/_prueba/ (no entra en la serie)
python -m radar_ia run                                     # corrida completa (la hace el cron de los lunes)
python -m radar_ia reprocesar 2026-11-17                   # re-extrae con el juez/alias actuales sobre el crudo guardado
python -m radar_ia auditar 2026-11-17 --pct 10             # muestra aleatoria para revisar a mano
python -m radar_ia publicar                                # regenera HISTORIAL.md, dashboard y reporte
```

## Auditoría del juez

`auditar` genera `resultados/FECHA/auditoria.csv` con un 10% aleatorio de respuestas: texto completo, URLs, menciones contadas, alias débiles descartados, recomendado y lo que el juez dijo sobre Fixed. Las columnas `REVISOR_*` quedan vacías para completarlas a mano (sí/no, qué falta, qué sobra). La semilla queda en la primera línea para poder repetir la misma muestra.

## Qué se guarda (crudo)

`resultados/FECHA/respuestas.jsonl`, una línea por llamada: `ts` (fecha y hora UTC), `proveedor`, `modelo_pedido`, `modelo` (versión exacta que respondió), `modo`, `corrida`, `pregunta_id`, `intencion`, `pregunta`, `parametros`, `respuesta` (texto completo), `citas` (URLs citadas), `consultadas` (resultados de búsqueda vistos), `uso` (tokens), `latencia_s`, `error` / `error_tipo` si falló, y lo extraído: `alias`, `menciones`, `citas_por_proveedor`, `juez`, `juez_modelo`, `juez_version`.

## Reprocesar y versiones del juez

Si cambian el prompt del juez (`JUEZ_VERSION` en `extraer.py`), los alias o las intenciones, corré `reprocesar FECHA` sobre las semanas anteriores para que la serie sea comparable. No se vuelve a llamar a los asistentes: solo al juez, sobre el texto guardado. El original queda en `respuestas.original.jsonl`.

- **v2 (2026-11-18):** errores en tres categorías, omisiones, justificación del recomendado, alias fuertes/débiles, intenciones v2. La corrida 2026-11-17 se reprocesó con v2.

## Límites

La API no es idéntica a la app de consumo: no tiene memoria, personalización ni el mismo mensaje de sistema. Gemini no acepta ubicación en la búsqueda, y Anthropic la recibe en el texto. Es un indicador mucho más directo que un buscador, pero sigue siendo una aproximación.

## GitHub Actions

- Secrets: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY` (si falta una, ese asistente se omite).
- El cron corre los lunes a las 04:17 (hora de Uruguay) y commitea `resultados/` y `docs/`.
- Manual: *Actions → Radar IA semanal → Run workflow*.

## Subida a Drive

Con `drive.habilitado: true`, sube el JSON semanal y `HISTORIAL.md` (reemplazando el anterior) a `drive.carpeta_id`. Necesita los secrets `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` y `GOOGLE_OAUTH_REFRESH_TOKEN`: credenciales OAuth de usuario con scope `drive` (una cuenta de servicio no sirve). Si falla, el run sigue y solo avisa.

## Costo aproximado

23 preguntas × 3 asistentes × 2 modos × 2 corridas = 276 respuestas por semana + 276 llamadas del juez + búsquedas web.
