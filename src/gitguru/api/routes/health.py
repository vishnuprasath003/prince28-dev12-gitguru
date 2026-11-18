from fastapi import APIRouter, Depends, HTTPException, status

from gitguru.api.deps import check_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "healthy"}


@router.get("/ready")
async def ready(database: bool = Depends(check_db)):
    if not database:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not ready", "checks": {"database": False}},
        )

    return {"status": "ready", "checks": {"database": True}}
