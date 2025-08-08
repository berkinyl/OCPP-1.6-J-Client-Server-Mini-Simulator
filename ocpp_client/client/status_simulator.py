import asyncio
import random
import logging
from datetime import datetime
from enum import Enum
from ocpp_client.client.config import CLIENT_CONFIG

class ChargePointStatus(Enum):
    AVAILABLE = "Available"
    PREPARING = "Preparing"
    CHARGING = "Charging"
    FINISHING = "Finishing"
    SUSPENDED_EV = "SuspendedEV"
    SUSPENDED_EVSE = "SuspendedEVSE"
    FAULTED = "Faulted"
    UNAVAILABLE = "Unavailable"
    RESERVED = "Reserved"

class ConnectorState:
    def __init__(self, connector_id: int):
        self.connector_id = connector_id
        self.status = ChargePointStatus.AVAILABLE
        self.session_active = False
        self.last_status_change = datetime.now()

class StatusSimulator:
    def __init__(self, client):
        self.client = client
        self.connectors = {}
        self.logger = logging.getLogger("StatusSimulator")
        self.running = False
        self.manual_mode = True  # Default to manual mode
        
        for i in range(1, CLIENT_CONFIG["connector_count"] + 1):
            self.connectors[i] = ConnectorState(i)
            
    async def start(self):
        self.running = True
        
        await asyncio.sleep(2)
        for connector in self.connectors.values():
            await self.client.send_status_notification(
                connector.connector_id, 
                connector.status.value
            )
            
        tasks = []
        for connector_id in self.connectors.keys():
            task = asyncio.create_task(self.simulate_connector(connector_id))
            tasks.append(task)
            
        await asyncio.gather(*tasks, return_exceptions=True)
        
    async def simulate_connector(self, connector_id: int):
        connector = self.connectors[connector_id]
        
        while self.running:
            try:
                if not self.manual_mode:
                    await self.process_connector_state(connector)
                await asyncio.sleep(random.randint(10, 20))
                
            except Exception as e:
                self.logger.error(f"Connector {connector_id} simulation error: {e}")
                await asyncio.sleep(5)
                
    async def process_connector_state(self, connector: ConnectorState):
        config = CLIENT_CONFIG["simulation"]
        
        if random.random() < config["status_change_probability"]:
            if connector.status == ChargePointStatus.AVAILABLE:
                await self.start_charging_session(connector)
            elif connector.status == ChargePointStatus.CHARGING:
                if random.random() < 0.2:
                    await self.suspend_charging(connector)
                elif random.random() < 0.3:
                    await self.finish_charging(connector)
            elif connector.status in [ChargePointStatus.SUSPENDED_EV, ChargePointStatus.SUSPENDED_EVSE]:
                if random.random() < 0.6:
                    await self.resume_charging(connector)
                else:
                    await self.finish_charging(connector)
            elif connector.status == ChargePointStatus.FINISHING:
                await self.make_available(connector)
                
    async def start_charging_session(self, connector: ConnectorState):
        await self.change_status(connector, ChargePointStatus.PREPARING)
        await asyncio.sleep(random.randint(3, 8))
        await self.change_status(connector, ChargePointStatus.CHARGING)
        connector.session_active = True
        
    async def suspend_charging(self, connector: ConnectorState):
        status = random.choice([ChargePointStatus.SUSPENDED_EV, ChargePointStatus.SUSPENDED_EVSE])
        await self.change_status(connector, status)
        
    async def resume_charging(self, connector: ConnectorState):
        await self.change_status(connector, ChargePointStatus.CHARGING)
        
    async def finish_charging(self, connector: ConnectorState):
        await self.change_status(connector, ChargePointStatus.FINISHING)
        await asyncio.sleep(random.randint(2, 5))
        await self.make_available(connector)
        
    async def make_available(self, connector: ConnectorState):
        await self.change_status(connector, ChargePointStatus.AVAILABLE)
        connector.session_active = False
        
    async def change_status(self, connector: ConnectorState, new_status: ChargePointStatus):
        if connector.status != new_status:
            connector.status = new_status
            connector.last_status_change = datetime.now()
            
            await self.client.send_status_notification(
                connector.connector_id,
                new_status.value
            )
