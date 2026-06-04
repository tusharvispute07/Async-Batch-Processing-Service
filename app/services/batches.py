from app.core.constants import CHUNK_SIZE
import hashlib
import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.batch import Batch
from app.models.batch_item import BatchItem
from app.schemas.batch import BatchRequest
from app.core.constants import CHUNK_SIZE
from app.workers.tasks import process_chunk


def generate_payload_hash(payload: dict):
    payload_string = json.dumps(
        payload,
        sort_keys=True
    )

    return hashlib.sha256(
        payload_string.encode()
    ).hexdigest()


async def create_batch_service(
    request: BatchRequest,
    tenant_id: str,
    idempotency_key: str,
    db: AsyncSession
):

    payload_hash = generate_payload_hash(
        request.model_dump()
    )

    # Check idempotency
    result = await db.execute(
        select(Batch).where(
            Batch.tenant_id == tenant_id,
            Batch.idempotency_key == idempotency_key
        )
    )

    existing_batch = result.scalar_one_or_none()

    if existing_batch:

        # Same key + different payload
        if existing_batch.payload_hash != payload_hash:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Idempotency key already "
                    "used with different payload"
                )
            )

        # Same request
        return {
            "batch_id": str(existing_batch.id)
        }

    # Create batch
    batch = Batch(
        tenant_id=tenant_id,
        idempotency_key=idempotency_key,
        payload_hash=payload_hash,
        status="pending",
        total=len(request.items)
    )

    db.add(batch)

    # Needed to generate batch.id
    await db.flush()

    batch_items = [
        BatchItem(
            batch_id=batch.id,
            text=item
        )
        for item in request.items
    ]

    db.add_all(batch_items)

    await db.commit()

    item_ids = [
        item.id
        for item in batch_items
    ]

    for i in range(
        0,
        len(item_ids),
        CHUNK_SIZE
    ):
        chunk = item_ids[i:i + CHUNK_SIZE]

        process_chunk.delay(chunk)

    return {
        "batch_id": str(batch.id)
    }


async def get_batch_status_service(
    batch_id,
    tenant_id,
    db
):

    result = await db.execute(
        select(Batch).where(
            Batch.id == batch_id,
            Batch.tenant_id == tenant_id
        )
    )

    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=404,
            detail="Batch not found"
        )

    return {
        "batch_id": batch.id,
        "status": batch.status,
        "total": batch.total,
        "done": batch.done,
        "failed": batch.failed
    }


async def get_batch_results_service(
    batch_id,
    tenant_id,
    db
):

    # Verify tenant owns batch
    batch_result = await db.execute(
        select(Batch).where(
            Batch.id == batch_id,
            Batch.tenant_id == tenant_id
        )
    )

    batch = batch_result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=404,
            detail="Batch not found"
        )

    # Get completed items
    result = await db.execute(
        select(BatchItem).where(
            BatchItem.batch_id == batch_id,
            BatchItem.status == "completed"
        )
    )

    items = result.scalars().all()

    return {
        "results": [
            {
                "item_id": item.id,
                "text": item.text,
                "result": item.result
            }
            for item in items
        ]
    }

async def get_batch_failures_service(
    batch_id,
    tenant_id,
    db
):

    # Verify ownership
    batch_result = await db.execute(
        select(Batch).where(
            Batch.id == batch_id,
            Batch.tenant_id == tenant_id
        )
    )

    batch = batch_result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=404,
            detail="Batch not found"
        )

    # Get failed items
    result = await db.execute(
        select(BatchItem).where(
            BatchItem.batch_id == batch_id,
            BatchItem.status == "failed"
        )
    )

    items = result.scalars().all()

    return {
        "failures": [
            {
                "item_id": item.id,
                "text": item.text,
                "attempt_count": item.attempt_count,
                "last_error": item.last_error
            }
            for item in items
        ]
    }