from fastapi import (
    APIRouter,
    Header,
    Depends
)
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.batch import (
    BatchRequest,
    BatchStatusResponse,
    BatchResultsResponse,
    BatchFailuresResponse
)
from app.services.batches import (
    create_batch_service,
    get_batch_status_service,
    get_batch_results_service,
    get_batch_failures_service
)


router = APIRouter()


@router.post("/batches")
async def create_batch(
    request: BatchRequest,
    x_tenant_id: str = Header(...),
    idempotency_key: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    return await create_batch_service(
        request=request,
        tenant_id=x_tenant_id,
        idempotency_key=idempotency_key,
        db=db
    )

@router.get(
    "/batches/{batch_id}",
    response_model=BatchStatusResponse
)
async def get_batch_status(
    batch_id: UUID,
    x_tenant_id: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    return await get_batch_status_service(
        batch_id=batch_id,
        tenant_id=x_tenant_id,
        db=db
    )

@router.get(
    "/batches/{batch_id}/results",
    response_model=BatchResultsResponse
)
async def get_batch_results(
    batch_id: UUID,
    x_tenant_id: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    return await get_batch_results_service(
        batch_id=batch_id,
        tenant_id=x_tenant_id,
        db=db
    )


@router.get(
    "/batches/{batch_id}/failures",
    response_model=BatchFailuresResponse
)
async def get_batch_failures(
    batch_id: UUID,
    x_tenant_id: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    return await get_batch_failures_service(
        batch_id=batch_id,
        tenant_id=x_tenant_id,
        db=db
    )