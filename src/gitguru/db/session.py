from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from gitguru.config import settings


def make_engine():
    return create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)


engine = make_engine()

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)
