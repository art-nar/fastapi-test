from typing import Annotated, Sequence
from datetime import datetime
from fastapi import HTTPException, Path, Query, Depends, Response, APIRouter
from sqlmodel import Session, select
from ..models.models import Reservation
from ..schemas.schemas import ReservationCreate
from ..database.db import get_session
from ..utils.utils import check_reservation_conflict

router = APIRouter()


#  GET все брони
@router.get("/api/v1/reservations/")
async def read_reservations(
    table_id: Annotated[int | None, Query(title="Фильтр по ID столика")] = None,
    customer_name: Annotated[
        str | None, Query(max_length=50, title="Фильтр по имени клиента")
    ] = None,
    reservation_time: Annotated[
        str | None, Query(title="Фильтр по дате и времени брони")
    ] = None,
    session: Session = Depends(get_session),
) -> list[Reservation]:
    reservation_list: Sequence[Reservation] = session.exec(select(Reservation)).all()

    # Фильтр по ID столика
    if table_id is not None:
        reservation_list = [r for r in reservation_list if r.table_id == table_id]

    # Фильтр по имени клиента
    if customer_name:
        reservation_list = [
            r
            for r in reservation_list
            if customer_name.lower() in r.customer_name.lower()
        ]

    # Фильтр по дате и времени брони
    if reservation_time:
        reservation_list = [
            r
            for r in reservation_list
            if reservation_time in r.reservation_time.strftime("%Y-%m-%d, T%H:%M")
        ]
    return reservation_list


# POST создание брони
@router.post("/api/v1/reservations/")
@check_reservation_conflict
async def create_reservation(
    reservation_data: ReservationCreate, session: Session = Depends(get_session)
) -> Reservation:
    print(type(session))
    reservation = Reservation(
        table_id=reservation_data.table_id,
        customer_name=reservation_data.customer_name,
        reservation_time=reservation_data.reservation_time,
        duration_minutes=reservation_data.duration_minutes,
    )
    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    return reservation


# DELETE удаление брони
@router.delete("/api/v1/reservations/{reservation_id}/")
async def delete_reservation(
    reservation_id: Annotated[int, Path(title="ID бронирования")],
    session: Session = Depends(get_session),
) -> dict:
    reservation: Reservation | None = session.get(Reservation, reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Бронь не найдена")
    session.delete(reservation)
    session.commit()
    return Response(status_code=204)
