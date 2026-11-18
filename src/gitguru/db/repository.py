"""PostgreSQL repository for GitGuru documents."""

import re
from typing import Any

from sqlalchemy import Text, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from gitguru.db.models import Document

FILTER_KEY = re.compile(r"^[a-z_][a-z0-9_]{0,40}$")


def to_dict(doc: Document) -> dict[str, Any]:
    return {
        "id": str(doc.id),
        "title": doc.title,
        "source_url": doc.source_url,
        "licence": doc.licence,
        "doc_type": doc.doc_type,
        "published_on": (doc.published_on.isoformat() if doc.published_on else None),
        "sha256": doc.sha256,
        "metadata": doc.metadata_,
    }


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        *,
        q: str | None = None,
        filters: dict[str, str] | None = None,
        limit: int = 10,
        offset: int = 0,
    ):
        stmt = select(Document)

        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Document.title.ilike(like),
                    cast(Document.metadata_, Text).ilike(like),
                )
            )

        for key, value in (filters or {}).items():
            if not FILTER_KEY.fullmatch(key):
                raise ValueError(f"Invalid filter name: {key}")

            stmt = stmt.where(Document.metadata_.contains({key: value}))

        total = await self.session.scalar(
            select(func.count()).select_from(stmt.subquery())
        )

        result = await self.session.scalars(
            stmt.order_by(Document.title).limit(limit).offset(offset)
        )

        return total or 0, [to_dict(doc) for doc in result.all()]

    async def get(self, document_id: str):
        try:
            import uuid

            parsed_id = uuid.UUID(document_id)
        except ValueError:
            return None

        return await self.session.scalar(
            select(Document).where(Document.id == parsed_id)
        )
