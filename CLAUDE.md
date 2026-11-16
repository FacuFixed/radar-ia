# Radar IA de Fixed: contexto para Claude Code

Fixed es el mayor proveedor de facturación electrónica de Uruguay y quiere ser la API de facturación más fácil e integral del país. Este repo mide, cada semana y por API, si Claude, ChatGPT y Gemini mencionan y recomiendan a Fixed ante preguntas de desarrolladores. Reemplaza un indicador anterior basado en resultados de un buscador de EE.UU. que no reflejaba lo que ve un usuario uruguayo.

## Estructura
- `config.yaml`: modelos, modos, corridas, juez y Drive.
- `preguntas.yaml`: 20 preguntas fijas con `intencion`. Las de `marca` nombran a Fixed y se reportan aparte.
- `proveedores.yaml`: alias y dominios por proveedor. `uy_cfe: true` = entra en el share of voice; `datos_clave` de Fixed = verdad de referencia para el juez.
- `radar_ia/clientes.py`: un cliente por asistente con `preguntar(texto, con_busqueda)`. Búsqueda web: Anthropic `web_search_20250305` (maneja `pause_turn`), OpenAI Responses `web_search`, Gemini `google_search`.
- `radar_ia/extraer.py`: detección por alias + juez LLM (JSON).
- `radar_ia/metricas.py`: agregación y comparación con la semana anterior.
- `.github/workflows/radar-ia.yml`: cron semanal y commit de resultados.

## Comandos
- `python -m pytest -q`
- `python -m radar_ia run --simular --limite 2 --corridas 1` (sin keys; escribe en `resultados/_simulado/`)
- `python -m radar_ia check`
- `python -m radar_ia run [--limite N] [--corridas N] [--sin-juez]`

## Reglas
- Nunca commitear `.env` ni keys.
- No cambiar el texto de preguntas existentes ni el modelo del juez sin cambiar el id o dejarlo registrado: rompe la serie.
- Los resultados simulados nunca van a `resultados/` raíz.
- Ante dudas de parámetros de las APIs, verificar contra la documentación oficial actual; los SDK cambian seguido.

## Próximos pasos pendientes
1. Correr `check` con keys reales y ajustar nombres de modelo.
2. Primera corrida real chica (`--limite 2 --corridas 1`), revisar `respuestas.jsonl` a mano y calibrar alias/juez (falsos positivos de "Fixed" como palabra en inglés).
3. Opcional: agregar Perplexity (API Sonar) como cuarto asistente.
4. Opcional: habilitar subida a Drive para que la rutina semanal lo incluya en el mail.
