import asyncio

from sqlalchemy import text

from gitguru.db.session import make_engine


async def main():
    engine = make_engine()
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT indexname
                    FROM pg_indexes
                    WHERE tablename = 'documents'
                """)
            )
            for row in result:
                print(row[0])
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
