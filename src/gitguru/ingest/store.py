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


def document_id(sha256: str) -> str:
    """Create a stable document ID from its content hash."""
    return f"f-{sha256[:20]}"


async def store_parsed(
    session: AsyncSession,
    path: Path,
    parsed: ParsedDoc,
    source_url: str | None = None,
    licence: str | None = None,
) -> Document:
    """Save a parsed document and all its pages."""
    sha256 = file_sha256(path)
    external_id = document_id(sha256)

    existing = await session.scalar(
        select(Document).where(Document.external_id == external_id)
    )

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
        external_id=external_id,
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


# -------------------------------------------------------------------
# Day 10: Queue worker storage functions
# -------------------------------------------------------------------


async def save_document(
    session: AsyncSession,
    record: dict,
    parsed: ParsedDoc,
) -> Document:
    """Save a document using the SHA-256 from the ingestion record."""
    sha256 = record["sha256"]
    external_id = document_id(sha256)

    existing = await session.scalar(
        select(Document).where(Document.external_id == external_id)
    )

    if existing is not None:
        return existing

    title = record.get("title") or parsed.title or "Untitled document"

    document = Document(
        title=title,
        source_url=record.get("url"),
        licence=record.get("licence"),
        doc_type=parsed.kind,
        external_id=external_id,
        sha256=sha256,
        metadata_={
            "parser": parsed.parser,
            "pages": len(parsed.pages),
            "tables": sum(page.tables for page in parsed.pages),
            "source": record.get("source"),
            "path": record.get("path"),
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

    await session.flush()

    return document


async def save_failure(
    session: AsyncSession,
    record: dict,
    error: ParseError,
) -> ParseFailure:
    """Save a parsing failure from a queued ingestion record."""
    sha256 = record["sha256"]

    # Use the URL as the failure path/identity for queue records.
    failure_path = record.get("path") or record.get("url") or sha256

    failure = await session.scalar(
        select(ParseFailure).where(ParseFailure.path == failure_path)
    )

    if failure is None:
        failure = ParseFailure(
            path=failure_path,
            sha256=sha256,
            source_url=record.get("url"),
            reason=error.reason,
            detail=error.detail,
            attempts=1,
        )
        session.add(failure)
    else:
        failure.sha256 = sha256
        failure.source_url = record.get("url")
        failure.reason = error.reason
        failure.detail = error.detail
        failure.attempts += 1

    await session.flush()

    return failure
