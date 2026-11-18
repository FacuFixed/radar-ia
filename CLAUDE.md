# Radar IA de Fixed: contexto para Claude Code

Fixed es el mayor proveedor de facturación electrónica de Uruguay y quiere ser la API de facturación más fácil e integral del país. Este repo mide, cada semana y por API, si Claude, ChatGPT y Gemini mencionan y recomiendan a Fixed ante preguntas de desarrolladores. Reemplaza un indicador anterior basado en resultados de un buscador de EE.UU. que no reflejaba lo que ve un usuario uruguayo.

## Estructura
- `config.yaml`: modelos, modos, corridas, juez y Drive.
- `preguntas.yaml`: preguntas fijas con `intencion` (descubrimiento | comparacion | tecnico | precio | marca). KPIs = descubrimiento con búsqueda.
- `proveedores.yaml`: alias fuertes/débiles y dominios por proveedor. `uy_cfe: true` = entra en el share of voice; `datos_clave`, `datos_pendientes` y `diferenciadores` de Fixed = referencia para el juez.
- `radar_ia/clientes.py`: un cliente por asistente con `preguntar(texto, con_busqueda)`. Búsqueda web: Anthropic `web_search_20250305` (maneja `pause_turn`), OpenAI Responses `web_search`, Gemini `google_search`.
- `radar_ia/extraer.py`: detección por alias + juez LLM (JSON, `JUEZ_VERSION`) + consolidación (alias débiles solo con confirmación).
- `radar_ia/metricas.py`: agregación por intención × modo × asistente × corrida, con IC de Wilson.
- `radar_ia/historial.py`: HISTORIAL.md + dashboard `docs/index.html`. `radar_ia/reportes.py`: por qué ganan otros + auditoría.
- README.md: definición de cada métrica.
- `.github/workflows/radar-ia.yml`: cron semanal y commit de resultados.

## Comandos
- `python -m pytest -q`
- `python -m radar_ia run --simular --limite 2 --corridas 1` (sin keys; escribe en `resultados/_simulado/`)
- `python -m radar_ia check`
- `python -m radar_ia run [--prueba] [--limite N] [--corridas N] [--sin-juez]`
- `python -m radar_ia reprocesar FECHA` / `auditar FECHA` / `publicar`

## Reglas
- Nunca commitear `.env` ni keys.
- No cambiar el texto de preguntas existentes ni el modelo del juez sin cambiar el id o dejarlo registrado: rompe la serie.
- Los resultados simulados o de prueba nunca van a `resultados/` raíz.
- Si cambia el juez, los alias o las intenciones: subir `JUEZ_VERSION` si aplica y `reprocesar` las semanas anteriores.
- Ante dudas de parámetros de las APIs, verificar contra la documentación oficial actual; los SDK cambian seguido.

## Próximos pasos pendientes
1. Correr `check` con keys reales y ajustar nombres de modelo.
2. Primera corrida real chica (`--limite 2 --corridas 1`), revisar `respuestas.jsonl` a mano y calibrar alias/juez (falsos positivos de "Fixed" como palabra en inglés).
3. Opcional: agregar Perplexity (API Sonar) como cuarto asistente.
4. Opcional: habilitar subida a Drive para que la rutina semanal lo incluya en el mail.
