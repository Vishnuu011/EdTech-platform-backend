import asyncio
from pathlib import Path
import sys
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2])
)
from src.infrastructure.redis.client import redis_client


async def test_redis_connection():

    response=await redis_client.ping()

    print(f"Redis response: {response}")

    await redis_client.aclose()



if __name__ == "__main__":
    asyncio.run(test_redis_connection())