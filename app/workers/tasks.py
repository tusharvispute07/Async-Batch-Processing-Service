from app.models import batch_item
import asyncio
import random
from datetime import (
    datetime,
    timedelta
)

from sqlalchemy import select
from sqlalchemy.orm import (
    selectinload
)

from app.workers.celery_app import (
    celery
)
from app.core.database import (
    AsyncSessionLocal
)
from app.models.batch_item import (
    BatchItem
)
from app.models.batch import (
    Batch
)
from app.services.vendor import (
    analyze_text
)
from app.core.exceptions import (
    VendorRateLimitError,
    VendorServerError,
    VendorTimeoutError
)
from app.core.constants import (
    MAX_RETRIES,
    BASE_BACKOFF,
    MAX_BACKOFF,
    MAX_CONCURRENT_REQUESTS
)
from app.services.rate_limit import (
    acquire_token
)


PROCESSING_TIMEOUT_MINUTES = 5


async def process_item(
    item_id: int
):
    async with (
        AsyncSessionLocal()
        as db
    ):

        result = await db.execute(
            select(BatchItem)
            .options(
                selectinload(
                    BatchItem.batch
                )
            )
            .where(
                BatchItem.id
                == item_id
            )
        )

        item = (
            result.scalar_one()
        )

        # Already completed
        if (
            item.status
            == "completed"
        ):
            return

        # Already processing
        if (
            item.status
            == "processing"
        ):

            if (
                item.processing_started_at
                and
                datetime.utcnow()
                -
                item.processing_started_at
                <
                timedelta(
                    minutes=
                    PROCESSING_TIMEOUT_MINUTES
                )
            ):
                print(
                    f"Skipping "
                    f"{item.id}, "
                    f"already processing"
                )
                return

        attempt = (
            item.attempt_count
            or 0
        )

        while (
            attempt
            < MAX_RETRIES
        ):

            try:

                await acquire_token(
                    item.batch
                    .tenant_id
                )

                # Mark processing
                item.status = (
                    "processing"
                )

                item.processing_started_at = (
                    datetime.utcnow()
                )

                await db.commit()

                response = (
                    await analyze_text(
                        item.text
                    )
                )

                item.result = (
                    response[
                        "analysis"
                    ]
                )

                item.status = (
                    "completed"
                )

                item.processing_started_at = (
                    None
                )

                await db.commit()

                return

            except (
                VendorRateLimitError
            ) as e:

                attempt += 1

                item.attempt_count = (
                    attempt
                )

                item.last_error = (
                    str(e)
                )

                await db.commit()

                print(
                    f"429 retrying "
                    f"after "
                    f"{e.retry_after}"
                    f"s"
                )

                await asyncio.sleep(
                    e.retry_after
                )

            except (
                VendorServerError,
                VendorTimeoutError
            ) as e:

                attempt += 1

                item.attempt_count = (
                    attempt
                )

                item.last_error = (
                    str(e)
                )

                await db.commit()

                exponential_backoff = min(
                    BASE_BACKOFF
                    ** attempt,
                    MAX_BACKOFF
                )

                jitter = (
                    random.uniform(
                        0,
                        1
                    )
                )

                wait_time = (
                    exponential_backoff
                    + jitter
                )

                print(
                    f"Retry "
                    f"{attempt} "
                    f"in "
                    f"{wait_time:.2f}s"
                )

                await asyncio.sleep(
                    wait_time
                )

        # Permanent failure
        item.status = (
            "failed"
        )

        item.processing_started_at = (
            None
        )

        await db.commit()


async def update_batch_status(
    db,
    batch_id
):
    batch_result = (
        await db.execute(
            select(Batch)
            .where(
                Batch.id
                == batch_id
            )
        )
    )

    batch = (
        batch_result
        .scalar_one()
    )

    completed_result = (
        await db.execute(
            select(BatchItem)
            .where(
                BatchItem.batch_id
                == batch_id,
                BatchItem.status
                == "completed"
            )
        )
    )

    failed_result = (
        await db.execute(
            select(BatchItem)
            .where(
                BatchItem.batch_id
                == batch_id,
                BatchItem.status
                == "failed"
            )
        )
    )

    batch.done = len(
        completed_result
        .scalars()
        .all()
    )

    batch.failed = len(
        failed_result
        .scalars()
        .all()
    )

    total_finished = (
        batch.done
        + batch.failed
    )

    if (
        total_finished
        == batch.total
    ):

        if (
            batch.failed > 0
        ):
            batch.status = (
                "partially_failed"
            )
        else:
            batch.status = (
                "completed"
            )

    else:
        batch.status = (
            "processing"
        )

    await db.commit()


async def process_chunk_async(
    item_ids
):
    async with (
        AsyncSessionLocal()
        as db
    ):

        result = (
            await db.execute(
                select(BatchItem)
                .where(
                    BatchItem.id.in_(
                        item_ids
                    )
                )
            )
        )

        items = (
            result.scalars()
            .all()
        )

        semaphore = (
            asyncio.Semaphore(
                MAX_CONCURRENT_REQUESTS
            )
        )

        async def process_with_limit(
            item
        ):
            async with (
                semaphore
            ):
                await process_item(
                    item.id
                )

        await asyncio.gather(
            *[
                process_with_limit(
                    item
                )
                for item
                in items
            ]
        )

        if items:
            await (
                update_batch_status(
                    db,
                    items[0]
                    .batch_id
                )
            )


@celery.task
def process_chunk(
    item_ids
):
    asyncio.run(
        process_chunk_async(
            item_ids
        )
    )