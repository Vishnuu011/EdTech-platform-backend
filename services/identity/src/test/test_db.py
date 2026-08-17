import asyncio

import sys
from pathlib import Path
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2])
)
from sqlalchemy import text
from src.database.connection import engine


async def test_database_connection():

    async with engine.connect() as conn:
        result=await conn.execute(
            text("SELECT 1")
        )

        print (
            f"Database connection result: {
                result.scalar()
            }"
        )

        print("successfully connected")




if __name__ == "__main__":
    asyncio.run(test_database_connection())
