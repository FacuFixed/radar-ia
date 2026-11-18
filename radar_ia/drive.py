"""Sube el resumen semanal a la carpeta del Motor en Google Drive.

Usa credenciales OAuth de USUARIO (client id, secret y refresh token), no una cuenta de servicio:
las cuentas de servicio no tienen cuota en "Mi unidad" y fallan al crear archivos en carpetas
personales. Ver README para generar el refresh token una sola vez.
"""
from __future__ import annotations

import os
from pathlib import Path


def _get_service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_OAUTH_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _upsert(svc, nombre: str, carpeta_id: str, archivo: Path, mimetype: str) -> str:
    """Sube el archivo; si ya existe uno con ese nombre en la carpeta, lo reemplaza."""
    from googleapiclient.http import MediaFileUpload

    res = svc.files().list(
        q=f"name='{nombre}' and '{carpeta_id}' in parents and trashed=false",
        fields="files(id)",
        pageSize=1,
    ).execute()
    existentes = res.get("files", [])
    media = MediaFileUpload(str(archivo), mimetype=mimetype)
    if existentes:
        f = svc.files().update(
            fileId=existentes[0]["id"], media_body=media, fields="id,webViewLink"
        ).execute()
    else:
        meta = {"name": nombre, "parents": [carpeta_id]}
        f = svc.files().create(body=meta, media_body=media, fields="id,webViewLink").execute()
    return f.get("webViewLink", f["id"])


def subir(archivo: Path, carpeta_id: str) -> str:
    svc = _get_service()
    return _upsert(svc, archivo.name, carpeta_id, archivo, "application/json")


def subir_historial(historial: Path, carpeta_id: str) -> str:
    svc = _get_service()
    return _upsert(svc, historial.name, carpeta_id, historial, "text/markdown")
