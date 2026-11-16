"""Sube el resumen semanal a la carpeta del Motor en Google Drive.

Usa credenciales OAuth de USUARIO (client id, secret y refresh token), no una cuenta de servicio:
las cuentas de servicio no tienen cuota en "Mi unidad" y fallan al crear archivos en carpetas
personales. Ver README para generar el refresh token una sola vez.
"""
from __future__ import annotations

import os
from pathlib import Path


def subir(archivo: Path, carpeta_id: str) -> str:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_OAUTH_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        # drive.file no alcanza para escribir en una carpeta que la app no creó
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    svc = build("drive", "v3", credentials=creds, cache_discovery=False)
    meta = {"name": archivo.name, "parents": [carpeta_id]}
    media = MediaFileUpload(str(archivo), mimetype="application/json")
    f = svc.files().create(body=meta, media_body=media, fields="id,webViewLink").execute()
    return f.get("webViewLink", f["id"])
