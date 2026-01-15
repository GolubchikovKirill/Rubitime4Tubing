import httpx
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
RUBITIME_KEY = os.environ["RUBITIME_KEY"]

async def get_rubitime(record_id: int):
    async with httpx.AsyncClient(timeout=5.0) as client:
        url_get = "https://rubitime.ru/api2/get-record"
        payload = {
            "rk": RUBITIME_KEY,
            "id": record_id
        }
        r = await client.post(url_get, json=payload)
        r.raise_for_status()
        return r.json()

print(asyncio.run(get_rubitime(record_id=7551953)))
