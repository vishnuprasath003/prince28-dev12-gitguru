from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from gitguru.config import Settings, settings


def make_engine(config: Settings | None = None):
    config = config or settings
    return create_async_engine(
        config.database_url,
        echo=False,
        pool_pre_ping=True,
    )


def make_sessionmaker(engine):
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


engine = make_engine()
async_session_maker = make_sessionmaker(engine)
