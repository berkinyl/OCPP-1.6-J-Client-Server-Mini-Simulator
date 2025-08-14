from __future__ import annotations

import asyncio
import json
import logging
import ssl
import uuid
from datetime import datetime
from typing import Optional

import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK, ConnectionClosedError

from ocpp_client.client.config import CLIENT_CONFIG
from ocpp_client.client.manuel_controller import ManualController
from ocpp_client.client.message_templates import MessageTemplates
from ocpp_client.client.status_simulator import StatusSimulator

# UI'ye canlı bildirim göndermek için (varsa) websocket_manager'ı içe aktar
try:
   # Tercih edilen tam modül yolu
   from ocpp_client.backend.api.websocket import websocket_manager  # type: ignore
except Exception:
   try:
       # Bazı dizaynlarda kısayol içe aktarımı kullanılmış olabilir
       from backend.api.websocket import websocket_manager  # type: ignore
   except Exception:
       websocket_manager = None  # UI yoksa sessizce atla


class OCPPClient:
   """
   Minimal fakat üretime yakın bir OCPP 1.6 JSON istemcisi.
   - Server'a bağlanır ve BootNotification gönderir
   - Server conf 'interval' ile heartbeat periyodunu günceller
   - Son mesajdan bu yana 'interval' dolduysa Heartbeat gönderir
   - StatusSimulator durum değişimlerinde StatusNotification yollar
   - Server → Client CALL (RemoteStart/RemoteStop) komutlarını işler
   """

   def __init__(self, server_url: str, charge_point_id: str) -> None:
       self.server_url = server_url.rstrip("/")
       self.charge_point_id = charge_point_id
       self.websocket: Optional[websockets.WebSocketClientProtocol] = None

       self.logger = logging.getLogger(f"OCPPClient[{self.charge_point_id}]")
       self.templates = MessageTemplates()
       self.simulator = StatusSimulator(self)
       self.manual_controller = ManualController(self)

       self.connected = False
       self.connection_accepted = False  # EKLENEN SATIR
       self.heartbeat_interval: int = CLIENT_CONFIG["default_heartbeat_interval"]
       self.last_heartbeat: Optional[datetime] = None
       self.last_message_time: datetime = datetime.now()

       self._hb_task: Optional[asyncio.Task] = None
       self._sim_task: Optional[asyncio.Task] = None

   # Lifecycle
   async def start(self) -> None:
       """
       Sürekli yeniden bağlanma stratejisi ile ana döngü.
       """
       backoff = 2
       while True:
           try:
               await self.connect()
               await self.handle_connection()
               backoff = 2  # başarıyla bağlanınca backoff'u sıfırla
           except Exception as e:
               self.logger.error(f"Connection failed: {e}")
               await asyncio.sleep(backoff)
               backoff = min(backoff * 2, 30)  # basit backoff: 2→4→8→16→30

   async def connect(self) -> None:
       """
       WebSocket bağlantısı kur.
       """
       subprotocol = "ocpp1.6"
       uri = f"{self.server_url}/{self.charge_point_id}"

       # Self-signed sertifikalar için doğrulanmamış context (lokalde pratik)
       ssl_context = ssl._create_unverified_context()

       self.logger.info(f"Connecting to {uri} ...")
       self.websocket = await websockets.connect(
           uri,
           subprotocols=[subprotocol],
           ssl=ssl_context,
           ping_interval=30,
           ping_timeout=10,
       )
       self.connected = True
       self.logger.info("WebSocket connected")

   async def handle_connection(self) -> None:
       """
       Bağlantı kurulduktan sonra mesaj akışı ve görevler.
       """
       assert self.websocket is not None

       try:
           # 1) BootNotification
           await self.send_boot_notification()
           self.connection_accepted = True  # EKLENEN SATIR

           # 2) Heartbeat & Simulator görevleri
           self._hb_task = asyncio.create_task(self._heartbeat_loop())
           self._sim_task = asyncio.create_task(self.simulator.start())

           # 3) Sunucudan gelen mesajları dinle
           async for raw in self.websocket:
               await self._handle_incoming(raw)

       except (ConnectionClosed, ConnectionClosedOK, ConnectionClosedError):
           self.logger.warning("Connection closed")
       finally:
           self.connected = False
           self.connection_accepted = False  # EKLENEN SATIR
           # Görevleri iptal et
           if self._hb_task:
               self._hb_task.cancel()
               with contextlib.suppress(Exception):
                   await self._hb_task
           if self._sim_task:
               self._sim_task.cancel()
               with contextlib.suppress(Exception):
                   await self._sim_task

   # Incoming frames
   async def _handle_incoming(self, raw_message: str) -> None:
       """
       OCPP çerçevelerini ayrıştır:
         - CALL       : [2, msgId, action, payload]
         - CALLRESULT : [3, msgId, payload]
         - CALLERROR  : [4, msgId, errorCode, errorDescription, errorDetails]
       """
       try:
           message = json.loads(raw_message)
           msg_type = message[0]

           if msg_type == 2:
               # Server → Client CALL
               msg_id, action, payload = message[1], message[2], message[3]
               await self._handle_call(msg_id, action, payload)

           elif msg_type == 3:
               # CALLRESULT
               msg_id, payload = message[1], message[2] if len(message) > 2 else {}
               await self._handle_call_result(msg_id, payload)

           elif msg_type == 4:
               # CALLERROR
               msg_id = message[1]
               err_code = message[2] if len(message) > 2 else "Unknown"
               err_desc = message[3] if len(message) > 3 else ""
               self.logger.error(f"CALLERROR (id={msg_id}): {err_code} - {err_desc}")

           # Son mesaj zamanını güncelle
           self.last_message_time = datetime.now()

       except Exception as e:
           self.logger.error(f"Error handling incoming message: {e}")

   async def _handle_call(self, msg_id: str, action: str, payload: dict) -> None:
       """
       Server → Client CALL handler'ları.
       """
       try:
           if action == "RemoteStartTransaction":
               connector_id = payload.get("connectorId", 1)
               ok = await self.manual_controller.start_charging(connector_id)
               conf = {"status": "Accepted" if ok else "Rejected"}
               await self._send_raw([3, msg_id, conf])
               self.logger.info(f"Handled {action}: {conf['status']} (connector={connector_id})")

           elif action == "RemoteStopTransaction":
               connector_id = payload.get("connectorId", 1)
               ok = await self.manual_controller.stop_charging(connector_id)
               conf = {"status": "Accepted" if ok else "Rejected"}
               await self._send_raw([3, msg_id, conf])
               self.logger.info(f"Handled {action}: {conf['status']} (connector={connector_id})")

           else:
               # Bilinmeyen action: boş conf dön (uyumluluk için)
               await self._send_raw([3, msg_id, {}])
               self.logger.debug(f"Ignored server CALL action={action}")

       except Exception as e:
           self.logger.error(f"Failed handling CALL {action}: {e}")
           # Minimum bir hata cevabı göndermeye çalış
           try:
               await self._send_raw([4, msg_id, "InternalError", str(e), {}])
           except Exception:
               pass

   async def _handle_call_result(self, msg_id: str, payload: dict) -> None:
       """
       Client → Server çağrılarının cevapları (özellikle BootNotification.conf).
       """
       # BootNotification.conf → {"status": "Accepted", "currentTime": "...", "interval": 60}
       try:
           if payload.get("status") == "Accepted" and "interval" in payload:
               old = self.heartbeat_interval
               self.heartbeat_interval = int(payload["interval"])
               self.logger.info(f"Heartbeat interval updated: {old}s -> {self.heartbeat_interval}s")

               # Heartbeat görevini tazele
               if self._hb_task:
                   self._hb_task.cancel()
                   with contextlib.suppress(Exception):
                       await self._hb_task
                   self._hb_task = asyncio.create_task(self._heartbeat_loop())

       except Exception as e:
           self.logger.error(f"Error in CALLRESULT handler: {e}")

   # Outgoing helpers
   async def _send_raw(self, frame: list) -> None:
       if not self.connected or not self.websocket:
           raise RuntimeError("WebSocket not connected")
       await self.websocket.send(json.dumps(frame))

   async def send_message(self, action: str, payload: dict) -> Optional[str]:
       """
       OCPP CALL gönder: [2, msgId, action, payload]
       """
       if not self.connected or not self.websocket:
           return None
       msg_id = str(uuid.uuid4())
       frame = [2, msg_id, action, payload]
       try:
           await self.websocket.send(json.dumps(frame))
           self.logger.debug(f"Sent {action}: {payload}")
           self.last_message_time = datetime.now()
           return msg_id
       except Exception as e:
           self.logger.error(f"Failed to send {action}: {e}")
           return None

   # Specific messages
   async def send_boot_notification(self) -> None:
       payload = self.templates.boot_notification()
       await self.send_message("BootNotification", payload)
       self.logger.info("BootNotification sent")

   async def send_heartbeat(self) -> None:
       payload = self.templates.heartbeat()
       await self.send_message("Heartbeat", payload)
       self.last_heartbeat = datetime.now()
       self.logger.info("Heartbeat sent")

   async def send_status_notification(
       self, connector_id: int, status: str, error_code: str = "NoError"
   ) -> None:
       payload = self.templates.status_notification(connector_id, status, error_code)
       await self.send_message("StatusNotification", payload)
       self.logger.info(f"StatusNotification sent: Connector {connector_id} -> {status}")

       # UI'ye canlı güncelleme
       if websocket_manager is not None:
           try:
               await websocket_manager.broadcast(
                   {
                       "type": "status_update",
                       "connector_id": connector_id,
                       "status": status,
                       "timestamp": datetime.now().isoformat(),
                   }
               )
           except Exception:
               # UI yoksa sessizce geç
               pass

   # Background loops
   async def _heartbeat_loop(self) -> None:
       """
       OCPP 1.6 kuralına uygun basit heartbeat:
       - Son mesaj gönderiminden bu yana 'interval' dolduysa Heartbeat yolla.
       """
       while self.connected:
           try:
               elapsed = (datetime.now() - self.last_message_time).total_seconds()
               wait_time = max(self.heartbeat_interval - elapsed, 0)
               if wait_time > 0:
                   await asyncio.sleep(wait_time)

               # Süre dolduysa heartbeat gönder
               if (datetime.now() - self.last_message_time).total_seconds() >= self.heartbeat_interval:
                   await self.send_heartbeat()
                   self.last_message_time = datetime.now()

           except asyncio.CancelledError:
               break
           except Exception as e:
               self.logger.error(f"Heartbeat loop error: {e}")
               await asyncio.sleep(1)


# İç kullanım: contextlib.suppress için yerel, standart import
import contextlib  # noqa: E402  (dosya sonunda dursun)