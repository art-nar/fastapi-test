from datetime import datetime
from pydantic import field_validator
from sqlmodel import SQLModel, Field
from .choices import LocationChoices


class ReservationBase(SQLModel):
    table_id: int | None = Field(foreign_key="table.id")
    customer_name: str
    reservation_time: datetime
    duration_minutes: int


class ReservationCreate(ReservationBase):
    @field_validator("customer_name", mode="before")
    @classmethod
    def title_case_location(cls, value) -> str:
        return value.title()


class TableBase(SQLModel):
    name: str
    seats: int
    location: LocationChoices


class TableCreate(TableBase):
    @field_validator("location", mode="before")
    @classmethod
    def capitalize_case_location(cls, value) -> str:
        return value.capitalize() if isinstance(value, str) else value.value
