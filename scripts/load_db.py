"""Idempotently load sample records into PostgreSQL documents."""

import asyncio
import hashlib
import json
import uuid
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from gitguru.db.models import Document
from gitguru.db.session import make_engine

DATA_FILE = Path("data/sample_records.json")


def fingerprint(record: dict) -> str:
    canonical = json.dumps(
        record,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def to_row(record: dict) -> dict:
    external_id = str(record["id"])
    published = record.get("published_on")

    return {
        "id": uuid.uuid5(uuid.NAMESPACE_URL, f"gitguru:document:{external_id}"),
        "title": str(record.get("title") or record.get("command") or external_id),
        "source_url": record.get("source_url"),
        "licence": record.get("licence"),
        "doc_type": record.get("doc_type") or "git_command",
        "published_on": date.fromisoformat(published) if published else None,
        "sha256": fingerprint(record),
        "metadata_": {
            key: value
            for key, value in record.items()
            if key
            not in {
                "id",
                "title",
                "source_url",
                "licence",
                "doc_type",
                "published_on",
            }
        },
    }


async def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = data["value"] if isinstance(data, dict) else data

    engine = make_engine()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    inserted = updated = unchanged = 0

    try:
        async with session_factory() as session, session.begin():
            result = await session.scalars(select(Document))
            existing = {doc.id: doc for doc in result.all()}

            for record in records:
                row = to_row(record)
                doc = existing.get(row["id"])

                if doc is None:
                    doc = Document(**row)
                    session.add(doc)
                    existing[row["id"]] = doc
                    inserted += 1

                elif doc.sha256 != row["sha256"]:
                    for key, value in row.items():
                        setattr(doc, key, value)
                    updated += 1

                else:
                    unchanged += 1

    finally:
        await engine.dispose()

    print(
        f"records={len(records)} inserted={inserted} "
        f"updated={updated} unchanged={unchanged}"
    )


if __name__ == "__main__":
    asyncio.run(main())
