import asyncio
import json
import logging
import websockets
from datetime import datetime
from pathlib import Path
import ssl
import aiohttp
import os
from collections import OrderedDict  # cpId'yi "en başa" koymak için

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MockOCPPServer:
    def __init__(self, host="localhost", port=8080, use_ssl=True):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.logger = logging.getLogger("MockOCPPServer")
        self.connected_clients = {}
        # REST API kök adresi (ENV ile değiştirilebilir)
        self.rest_base = os.environ.get("REST_API_BASE", "http://localhost:3000")

    async def _post_to_rest(self, endpoint: str, payload: dict):
        """
        REST'e POST. payload, cpId'yi de içeren zarf (OrderedDict) olmalı.
        """
        url = f"{self.rest_base.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                
                self.logger.info(f"[REST] → {endpoint} payload: {json.dumps(payload, ensure_ascii=False)}")
                
                async with session.post(url, json=payload) as resp:
                    text = await resp.text()
                    if resp.status >= 400:
                        self.logger.error(f"[REST] {endpoint} -> {resp.status} {text}")
                    else:
                        self.logger.info(f"[REST] OK {endpoint} -> {resp.status}")
        except Exception as e:
            self.logger.error(f"[REST] POST {endpoint} failed: {e}")

    async def _log_action_to_rest(self, cp_id: str, action: str, payload: dict):
        """
        OCPP şemasına dokunmadan, REST'e giderken cpId kolonu eklenir.
        Her endpoint'e gönderilen JSON'un EN BAŞINA cpId konur (OrderedDict).
        """
        if action == "BootNotification":
            body = OrderedDict([
                ("cpId", cp_id),
                ("chargePointVendor",       payload.get("chargePointVendor")),
                ("chargePointModel",        payload.get("chargePointModel")),
                ("chargePointSerialNumber", payload.get("chargePointSerialNumber")),
                ("chargeBoxSerialNumber",   payload.get("chargeBoxSerialNumber")),
                ("firmwareVersion",         payload.get("firmwareVersion")),
                ("iccid",                   payload.get("iccid")),
                ("imsi",                    payload.get("imsi")),
                ("meterType",               payload.get("meterType")),
                ("meterSerialNumber",       payload.get("meterSerialNumber")),
            ])
            await self._post_to_rest("/bootnotification", body)

        elif action == "Heartbeat":
            body = OrderedDict([
                ("cpId", cp_id),
                ("currentTime", payload.get("currentTime")),  # genelde boş gönderiyordun; istersen bırak
            ])
            await self._post_to_rest("/heartbeat", body)

        elif action == "StatusNotification":
            body = OrderedDict([
                ("cpId", cp_id),
                ("connectorId",     payload.get("connectorId")),
                ("status",          payload.get("status")),
                ("errorCode",       payload.get("errorCode")),
                ("info",            payload.get("info")),
                ("timestamp",       payload.get("timestamp")),
                ("vendorId",        payload.get("vendorId")),
                ("vendorErrorCode", payload.get("vendorErrorCode")),
            ])
            await self._post_to_rest("/status-notification", body)

        else:
            # Diğer action'lar için forward yapmıyorsan logla ve geç
            self.logger.debug(f"[REST] No route mapped for action: {action}")

    async def start(self):
        protocol = "wss" if self.use_ssl else "ws"
        self.logger.info(f"Starting mock OCPP server on {protocol}://{self.host}:{self.port}")

        ssl_context = None
        if self.use_ssl:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_cert = Path("cert.pem")
            ssl_key  = Path("key.pem")
            if not ssl_cert.exists() or not ssl_key.exists():
                self.logger.error("SSL certificate or key file not found!")
                raise FileNotFoundError("cert.pem or key.pem not found in current directory.")
            ssl_context.load_cert_chain(str(ssl_cert), str(ssl_key))

        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            subprotocols=["ocpp1.6"],
            ssl=ssl_context
        ):
            self.logger.info(f"Mock server started on {protocol}://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever

    async def handle_client(self, websocket, path):
        # <<< CP_ID burada URL path'inden alınır
        charge_point_id = path.strip('/')
        client_addr = websocket.remote_address

        self.logger.info(f"Client connected: {charge_point_id} from {client_addr}")
        self.connected_clients[charge_point_id] = websocket

        try:
            async for message in websocket:
                await self.handle_message(websocket, charge_point_id, message)
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client disconnected: {charge_point_id}")
        finally:
            self.connected_clients.pop(charge_point_id, None)

    async def handle_message(self, websocket, charge_point_id, raw_message):
        try:
            message = json.loads(raw_message)
            message_type = message[0]
            message_id   = message[1]
            action       = message[2]
            payload      = message[3] if len(message) > 3 else {}

            self.logger.info(f"[{charge_point_id}] Received {action}: {payload}")

            if message_type == 2:  # CALL
                response = await self.process_call(action, payload)
                response_message = [3, message_id, response]

                await websocket.send(json.dumps(response_message))
                self.logger.info(f"[{charge_point_id}] Sent response: {response}")

                # REST'e cpId eklenmiş zarfı gönder (asenkron)
                asyncio.create_task(self._log_action_to_rest(charge_point_id, action, payload))

            # (CALLRESULT ve CALLERROR'ı özel forward etmek istersen burada ekleyebilirsin)

        except Exception as e:
            self.logger.error(f"Error processing message from {charge_point_id}: {e}")

    async def process_call(self, action, payload):
        if action == "BootNotification":
            return {
                "status": "Accepted",
                "currentTime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "interval": 60  # Heartbeat interval (saniye)
            }
        elif action == "Heartbeat":
            return {
                "currentTime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            }
        elif action == "StatusNotification":
            return {}
        else:
            self.logger.warning(f"Unknown action: {action}")
            return {}

async def main():
    server = MockOCPPServer()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
