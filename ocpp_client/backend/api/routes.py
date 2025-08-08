from fastapi import APIRouter, HTTPException, Depends
from models import ConnectorStatus, SystemStatus
from ocpp_client.backend.dependencies import get_ocpp_client
import logging

router = APIRouter()
logger = logging.getLogger("API")

@router.get("/status", response_model=SystemStatus)
async def get_system_status(client = Depends(get_ocpp_client)):
    if client is None:
        raise HTTPException(status_code=500, detail="OCPP client not initialized")

    return SystemStatus(
        connected=client.connected,
        charge_point_id=client.charge_point_id,
        heartbeat_interval=client.heartbeat_interval,
        last_heartbeat=getattr(client, 'last_heartbeat', None),
        connectors={
            cid: ConnectorStatus(
                connector_id=conn.connector_id,
                status=conn.status.value,
                last_update=conn.last_status_change,
                session_active=conn.session_active
            )
            for cid, conn in client.simulator.connectors.items()
        },
        manual_mode=client.simulator.manual_mode
    )

@router.post("/connectors/{connector_id}/start")
async def start_charging(connector_id: int, client = Depends(get_ocpp_client)):
    if client is None or connector_id not in client.simulator.connectors:
        raise HTTPException(status_code=404, detail="Connector not found or client not initialized")

    success = await client.manual_controller.start_charging(connector_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot start charging")
    return {"message": "Charging started", "connector_id": connector_id}

@router.post("/connectors/{connector_id}/stop")
async def stop_charging(connector_id: int, client = Depends(get_ocpp_client)):
    if client is None or connector_id not in client.simulator.connectors:
        raise HTTPException(status_code=404, detail="Connector not found or client not initialized")

    success = await client.manual_controller.stop_charging(connector_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot stop charging")
    return {"message": "Charging stopped", "connector_id": connector_id}

@router.post("/connectors/{connector_id}/suspend")
async def suspend_charging(connector_id: int, client = Depends(get_ocpp_client)):
    if client is None or connector_id not in client.simulator.connectors:
        raise HTTPException(status_code=404, detail="Connector not found or client not initialized")

    success = await client.manual_controller.suspend_charging(connector_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot suspend charging")
    return {"message": "Charging suspended", "connector_id": connector_id}

@router.post("/connectors/{connector_id}/resume")
async def resume_charging(connector_id: int, client = Depends(get_ocpp_client)):
    if client is None or connector_id not in client.simulator.connectors:
        raise HTTPException(status_code=404, detail="Connector not found or client not initialized")
    
    success = await client.manual_controller.resume_charging(connector_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot resume charging")
    
    return {"message": "Charging resumed", "connector_id": connector_id}

@router.post("/mode/toggle")
async def toggle_mode(client = Depends(get_ocpp_client)):
    if client is None:
        raise HTTPException(status_code=500, detail="Client not initialized")

    client.simulator.manual_mode = not client.simulator.manual_mode
    mode = "Manual" if client.simulator.manual_mode else "Automatic"
    logger.info(f"Mode switched to: {mode}")
    return {"mode": mode, "manual": client.simulator.manual_mode}
