import asyncio

from sqlalchemy import text

from gitguru.db.session import make_engine


async def main():
    engine = make_engine()
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT current_database(), version();"))
        row = res.fetchone()
        print(f"Connected successfully to database: {row[0]}")
        print(f"PostgreSQL version: {row[1]}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
