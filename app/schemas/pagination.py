from pydantic import BaseModel


class Pagination(BaseModel):
    limit: int
    page: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class Page[T](BaseModel):
    items: list[T]
    total: int
