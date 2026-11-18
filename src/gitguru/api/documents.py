import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from gitguru.api.deps import get_repo
from gitguru.db.repository import DocumentRepository

router = APIRouter(prefix="/documents", tags=["documents"])

FILTER_KEY = re.compile(r"^[a-z_][a-z0-9_]{0,40}$")


@router.get("/")
async def list_documents(
    request: Request,
    repo: Annotated[DocumentRepository, Depends(get_repo)],
    q: str | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    reserved = {"q", "limit", "offset"}

    filters = {
        key: value for key, value in request.query_params.items() if key not in reserved
    }

    for key in filters:
        if not FILTER_KEY.fullmatch(key):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filter name: {key}",
            )

    total, documents = await repo.list(
        q=q,
        filters=filters,
        limit=limit,
        offset=offset,
    )

    return {
        "total": total,
        "documents": documents,
        "filters": filters,
        "limit": limit,
        "offset": offset,
    }
