from datetime import timedelta
from typing import Callable
from functools import wraps
from datetimerange import DateTimeRange
from fastapi import HTTPException
from sqlmodel import Session, select
from ..models.models import Reservation
from ..schemas.schemas import ReservationCreate
from ..database.db import get_session


# Проверка на пересечение брони
def check_reservation_conflict(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        print(f'Arguments passed: {args} as {type(args)}')
        print(f'Arguments passed: {kwargs} as {type(kwargs)}')
        reservation_data: ReservationCreate = kwargs.get("reservation_data")
        session: Session = kwargs.get("session")

        if session is None:
            session = next(get_session())

        new_start = reservation_data.reservation_time + timedelta(seconds=1)
        new_end = new_start + timedelta(
            minutes=(reservation_data.duration_minutes - 1), seconds=58
        )
        new_range = DateTimeRange(new_start, new_end)

        existing_reservations = session.exec(
            select(Reservation).where(Reservation.table_id == reservation_data.table_id)
        ).all()

        for existing in existing_reservations:
            existing_start = existing.reservation_time
            existing_end = existing_start + timedelta(minutes=existing.duration_minutes)
            existing_range = DateTimeRange(existing_start, existing_end)

            if new_range.is_intersection(existing_range):
                raise HTTPException(
                    status_code=409,
                    detail="Время брони пересекается с существующей бронью",
                )

        return await func(*args, **kwargs)

    return wrapper
