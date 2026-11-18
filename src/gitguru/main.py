from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from gitguru.api.documents import router as documents_router
from gitguru.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(title="GitGuru API", version="0.1.0", lifespan=lifespan)

app.include_router(documents_router)


@app.get("/")
async def root():
    return {"message": "Welcome to GitGuru API", "status": "active"}


@app.get("/health")
async def health_check():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:  # noqa: BLE001
        return {"status": "unhealthy", "database": str(e)}
