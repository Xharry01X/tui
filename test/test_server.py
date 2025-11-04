import asyncio
import websockets
from src.config import CENTRAL_SERVER_URL

async def test_connection():
    try:
        async with websockets.connect(CENTRAL_SERVER_URL) as websocket:
            print("✅ Connected to central server!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
