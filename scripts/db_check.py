import asyncio

from sqlalchemy import text

from gitguru.db.session import make_engine


async def main():
    engine = make_engine()

    async with engine.connect() as conn:
        revision = await conn.execute(text("SELECT version_num FROM alembic_version"))
        print("REVISION:", revision.scalar())

        index = await conn.execute(
            text("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'documents'
                AND indexname = 'ix_documents_metadata_gin'
            """)
        )
        print("GIN INDEX:", index.scalar())

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
