from typing import Annotated, Sequence
from fastapi import HTTPException, Path, Query, Depends, Response, APIRouter
from sqlmodel import Session, select
from ..schemas.schemas import TableCreate
from ..schemas.choices import LocationURLChoices
from ..models.models import Table
from ..database.db import get_session

router = APIRouter()


#  GET все столики
@router.get("/api/v1/tables/")
async def read_tables(
    location: Annotated[
        LocationURLChoices | None, Query(title="Фильтр по локации (выбор из списка)")
    ] = None,
    name: Annotated[
        str | None, Query(max_length=10, title="Фильтр по наименованию столика")
    ] = None,
    has_reservations: Annotated[
        bool | None, Query(title="Фильтр по наличию броней")
    ] = False,
    session: Session = Depends(get_session),
) -> list[Table]:
    table_list: Sequence[Table] = session.exec(select(Table)).all()

    # фильтр по локации
    if location:
        table_list = [
            t for t in table_list if t.location.value.lower() == location.value
        ]

    # фильтр по наименованию столика
    if name:
        table_list = [t for t in table_list if name.lower() in t.name.lower()]

    # фильтр по наличию броней
    if has_reservations:
        table_list = [t for t in table_list if len(t.reservations) > 0]
    return table_list


# GET столик по ID
@router.get("/api/v1/tables/{table_id}/")
async def read_table(
    table_id: Annotated[int, Path(title="ID столика")],
    session: Session = Depends(get_session),
) -> Table:
    table: Table | None = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Стол не найден")
    return table


# POST создание столика
@router.post("/api/v1/tables/")
async def create_table(
    table_data: TableCreate, session: Session = Depends(get_session)
) -> Table:
    table = Table(
        name=table_data.name,
        location=table_data.location,
        seats=table_data.seats,
    )
    session.add(table)
    session.commit()
    session.refresh(table)
    return table


# DELETE удаление столика
@router.delete("/api/v1/tables/{table_id}/")
async def delete_table(
    table_id: Annotated[int, Path(title="ID столика")],
    session: Session = Depends(get_session),
) -> dict:
    table: Table | None = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Стол не найден")
    session.delete(table)
    session.commit()
    return Response(status_code=204)
