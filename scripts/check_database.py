import asyncio

from sqlalchemy import text

from backend.persistence.database import engine


async def main() -> None:
    print("Connecting to PostgreSQL...")

    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))
        value = result.scalar_one()

    print(f"Database connection successful: {value}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())