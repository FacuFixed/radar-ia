# Radar IA de Fixed

Cada lunes les hace las mismas 20 preguntas de desarrollador a Claude, ChatGPT y Gemini, por API, y mide si mencionan y recomiendan a Fixed frente a los otros proveedores uruguayos de facturación electrónica.

## Qué mide

Cada pregunta se hace en dos modos. **con_busqueda** usa la búsqueda web de cada proveedor, con ubicación Uruguay en OpenAI y Anthropic, y es lo más parecido a cómo la gente usa hoy los asistentes. **sin_busqueda** muestra lo que el modelo "sabe" por entrenamiento. Por defecto se hacen 3 corridas por pregunta, porque las respuestas varían.

Cada respuesta pasa por dos capas de lectura. Primero, una detección por alias (`proveedores.yaml`), determinística. Después, un juez LLM barato que extrae el orden, la recomendación principal y la exactitud de lo que dice sobre Fixed, contrastado con `datos_clave`.

Métricas semanales (`resultados/ia_llm__AAAA-MM-DD.json`). Las generales excluyen las preguntas de marca, que se reportan aparte:

| Métrica | Qué es |
|---|---|
| `pct_menciona_fixed` | % de respuestas que nombran a Fixed |
| `pct_fixed_recomendado_principal` | % donde Fixed es la primera recomendación |
| `posicion_media_fixed` | orden promedio cuando aparece |
| `share_of_voice_fixed_uy` | menciones de Fixed / menciones de todos los proveedores uruguayos de CFE |
| `pct_cita_dominio_fixed` | % de respuestas con fuentes que citan fixed.uy o developers.fixed.uy |
| `errores_sobre_fixed` | afirmaciones falsas sobre Fixed (precio, sandbox, etc.) |

Todo se desglosa por modelo y modo, por intención (categoría, integración, prueba, precio, IA) y por modo. Las respuestas crudas quedan en `resultados/AAAA-MM-DD/respuestas.jsonl`.

**Límite:** la API no es idéntica a la app de consumo (no tiene memoria, personalización ni el mismo mensaje de sistema). Es un indicador mucho más directo que los resultados de un buscador, pero sigue siendo una aproximación.

## Puesta en marcha

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt pytest
cp .env.example .env        # completar las keys
python -m pytest -q
python -m radar_ia run --simular --limite 2 --corridas 1   # prueba sin keys
python -m radar_ia check                                    # valida keys y nombres de modelo
python -m radar_ia run --limite 2 --corridas 1              # primera prueba real y barata
python -m radar_ia run                                      # corrida completa
```

Si `check` falla por el nombre del modelo, cambialo en `config.yaml`. Los nombres que vienen por defecto son los que conocían los SDK al 16/11/2026 y hay que confirmarlos.

## GitHub Actions

1. Crear un repo privado y subir esta carpeta.
2. En *Settings → Secrets and variables → Actions*, cargar `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` y `GEMINI_API_KEY`. Si falta alguna, ese asistente se omite.
3. Probar a mano desde *Actions → Radar IA semanal → Run workflow* con `limite=2` y `corridas=1`.
4. El cron corre los lunes a las 04:17 (hora de Uruguay) y commitea los resultados en `resultados/`.

## Subida a Drive (opcional)

Para que la rutina semanal de Notion/Gmail lo lea de la carpeta "Radar de competencia - Motor", poné `drive.habilitado: true` en `config.yaml` y cargá estos secrets: `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` y `GOOGLE_OAUTH_REFRESH_TOKEN`.

Hay que usar credenciales OAuth de usuario (un cliente OAuth "Desktop" en Google Cloud, con el scope `https://www.googleapis.com/auth/drive` y un refresh token generado una sola vez). Una cuenta de servicio no sirve porque no tiene cuota para crear archivos en "Mi unidad".

## Costo aproximado

20 preguntas × 3 asistentes × 2 modos × 3 corridas = 360 respuestas por semana, más 360 llamadas cortas del juez. A eso se suma el costo de la búsqueda web de cada proveedor. Hacé una corrida completa y mirá el consumo en cada consola antes de dejar el cron. Para bajar costos se puede reducir `corridas_por_pregunta` a 2 o sacar el modo `sin_busqueda`.

## Reglas para no romper la serie

- No editar el texto de una pregunta existente: si cambia, cambiale el `id`.
- No cambiar el modelo del juez entre semanas.
- Cuando cambie un modelo evaluado, queda registrado en `modelos_que_respondieron`. Mencionarlo al comparar.
