#   uvicorn sim_manager.app:app --port 9000
from __future__ import annotations

import os
import sys
import socket
import logging
from pathlib import Path
from subprocess import Popen
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel, Field, model_validator

from .process_store import store, ClientProcess

# ------------------------------------------------------------
# Genel ayar
# ------------------------------------------------------------
logger = logging.getLogger("SimManager")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(title="Sim-Manager (Clients Only)", version="1.1")

# UI statik/şablon
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ------------------------------------------------------------
# Yardımcılar
# ------------------------------------------------------------
def _client_entry_module(ui: bool) -> list[str]:
    # UI'li client'ı paket olarak çalıştır (import sorunlarını çözmek için -m kullanıyoruz)
    if ui:
        return [sys.executable, "-m", "ocpp_client.backend.main"]
    else:
        return [sys.executable, "-m", "ocpp_client.run_client"]  # headless kullanırsan ekleyebilirsin

def _client_scheme() -> str:
    """
    Sertifikalar varsa https, yoksa http döndür.
    """
    cert = ROOT_DIR / "ocpp_client" / "backend" / "cert.pem"
    key  = ROOT_DIR / "ocpp_client" / "backend" / "key.pem"
    return "https" if cert.exists() and key.exists() else "http"

def _port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex((host, port)) == 0

def _next_free_port(start_from: int) -> int:
    p = start_from
    while _port_in_use(p):
        p += 1
    return p

def _is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def _ui_url(port: int, cp_id: str) -> str:
    """
    Client UI linkinde CP_ID görünsün diye query param ekler.
    İstersen bu fonksiyonu path formatına çevirebilirsin.
    """
    scheme = _client_scheme()
    return f"{scheme}://localhost:{port}/?cp_id={cp_id}"

# ------------------------------------------------------------
# Modeller
# ------------------------------------------------------------
class SpawnReq(BaseModel):
    # 1) prefix + count ile üretim
    prefix: Optional[str] = Field(None, max_length=64, description="Örn: CP-IZMIR")
    count: Optional[int]  = Field(None, ge=1, le=200)
    start_index: int      = Field(1, ge=1)

    # 2) veya doğrudan id listesi
    ids: Optional[List[str]] = Field(None, description='["CP-A", "CP-B"] gibi')

    # Ortak ayarlar
    city: Optional[str] = Field(None, max_length=64)
    server_url: str     = Field("wss://localhost:8080", description="OCPP server adresi (wss:// veya ws://)")
    base_port: int      = Field(8101, description="İlk UI portu (otomatik artar)")
    ui: bool            = Field(True, description="True: UI'li client")

    @model_validator(mode="after")
    def _validate_source(self) -> "SpawnReq":
        if self.ids and (self.prefix or self.count):
            raise ValueError("ids ile prefix/count birlikte verilemez.")
        if not self.ids and not (self.prefix and self.count):
            raise ValueError("Ya ids verin ya da prefix + count verin.")
        return self

class SpawnResult(BaseModel):
    cp_id: str
    pid: int
    ui: Optional[str] = None
    city: Optional[str] = None

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
@app.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
def health():
    # Ayakta ve kaç client var bilgisi
    alive = 0
    for meta in list(store.clients.values()):
        if _is_alive(meta.pid):
            alive += 1
        else:
            # ölmüşse temizle
            del store.clients[meta.cp_id]
    return {"ok": True, "clients": alive, "scheme": _client_scheme(), "base_port": store.base_port}

# ------------------------------------------------------------
# API: Clients
# ------------------------------------------------------------
@app.get("/clients")
def list_clients():
    scheme = _client_scheme()
    out = []
    for cp_id, meta in list(store.clients.items()):
        if not _is_alive(meta.pid):
            del store.clients[cp_id]
            continue
        out.append({
            "cp_id": cp_id,
            "pid": meta.pid,
            "ui": _ui_url(meta.port, cp_id), 
            "city": meta.city
        })
    return out

@app.post("/clients/kill/{cp_id}")
def kill_client(cp_id: str):
    meta = store.clients.get(cp_id)
    if not meta:
        raise HTTPException(404, "Client not found")
    store.kill_pid(meta.pid)
    del store.clients[cp_id]
    return {"status": "killed", "cp_id": cp_id}

@app.post("/clients/kill-all")
def kill_all():
    count = 0
    for cp_id, meta in list(store.clients.items()):
        store.kill_pid(meta.pid)
        del store.clients[cp_id]
        count += 1
    return {"status": "killed", "count": count}

@app.post("/clients/spawn")
def spawn_clients(req: SpawnReq):
    """
    Örnek 1 (prefix + count):
    {
      "prefix": "CP-IZMIR",
      "count": 3,
      "start_index": 1,
      "city": "Izmir",
      "server_url": "wss://localhost:8080",
      "base_port": 8101,
      "ui": true
    }

    Örnek 2 (ids):
    {
      "ids": ["CP-AYDIN-001", "CP-AYDIN-002"],
      "city": "Aydin",
      "server_url": "wss://localhost:8080",
      "base_port": 8120,
      "ui": true
    }
    """
    # Port sayacını çağrıdan gelen base_port'a çek
    store.set_base_port(req.base_port)

    # log klasörleri
    logs = ROOT_DIR / "logs" / "clients"
    logs.mkdir(parents=True, exist_ok=True)

    scheme = _client_scheme()
    env_template = os.environ.copy()

    # Üretilecek kimliklerin listesini çıkar
    if req.ids:
        ids = req.ids
    else:
        ids = [f"{req.prefix}-{i:03d}" for i in range(req.start_index, req.start_index + (req.count or 0))]

    results: List[SpawnResult] = []
    cmd = _client_entry_module(ui=req.ui)

    for cp_id in ids:
        # Kayıtlı ama ölmüşse temizle
        meta = store.clients.get(cp_id)
        if meta and not _is_alive(meta.pid):
            del store.clients[cp_id]
            meta = None

        # Hâlâ çalışıyorsa atla
        if meta:
            continue

        # Uygun ve boş bir port bul
        port = _next_free_port(store.next_port())

        # ENV'leri hazırla
        env = env_template.copy()
        env["APP_PORT"] = str(port)
        env["CP_ID"] = cp_id
        env["SERVER_URL"] = req.server_url  # senin serverın: wss:// ... (TLS varsa)

        # stdout/stderr logları
        out = open(logs / f"{cp_id}.out", "ab")
        err = open(logs / f"{cp_id}.err", "ab")

        # Proje kökünden çalıştır (import yolları için kritik)
        proc: Popen = Popen(cmd, env=env, cwd=str(ROOT_DIR), stdout=out, stderr=err)

        store.clients[cp_id] = ClientProcess(pid=proc.pid, port=port, cp_id=cp_id, city=req.city)
        results.append(SpawnResult(
            cp_id=cp_id,
            pid=proc.pid,
            ui=_ui_url(port, cp_id) if req.ui else None,   # <<< değişti
            city=req.city
        ))
        logger.info(f"Spawned client: {cp_id} pid={proc.pid} port={port} url={scheme}://localhost:{port}")

    return [r.model_dump() for r in results]
