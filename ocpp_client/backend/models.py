from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict
from enum import Enum

class ChargePointStatusEnum(str, Enum):
    AVAILABLE = "Available"
    PREPARING = "Preparing" 
    CHARGING = "Charging"
    FINISHING = "Finishing"
    SUSPENDED_EV = "SuspendedEV"
    SUSPENDED_EVSE = "SuspendedEVSE"
    FAULTED = "Faulted"
    UNAVAILABLE = "Unavailable"
    RESERVED = "Reserved"

class ConnectorStatus(BaseModel):
    connector_id: int
    status: ChargePointStatusEnum
    last_update: datetime
    session_active: bool = False
    error_code: str = "NoError"

class ConnectorCommand(BaseModel):
    action: str
    connector_id: int
    user_id: Optional[str] = None

class SystemStatus(BaseModel):
    connected: bool
    charge_point_id: str
    heartbeat_interval: int
    last_heartbeat: Optional[datetime]
    connectors: Dict[int, ConnectorStatus]
    manual_mode: bool = True