from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from gitguru.db.repository import DocumentRepository


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session


async def get_repo(
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> DocumentRepository:
    return DocumentRepository(session)


async def check_db(request: Request) -> bool:
    try:
        async with request.app.state.session_factory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False
