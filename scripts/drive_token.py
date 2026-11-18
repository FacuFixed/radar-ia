"""Genera, una sola vez, el refresh token de Google Drive para el Radar.

Uso:
  pip3 install google-auth-oauthlib
  python3 scripts/drive_token.py ruta/al/client_secret.json

Abre el navegador para autorizar tu cuenta de Google y muestra los tres valores
que van como secrets en GitHub. No guarda nada en disco.
"""
import json
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

if len(sys.argv) != 2:
    sys.exit(__doc__)

flow = InstalledAppFlow.from_client_secrets_file(sys.argv[1], scopes=["https://www.googleapis.com/auth/drive"])
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
info = json.loads(creds.to_json())
print("\nCargá estos tres secrets en GitHub (Settings → Secrets and variables → Actions):\n")
print(f"GOOGLE_OAUTH_CLIENT_ID      = {info['client_id']}")
print(f"GOOGLE_OAUTH_CLIENT_SECRET  = {info['client_secret']}")
print(f"GOOGLE_OAUTH_REFRESH_TOKEN  = {info['refresh_token']}")
