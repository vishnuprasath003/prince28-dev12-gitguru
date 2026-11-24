"""Store parsed documents and failures in PostgreSQL."""

import hashlib
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from gitguru.db.models import Document, Page, ParseFailure
from gitguru.ingest.parse import ParsedDoc, ParseError


def file_sha256(path: Path) -> str:
    """Calculate the SHA-256 fingerprint of a raw file."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


async def store_parsed(
    session: AsyncSession,
    path: Path,
    parsed: ParsedDoc,
    source_url: str | None = None,
    licence: str | None = None,
) -> Document:
    """Save a parsed document and all its pages."""
    sha256 = file_sha256(path)

    existing = await session.scalar(select(Document).where(Document.sha256 == sha256))

    if existing is not None:
        await session.execute(
            delete(ParseFailure).where(ParseFailure.path == str(path))
        )
        await session.flush()
        return existing

    document = Document(
        title=parsed.title or path.stem,
        source_url=source_url,
        licence=licence,
        doc_type=parsed.kind,
        sha256=sha256,
        metadata_={
            "parser": parsed.parser,
            "pages": len(parsed.pages),
            "tables": sum(page.tables for page in parsed.pages),
            "path": str(path),
        },
    )

    session.add(document)
    await session.flush()

    for parsed_page in parsed.pages:
        session.add(
            Page(
                doc_id=document.id,
                page_no=parsed_page.page_no,
                text=parsed_page.text,
                headings=parsed_page.headings,
            )
        )

    await session.execute(delete(ParseFailure).where(ParseFailure.path == str(path)))

    await session.flush()

    return document


async def store_failure(
    session: AsyncSession,
    path: Path,
    error: ParseError,
    source_url: str | None = None,
) -> ParseFailure:
    """Record a failed file, updating its attempt count when retried."""
    sha256 = file_sha256(path)

    failure = await session.scalar(
        select(ParseFailure).where(ParseFailure.path == str(path))
    )

    if failure is None:
        failure = ParseFailure(
            path=str(path),
            sha256=sha256,
            source_url=source_url,
            reason=error.reason,
            detail=error.detail,
            attempts=1,
        )
        session.add(failure)
    else:
        failure.sha256 = sha256
        failure.source_url = source_url
        failure.reason = error.reason
        failure.detail = error.detail
        failure.attempts += 1

    await session.flush()

    return failure
