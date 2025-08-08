import subprocess
import sys
import os

def main():
    print("🚀 Starting Mock OCPP Server...")
    print("📡 Server will run on ws://localhost:8080")
    print("🔌 Clients can connect to ws://localhost:8080/{charge_point_id}")
    print("⚡ Press Ctrl+C to stop\n")
    
    try:
        subprocess.run([sys.executable, "mock_server.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()