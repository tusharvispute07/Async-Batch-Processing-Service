import time
import asyncio

from app.core.redis import (
    redis_client
)


TENANT_LIMITS = {
    "company_1": {
        "capacity": 5,
        "refill_rate": 1
    },
    "company_2": {
        "capacity": 10,
        "refill_rate": 2
    }
}


TOKEN_BUCKET_SCRIPT = """
    local key = KEYS[1]

    local capacity = tonumber(ARGV[1])
    local refill_rate = tonumber(ARGV[2])
    local now = tonumber(ARGV[3])

    local bucket = redis.call(
        'HMGET',
        key,
        'tokens',
        'timestamp'
    )

    local tokens = tonumber(bucket[1])
    local last_timestamp =
        tonumber(bucket[2])

    if tokens == nil then
        tokens = capacity
        last_timestamp = now
    end

    local elapsed =
        math.max(
            0,
            now - last_timestamp
        )

    local refill =
        elapsed * refill_rate

    tokens =
        math.min(
            capacity,
            tokens + refill
        )

    if tokens < 1 then

        redis.call(
            'HMSET',
            key,
            'tokens',
            tokens,
            'timestamp',
            now
        )

        return 0
    end

    tokens = tokens - 1

    redis.call(
        'HMSET',
        key,
        'tokens',
        tokens,
        'timestamp',
        now
    )

    return 1
    """


async def acquire_token(
    tenant_id: str
):

    config = TENANT_LIMITS.get(
        tenant_id,
        {
            "capacity": 5,
            "refill_rate": 1
        }
    )

    bucket_key = (
        f"bucket:{tenant_id}"
    )

    while True:

        allowed = (
            await redis_client.eval(
                TOKEN_BUCKET_SCRIPT,
                1,
                bucket_key,
                config["capacity"],
                config[
                    "refill_rate"
                ],
                time.time()
            )
        )

        if allowed == 1:
            return

        await asyncio.sleep(1)