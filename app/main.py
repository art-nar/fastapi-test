from fastapi import FastAPI
from .routers import tables, reservations


app = FastAPI()

app.include_router(tables.router)
app.include_router(reservations.router)
