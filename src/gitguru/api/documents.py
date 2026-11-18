import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from gitguru.db.models import Document, Page
from gitguru.db.session import async_session_maker
from gitguru.schemas.document import DocumentCreate, DocumentResponse

router = APIRouter(prefix="/documents", tags=["documents"])


async def get_db():
    async with async_session_maker() as session:
        yield session


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    doc_in: DocumentCreate,
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    existing = await db.execute(
        select(Document).where(Document.sha256 == doc_in.sha256)
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A document with this sha256 hash already exists.",
        )

    db_doc = Document(
        title=doc_in.title,
        source_url=doc_in.source_url,
        licence=doc_in.licence,
        doc_type=doc_in.doc_type,
        published_on=doc_in.published_on,
        sha256=doc_in.sha256,
        metadata_=doc_in.metadata_,
    )

    for page_in in doc_in.pages:
        db_page = Page(page_no=page_in.page_no, text=page_in.text)
        db_doc.pages.append(db_page)

    db.add(db_doc)
    await db.commit()

    stmt = (
        select(Document)
        .options(selectinload(Document.pages))
        .where(Document.id == db_doc.id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    stmt = (
        select(Document).options(selectinload(Document.pages)).offset(skip).limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    stmt = (
        select(Document)
        .options(selectinload(Document.pages))
        .where(Document.id == doc_id)
    )
    result = await db.execute(stmt)
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return doc
