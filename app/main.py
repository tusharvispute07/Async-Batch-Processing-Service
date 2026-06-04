from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import engine, Base
from app.api.batches import router as batches_router

# IMPORTANT:
# Import models so SQLAlchemy registers them
from app.models.batch import Batch
from app.models.batch_item import BatchItem


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs when FastAPI starts.
    Creates database tables automatically.
    """

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(
    title="Batch Processing Service",
    lifespan=lifespan
)

# Register API Router
app.include_router(batches_router)


@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "batch-processing-service"
    }
