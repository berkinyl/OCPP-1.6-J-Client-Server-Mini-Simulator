from datetime import datetime
from ocpp_client.client.config import CLIENT_CONFIG

class MessageTemplates:
    
    @staticmethod
    def boot_notification() -> dict:
        return {
            "chargePointVendor": CLIENT_CONFIG["charge_point_vendor"],
            "chargePointModel": CLIENT_CONFIG["charge_point_model"],
            "firmwareVersion": CLIENT_CONFIG["firmware_version"],
            "chargePointSerialNumber": CLIENT_CONFIG["serial_number"]
        }
    
    @staticmethod
    def heartbeat() -> dict:
        return {}
    
    @staticmethod
    def status_notification(connector_id: int, status: str, error_code: str = "NoError") -> dict:
        return {
            "connectorId": connector_id,
            "errorCode": error_code,
            "status": status,
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }