import hashlib
import json
from pathlib import Path

def get_or_create_client_config(cp_id: str):
    """Her CP_ID için kalıcı ve benzersiz config üretir"""
    
    # Config dosyasını saklamak için dizin
    config_dir = Path("client_configs")
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / f"{cp_id}.json"
    
    # Eğer bu CP_ID için config varsa, onu yükle
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    
    # Yoksa yeni oluştur
    # CP_ID'den deterministik değerler üret (her zaman aynı olacak)
    hash_base = hashlib.md5(cp_id.encode()).hexdigest()
    
    config = {
        "server_url": "wss://localhost:8080",
        "charge_point_id": cp_id,
        "charge_point_vendor": "Vestel",
        "charge_point_model": "AC22kW",
        "charge_point_serial_number": f"VST-{hash_base[:8].upper()}",
        "charge_box_serial_number": f"BOX-{hash_base[8:16].upper()}",
        "firmware_version": "1.2.3",
        "iccid": f"898600{hash_base[:14]}",  # Türkiye ICCID formatı
        "imsi": f"28601{hash_base[:10]}",     # Türkiye IMSI formatı
        "meter_type": "AC",
        "meter_serial_number": f"MTR-{hash_base[16:24].upper()}",
        "default_heartbeat_interval": 60,
        "connector_count": 2,
        "simulation": {
            "charging_duration_min": 30,
            "charging_duration_max": 120,
            "idle_duration_min": 60,
            "idle_duration_max": 300,
            "status_change_probability": 0.15
        }
    }
    
    # Config'i kaydet
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config

# Varsayılan config (import edildiğinde CP_ID yoksa kullanılır)
CLIENT_CONFIG = {
    "server_url": "wss://localhost:8080",  
    "charge_point_id": "VESTEL_EVC",
    "charge_point_vendor": "Vestel",
    "charge_point_model": "AC22kW",
    "charge_point_serial_number": "VST2024001",
    "charge_box_serial_number": "BOX2024001",
    "firmware_version": "1.2.3",
    "iccid": "8986011234567890123",
    "imsi": "286011234567890",
    "meter_type": "AC",
    "meter_serial_number": "MTR2024001",
    "default_heartbeat_interval": 60,
    "connector_count": 2,
    "simulation": {
        "charging_duration_min": 30,
        "charging_duration_max": 120,
        "idle_duration_min": 60,
        "idle_duration_max": 300,
        "status_change_probability": 0.15
    }
}