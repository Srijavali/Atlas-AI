import asyncio

import asyncpg


async def main() -> None:
    print("Testing direct asyncpg connection...")

    connection = await asyncpg.connect(
        user="postgres",
        password="postgres",
        database="atlas_ai",
        host="127.0.0.1",
        port=5433,
    )

    try:
        result = await connection.fetchval("SELECT 1")
        print(f"Direct asyncpg connection successful: {result}")
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())