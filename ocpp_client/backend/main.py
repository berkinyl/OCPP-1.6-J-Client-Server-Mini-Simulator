from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import uvicorn
import asyncio
import ssl
import threading
import os

from api.websocket import websocket_manager
from models import ConnectorStatus
from ocpp_client.backend.dependencies import set_ocpp_client_instance

app = FastAPI(title="OCPP Client Control Panel", version="1.0.0")

BASE_DIR = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

from api.routes import router  # ✅ Sonradan import
app.include_router(router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    from ocpp_client.client.main import create_ocpp_client

    instance = create_ocpp_client()
    set_ocpp_client_instance(instance)  # ✅ Set globally

    def run_ocpp_client():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(instance.start())

    thread = threading.Thread(target=run_ocpp_client)
    thread.daemon = True
    thread.start()

    await asyncio.sleep(1)

if __name__ == "__main__":
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(
        os.path.join(BASE_DIR, "cert.pem"),
        os.path.join(BASE_DIR, "key.pem")
    )

    uvicorn.run(
        "ocpp_client.backend.main:app",
        host="0.0.0.0",
        port=3000,
        ssl_keyfile=os.path.join(BASE_DIR, "key.pem"),
        ssl_certfile=os.path.join(BASE_DIR, "cert.pem"),
        reload=False
    )
