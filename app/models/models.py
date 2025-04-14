from sqlmodel import Field, Relationship
from ..schemas.schemas import ReservationBase, TableBase


class Reservation(ReservationBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    table: "Table" = Relationship(back_populates="reservations")


class Table(TableBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    reservations: list[Reservation] = Relationship(back_populates="table")
