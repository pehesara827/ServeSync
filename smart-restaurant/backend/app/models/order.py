"""Order data model definitions shared by routers and services."""
from pydantic import BaseModel, Field


class OrderItemIn(BaseModel):
    item_name: str = Field(min_length=1)
    price: int = Field(ge=0)
    quantity: int = Field(gt=0)


class OrderItemOut(OrderItemIn):
    id: int


class OrderCreate(BaseModel):
    table_number: int = Field(gt=0)
    status: str = "pending"
    items: list[OrderItemIn] = []


class StatusUpdate(BaseModel):
    status: str


class OrderOut(BaseModel):
    id: int
    table_number: int
    status: str
    created_at: str | None = None
    items: list[OrderItemOut] = []
    total: int = 0
