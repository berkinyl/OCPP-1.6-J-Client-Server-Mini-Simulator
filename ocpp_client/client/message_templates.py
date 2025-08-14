from datetime import datetime
from ocpp_client.client.config import CLIENT_CONFIG

class MessageTemplates:
    
    @staticmethod
    def boot_notification() -> dict:
        return {
            "chargePointVendor": CLIENT_CONFIG["charge_point_vendor"],
            "chargePointModel": CLIENT_CONFIG["charge_point_model"],
            "chargePointSerialNumber": CLIENT_CONFIG.get("charge_point_serial_number"),
            "chargeBoxSerialNumber": CLIENT_CONFIG.get("charge_box_serial_number"),
            "firmwareVersion": CLIENT_CONFIG.get("firmware_version"),
            "iccid": CLIENT_CONFIG.get("iccid"),
            "imsi": CLIENT_CONFIG.get("imsi"),
            "meterType": CLIENT_CONFIG.get("meter_type"),
            "meterSerialNumber": CLIENT_CONFIG.get("meter_serial_number")
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