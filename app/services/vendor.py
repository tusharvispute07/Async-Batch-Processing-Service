import asyncio
import random

from app.core.exceptions import (
    VendorRateLimitError,
    VendorServerError,
    VendorTimeoutError
)


async def analyze_text(
    text: str
):

    # Simulate latency
    await asyncio.sleep(
        random.uniform(1, 3)
    )

    random_number = random.random()

    # 10% chance → 429
    if random_number < 0.10:
        raise VendorRateLimitError(
            retry_after=3
        )

    # 10% chance → 500
    if random_number < 0.20:
        raise VendorServerError(
            "Vendor internal error"
        )

    # 5% chance → timeout
    if random_number < 0.25:
        raise VendorTimeoutError(
            "Vendor timeout"
        )

    # Success
    return {
        "analysis": (
            f"Analyzed: {text}"
        )
    }