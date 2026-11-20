from fastapi import APIRouter, Depends, HTTPException, Request, status

from gitguru.api.deps import check_db

router = APIRouter(tags=["health"])


@router.api_route("/health", methods=["GET", "HEAD"])
async def health(request: Request):
    return {
        "status": "ok",
        "app": "gitguru",
        "env": request.app.state.app_env,
        "version": request.app.state.git_sha,
    }


@router.get("/ready")
async def ready(database: bool = Depends(check_db)):
    if not database:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not ready", "checks": {"database": False}},
        )

    return {"status": "ready", "checks": {"database": True}}
