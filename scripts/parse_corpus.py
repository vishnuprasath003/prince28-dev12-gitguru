"""Parse downloaded corpus files concurrently and store results in PostgreSQL."""

import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from gitguru.db.models import ParseFailure
from gitguru.db.session import async_session_maker
from gitguru.ingest.parse import ParseError, parse_file
from gitguru.ingest.store import store_failure, store_parsed

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "manifest.jsonl"


def resolve_path(path: str) -> Path:
    """Resolve manifest paths consistently."""
    file_path = Path(path)

    if not file_path.is_absolute():
        file_path = ROOT / file_path

    return file_path.resolve()


def read_manifest() -> list[dict]:
    """Read downloaded files from the JSONL manifest."""
    if not MANIFEST.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST}")

    records = []

    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        record = json.loads(line)

        if record.get("status") == "downloaded":
            records.append(record)

    return records


async def get_failed_paths() -> set[str]:
    """Get normalized paths currently recorded in parse_failures."""
    async with async_session_maker() as session:
        paths = await session.scalars(select(ParseFailure.path))

    return {str(resolve_path(path)) for path in paths.all()}


async def process_record(
    record: dict,
    semaphore: asyncio.Semaphore,
) -> str:
    """Parse one file and store either its document or its failure."""
    path = resolve_path(record["path"])

    if not path.exists():
        print(f"MISSING  {path.name}", flush=True)
        return "missing"

    async with semaphore:
        try:
            parsed = await asyncio.to_thread(parse_file, path)

            async with async_session_maker() as session, session.begin():
                await store_parsed(
                    session,
                    path,
                    parsed,
                    source_url=record.get("url"),
                )

            print(f"PARSED   {path.name}", flush=True)
            return "parsed"

        except ParseError as error:
            async with async_session_maker() as session, session.begin():
                await store_failure(
                    session,
                    path,
                    error,
                    source_url=record.get("url"),
                )

            print(f"FAILED   {path.name}: {error}", flush=True)
            return "failed"

        except Exception as error:  # noqa: BLE001
            parse_error = ParseError("parse_error", str(error))

            async with async_session_maker() as session, session.begin():
                await store_failure(
                    session,
                    path,
                    parse_error,
                    source_url=record.get("url"),
                )

            print(f"FAILED   {path.name}: {error}", flush=True)
            return "failed"


async def main(
    limit: int = 0,
    retry_failed: bool = False,
    workers: int = 3,
) -> None:
    """Process manifest files concurrently."""
    records = read_manifest()

    if retry_failed:
        failed_paths = await get_failed_paths()
        records = [
            record
            for record in records
            if str(resolve_path(record["path"])) in failed_paths
        ]

    if limit:
        records = records[:limit]

    counts = {"parsed": 0, "failed": 0, "missing": 0}
    semaphore = asyncio.Semaphore(workers)

    print(f"Files to process: {len(records)}")
    print(f"Concurrent workers: {workers}\n")

    tasks = [process_record(record, semaphore) for record in records]

    for task in asyncio.as_completed(tasks):
        result = await task
        counts[result] += 1

    print("\nParsing summary")
    print(f"Manifest files: {len(records)}")
    print(f"Parsed: {counts['parsed']}")
    print(f"Failed: {counts['failed']}")
    print(f"Missing: {counts['missing']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse downloaded corpus files.")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum number of files to process.",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry only files recorded in parse_failures.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Number of concurrent workers.",
    )

    args = parser.parse_args()

    asyncio.run(main(args.limit, args.retry_failed, args.workers))
