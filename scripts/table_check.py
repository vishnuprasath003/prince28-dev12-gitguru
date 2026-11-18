import asyncio

from sqlalchemy import text

from gitguru.db.session import make_engine


async def main():
    engine = make_engine()
    async with engine.connect() as conn:
        res = await conn.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public';
            """)
        )
        tables = [row[0] for row in res.fetchall()]
        print(f"Tables in database: {tables}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
