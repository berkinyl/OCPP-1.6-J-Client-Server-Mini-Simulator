import asyncio
import logging
from ocpp_client.client.ocpp_client import OCPPClient
from ocpp_client.client.config import CLIENT_CONFIG

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_ocpp_client():
    return OCPPClient(
        server_url=CLIENT_CONFIG["server_url"],
        charge_point_id=CLIENT_CONFIG["charge_point_id"]
    )

async def main():
    client = create_ocpp_client()
    await client.start()

if __name__ == "__main__":
    asyncio.run(main())