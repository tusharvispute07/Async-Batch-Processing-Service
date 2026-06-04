from uuid import UUID
from pydantic import BaseModel
from typing import List


class BatchRequest(BaseModel):
    items: List[str]


class BatchStatusResponse(BaseModel):
    batch_id: UUID
    status: str
    total: int
    done: int
    failed: int

class BatchResultItem(BaseModel):
    item_id: UUID
    text: str
    result: str


class BatchResultsResponse(BaseModel):
    results: list[BatchResultItem]


class FailureItem(BaseModel):
    item_id: UUID
    text: str
    attempt_count: int
    last_error: str


class BatchFailuresResponse(BaseModel):
    failures: list[FailureItem]