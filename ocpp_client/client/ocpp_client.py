import asyncio
import json
import logging
import uuid
from datetime import datetime
import websockets
from ocpp_client.client.status_simulator import StatusSimulator
from ocpp_client.client.message_templates import MessageTemplates
from ocpp_client.client.manuel_controller import ManualController
from ocpp_client.client.config import CLIENT_CONFIG
import ssl

class OCPPClient:
    def __init__(self, server_url: str, charge_point_id: str):
        self.server_url = server_url
        self.charge_point_id = charge_point_id
        self.websocket = None
        self.heartbeat_interval = CLIENT_CONFIG["default_heartbeat_interval"]
        self.logger = logging.getLogger(f"OCPPClient[{charge_point_id}]")
        self.simulator = StatusSimulator(self)
        self.manual_controller = ManualController(self)
        self.templates = MessageTemplates()
        self.connected = False
        self.heartbeat_task = None
        self.last_heartbeat = None
        
    async def start(self):
        while True:
            try:
                await self.connect()
                await self.handle_connection()
            except Exception as e:
                self.logger.error(f"Connection failed: {e}")
                await asyncio.sleep(5)
                
    async def connect(self):
        subprotocol = "ocpp1.6"
        self.logger.info(f"Connecting to {self.server_url}")
        

        ssl_context = ssl._create_unverified_context()

        self.websocket = await websockets.connect(
            f"{self.server_url}/{self.charge_point_id}",
            subprotocols=[subprotocol],
            ssl=ssl_context,
            ping_interval=30,
            ping_timeout=10
        )

        
        self.connected = True
        self.logger.info("WebSocket connected")
        
    async def handle_connection(self):
        try:
            await self.send_boot_notification()
            
            self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
            simulator_task = asyncio.create_task(self.simulator.start())
            
            async for message in self.websocket:
                await self.handle_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("Connection closed")
        finally:
            self.connected = False
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                
    async def handle_message(self, raw_message: str):
        try:
            message = json.loads(raw_message)
            message_type = message[0]
            message_id = message[1]
            
            if message_type == 3:  # CALLRESULT
                action = message[2] if len(message) > 2 else "Unknown"
                payload = message[3] if len(message) > 3 else {}
                await self.handle_call_result(message_id, action, payload)
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            
    async def handle_call_result(self, message_id: str, action: str, payload: dict):
        if payload.get("status") == "Accepted" and payload.get("interval"):
            old_interval = self.heartbeat_interval
            self.heartbeat_interval = payload["interval"]
            self.logger.info(f"Heartbeat interval updated: {old_interval}s -> {self.heartbeat_interval}s")
            
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
                
    async def send_message(self, action: str, payload: dict) -> str:
        if not self.connected:
            return None
            
        message_id = str(uuid.uuid4())
        message = [2, message_id, action, payload]
        
        try:
            await self.websocket.send(json.dumps(message))
            self.logger.debug(f"Sent {action}: {payload}")
            return message_id
        except Exception as e:
            self.logger.error(f"Failed to send {action}: {e}")
            return None
            
    async def send_boot_notification(self):
        payload = self.templates.boot_notification()
        await self.send_message("BootNotification", payload)
        self.logger.info("BootNotification sent")
        
    async def send_heartbeat(self):
        payload = self.templates.heartbeat()
        await self.send_message("Heartbeat", payload)
        self.last_heartbeat = datetime.now()
        self.logger.info("Heartbeat sent")
        
    async def send_status_notification(self, connector_id: int, status: str, error_code: str = "NoError"):
        payload = self.templates.status_notification(connector_id, status, error_code)
        await self.send_message("StatusNotification", payload)
        self.logger.info(f"StatusNotification sent: Connector {connector_id} -> {status}")
        
        try:
            from backend.api.websocket import websocket_manager
            await websocket_manager.broadcast({
                "type": "status_update",
                "connector_id": connector_id,
                "status": status,
                "timestamp": datetime.now().isoformat()
            })
        except:
            pass
        
    async def heartbeat_loop(self):
        while self.connected:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self.send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")
