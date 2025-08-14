from __future__ import annotations

import os
import asyncio
import ssl
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import uvicorn
from fastapi import HTTPException


# Backend (UI) bağımlılıkları
from ocpp_client.backend.dependencies import set_ocpp_client_instance
from ocpp_client.backend.api.routes import router as api_router
from ocpp_client.backend.api.websocket import websocket_manager

# Client tarafı
from ocpp_client.client.config import CLIENT_CONFIG, get_or_create_client_config
from ocpp_client.client.ocpp_client import OCPPClient

# Konfigürasyon & ENV override
BASE_DIR = Path(__file__).resolve().parent
CERT_FILE = BASE_DIR / "cert.pem"
KEY_FILE  = BASE_DIR / "key.pem"

# ENV'den CP_ID al ve config yükle
cp_id = os.getenv("CP_ID", "VESTEL_EVC")
if cp_id != "VESTEL_EVC":
   # CP_ID varsa özel config yükle
   client_config = get_or_create_client_config(cp_id)
   CLIENT_CONFIG.update(client_config)
else:
   CLIENT_CONFIG["charge_point_id"] = cp_id

# Server URL'yi ENV'den güncelle
CLIENT_CONFIG["server_url"] = os.getenv("SERVER_URL", CLIENT_CONFIG["server_url"])
APP_PORT = int(os.getenv("APP_PORT", "8000"))

# FastAPI Uygulaması
app = FastAPI(title="OCPP Client Control Panel", version="1.0.0")

# Statik & Şablonlar
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# CORS
app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
)

# WebSocket endpoint (UI canlı güncellemeleri için)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
   await websocket_manager.connect(websocket)
   try:
       while True:
           # İstemciden mesaj beklemiyoruz; bağlantıyı açık tutuyoruz
           await websocket.receive_text()
   except WebSocketDisconnect:
       websocket_manager.disconnect(websocket)

@app.get("/health-check")
async def health_check():
   if _ocpp_client is None:
       raise HTTPException(status_code=503, detail="Client not initialized")
   
   if not _ocpp_client.connection_accepted:
       error_msg = _ocpp_client.connection_error or "Not connected to OCPP server"
       raise HTTPException(status_code=503, detail=error_msg)
   
   return {"status": "ok", "connected": True, "cp_id": _ocpp_client.charge_point_id}

# UI Anasayfa
@app.get("/")
async def index(request: Request):
   return templates.TemplateResponse("index.html", {"request": request})

# REST API (UI'nin kullandığı uçlar)
app.include_router(api_router, prefix="/api")

# OCPP Client ömrü
# Tek instance: ENV ile verilen kimlik ve server'a bağlanır.
_ocpp_client: OCPPClient | None = None

@app.on_event("startup")
async def on_startup():
   global _ocpp_client

   # Logger (isteğe göre sade)
   logging.basicConfig(
       level=logging.INFO,
       format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
   )

   _ocpp_client = OCPPClient(
       server_url=CLIENT_CONFIG["server_url"],
       charge_point_id=CLIENT_CONFIG["charge_point_id"]
   )
   set_ocpp_client_instance(_ocpp_client)

   # Client'ı arka planda asyncio task olarak çalıştır
   asyncio.create_task(_ocpp_client.start())

   # Olası ilk çizim için ufak bekleme
   await asyncio.sleep(0.5)

@app.on_event("shutdown")
async def on_shutdown():
   # Gerekirse burada client kapatma/temizlik eklenebilir
   pass

# Uvicorn çalıştırma
if __name__ == "__main__":
   # TLS ile çalıştırıyoruz (self-signed olabilir)
   uvicorn.run(
       "ocpp_client.backend.main:app",
       host="0.0.0.0",
       port=APP_PORT,
       ssl_keyfile=str(KEY_FILE) if KEY_FILE.exists() else None,
       ssl_certfile=str(CERT_FILE) if CERT_FILE.exists() else None,
       reload=False
   )