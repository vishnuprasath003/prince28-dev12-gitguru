import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class PageBase(BaseModel):
    page_no: int
    text: str


class PageResponse(PageBase):
    id: uuid.UUID
    doc_id: uuid.UUID

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    title: str
    source_url: str | None = None
    licence: str | None = None
    doc_type: str | None = None
    published_on: date | None = None
    sha256: str = Field(..., min_length=64, max_length=64)
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")
    pages: list[PageBase] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class DocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    source_url: str | None = None
    licence: str | None = None
    doc_type: str | None = None
    published_on: date | None = None
    sha256: str
    metadata_: dict[str, Any] = Field(..., alias="metadata")
    created_at: datetime
    pages: list[PageResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
        populate_by_name = True
