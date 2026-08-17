import asyncio
import sys
from pathlib import Path
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2])
)

from src.infrastructure.messaging.rabbitmq import rabbitmq


async def test_rabbitmq_connection():

    await rabbitmq.connect()

    print("RabbitMQ connection established.")

    await rabbitmq.close()

    print("RabbitMQ connection closed.")


async def check_rabbitmq_connection():
    if not rabbitmq.is_connected:
        await rabbitmq.connect()

    return rabbitmq.is_connected


if __name__ == "__main__":
    asyncio.run(test_rabbitmq_connection())    