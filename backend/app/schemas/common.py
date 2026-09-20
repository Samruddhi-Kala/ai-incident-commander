import math
from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number starting at 1")
    page_size: int = Field(20, ge=1, le=100, description="Number of items per page (max 100)")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    page: int
    page_size: int
    total: int
    total_pages: int

    @classmethod
    def create(cls, items: List[T], page: int, page_size: int, total: int):
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return cls(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )
