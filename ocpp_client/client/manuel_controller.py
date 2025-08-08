import asyncio
import logging
from datetime import datetime
from ocpp_client.client.status_simulator import ChargePointStatus

class ManualController:
    def __init__(self, client):
        self.client = client
        self.logger = logging.getLogger("ManualController")
        
    async def start_charging(self, connector_id: int) -> bool:
        connector = self.client.simulator.connectors.get(connector_id)
        if not connector:
            return False
            
        if connector.status != ChargePointStatus.AVAILABLE:
            self.logger.warning(f"Connector {connector_id} not available for charging")
            return False
            
        await self.client.simulator.change_status(connector, ChargePointStatus.PREPARING)
        await asyncio.sleep(3)
        await self.client.simulator.change_status(connector, ChargePointStatus.CHARGING)
        connector.session_active = True
        
        self.logger.info(f"Manual charging started on connector {connector_id}")
        return True
        
    async def stop_charging(self, connector_id: int) -> bool:
        connector = self.client.simulator.connectors.get(connector_id)
        if not connector:
            return False
            
        if connector.status not in [
            ChargePointStatus.CHARGING,
            ChargePointStatus.SUSPENDED_EV,
            ChargePointStatus.SUSPENDED_EVSE
        ]:
            return False
            
        await self.client.simulator.change_status(connector, ChargePointStatus.FINISHING)
        await asyncio.sleep(2)
        await self.client.simulator.change_status(connector, ChargePointStatus.AVAILABLE)
        connector.session_active = False
        
        self.logger.info(f"Manual charging stopped on connector {connector_id}")
        return True
        
    async def suspend_charging(self, connector_id: int) -> bool:
        connector = self.client.simulator.connectors.get(connector_id)
        if not connector:
            return False
            
        if connector.status != ChargePointStatus.CHARGING:
            self.logger.warning(f"Connector {connector_id} is not charging. Cannot suspend.")
            return False
            
        await self.client.simulator.change_status(connector, ChargePointStatus.SUSPENDED_EV)
        self.logger.info(f"Manual charging suspended on connector {connector_id}")
        return True

    async def resume_charging(self, connector_id: int) -> bool:
        connector = self.client.simulator.connectors.get(connector_id)
        if not connector:
            return False
            
        if connector.status != ChargePointStatus.SUSPENDED_EV:
            self.logger.warning(f"Connector {connector_id} is not suspended. Cannot resume.")
            return False
            
        await self.client.simulator.change_status(connector, ChargePointStatus.CHARGING)
        self.logger.info(f"Manual charging resumed on connector {connector_id}")
        return True
