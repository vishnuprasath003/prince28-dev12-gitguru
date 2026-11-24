import pytest
from sqlalchemy import select

from gitguru.config import Settings
from gitguru.db.models import Document, Page, ParseFailure
from gitguru.db.session import make_engine, make_sessionmaker
from gitguru.ingest.parse import ParsedDoc, ParsedPage, ParseError
from gitguru.ingest.store import store_failure, store_parsed


@pytest.fixture
async def db_session(database_url):
    """Create a session connected to the isolated test database."""
    settings = Settings(app_env="ci", database_url=database_url, _env_file=None)
    engine = make_engine(settings)

    async with make_sessionmaker(engine)() as session:
        yield session

    await engine.dispose()


async def test_store_parsed_saves_document_and_pages(db_session, tmp_path):
    path = tmp_path / "guide.md"
    path.write_text("# Fever\n\nDrink water.", encoding="utf-8")

    parsed = ParsedDoc(
        parser="markdown",
        kind="text",
        title="Health Guide",
        pages=[
            ParsedPage(
                page_no=1,
                text="Drink water.",
                headings=["Fever"],
                tables=0,
            )
        ],
    )

    document = await store_parsed(
        db_session,
        path,
        parsed,
        source_url="https://example.com/guide",
    )

    saved_document = await db_session.get(Document, document.id)
    saved_pages = list(
        await db_session.scalars(select(Page).where(Page.doc_id == document.id))
    )

    assert saved_document is not None
    assert saved_document.title == "Health Guide"
    assert saved_document.source_url == "https://example.com/guide"
    assert len(saved_pages) == 1
    assert saved_pages[0].page_no == 1
    assert saved_pages[0].headings == ["Fever"]
    assert saved_pages[0].text == "Drink water."


async def test_store_failure_saves_parse_error(db_session, tmp_path):
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"invalid pdf content")

    error = ParseError("corrupt", "Unable to read PDF")

    failure = await store_failure(
        db_session,
        path,
        error,
        source_url="https://example.com/broken.pdf",
    )

    saved = await db_session.scalar(
        select(ParseFailure).where(ParseFailure.path == str(path))
    )

    assert saved is not None
    assert saved.id == failure.id
    assert saved.reason == "corrupt"
    assert saved.detail == "Unable to read PDF"
    assert saved.attempts == 1
    assert saved.source_url == "https://example.com/broken.pdf"


async def test_store_failure_updates_attempts_and_parsed_removes_failure(
    db_session, tmp_path
):
    path = tmp_path / "recovered.md"
    path.write_text("# Recovered\n\nThis file is readable.", encoding="utf-8")

    first_error = ParseError("empty", "No readable content")
    await store_failure(db_session, path, first_error)

    second_error = ParseError("corrupt", "Second parsing attempt failed")
    await store_failure(db_session, path, second_error)

    failure = await db_session.scalar(
        select(ParseFailure).where(ParseFailure.path == str(path))
    )

    assert failure is not None
    assert failure.attempts == 2
    assert failure.reason == "corrupt"

    parsed = ParsedDoc(
        parser="markdown",
        kind="text",
        title="Recovered Guide",
        pages=[
            ParsedPage(
                page_no=1,
                text="This file is readable.",
                headings=["Recovered"],
            )
        ],
    )

    await store_parsed(db_session, path, parsed)

    remaining_failure = await db_session.scalar(
        select(ParseFailure).where(ParseFailure.path == str(path))
    )

    assert remaining_failure is None
