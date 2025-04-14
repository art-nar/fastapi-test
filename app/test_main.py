import pytest
from sqlmodel import SQLModel, create_engine, Session
from httpx import AsyncClient, ASGITransport

from .main import app
from .database.db import get_session

# Тестовая БД (in-memory SQLite)
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


# Создание тестовой сессии
def override_get_session():
    with Session(engine) as session:
        yield session


# Подменяем сессию в зависимости
app.dependency_overrides[get_session] = override_get_session

transport = ASGITransport(app=app)

### ТЕСТЫ С ВАЛИДНЫМИ ДАННЫМИ ###


@pytest.fixture(scope="module", autouse=True)
def prepare_database():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_read_tables():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/tables/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_read_table_by_id():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        post_response = await ac.post(
            "/api/v1/tables/",
            json={"name": "Cтолик 2", "location": "терраса", "seats": 4},
        )
        table_id = post_response.json()["id"]

        response = await ac.get(f"/api/v1/tables/{table_id}/")
        assert response.status_code == 200
        assert response.json()["id"] == table_id


@pytest.mark.asyncio
async def test_create_table():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/tables/",
            json={"name": "Cтолик 1", "location": "Терраса", "seats": 4},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Cтолик 1"
        assert data["location"] == "Терраса"
        assert data["seats"] == 4


@pytest.mark.asyncio
async def test_delete_table():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        post_response = await ac.post(
            "/api/v1/tables/",
            json={"name": "Cтолик 4", "location": "зал у окна", "seats": 10},
        )
        table_id = post_response.json()["id"]

        delete = await ac.delete(f"/api/v1/tables/{table_id}/")
        assert delete.status_code == 204


@pytest.mark.asyncio
async def test_create_reservation():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        post_response = await ac.post(
            "/api/v1/tables/",
            json={"name": "Cтолик 4", "location": "подвал", "seats": 6},
        )
        table_id = post_response.json()["id"]

        response = await ac.post(
            "/api/v1/reservations/",
            json={
                "table_id": table_id,
                "customer_name": "Сергей",
                "reservation_time": "2025-04-13T15:00:00",
                "duration_minutes": 60,
            },
        )
        assert response.status_code == 200
        assert response.json()["customer_name"] == "Сергей"


@pytest.mark.asyncio
async def test_delete_reservation():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        table_post = await ac.post(
            "/api/v1/tables/",
            json={"name": "Cтолик 5", "location": "зал у окна", "seats": 4},
        )
        table_id = table_post.json()["id"]

        reservation_post = await ac.post(
            "/api/v1/reservations/",
            json={
                "table_id": table_id,
                "customer_name": "Иван",
                "reservation_time": "2025-05-01T18:00:00",
                "duration_minutes": 60,
            },
        )
        reservation_id = reservation_post.json()["id"]

        delete = await ac.delete(f"/api/v1/reservations/{reservation_id}/")
        assert delete.status_code == 204


### ТЕСТЫ С НЕВАЛИДНЫМИ ДАННЫМИ ###


@pytest.mark.asyncio
async def test_delete_reservation_not_found():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.delete("/api/v1/reservations/999999/")
        assert response.status_code == 404
        assert response.json()["detail"] == "Бронь не найдена"


@pytest.mark.asyncio
async def test_delete_table_not_found():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.delete("/api/v1/tables/999999/")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_table_invalid_id_type():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.delete("/api/v1/tables/not-an-id/")
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_location_param_in_filter():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/tables/?location=гардероб")
        assert response.status_code == 422
        response = await ac.get("/api/v1/tables/?location=крышка")
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_name_param_too_long():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/tables/?name=" + "a" * 50)
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_location_not_in_enum():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/tables/",
            json={"name": "Cтолик 1", "location": "гардероб", "seats": 4},
        )
        assert response.status_code == 422
        assert response.json()["detail"][0]["msg"] =="Input should be 'Терраса', 'Подвал', 'Зал у окна' or 'Крыша'"


### ПРОВЕРКА ВАЛИДАЦИИ ДАННЫХ И РАБОТЫ ДЕКОРАТОРОВ


@pytest.mark.asyncio
async def test_check_reservation_conflict():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        post_response = await ac.post(
            "/api/v1/tables/",
            json={"name": "Cтолик 4", "location": "подвал", "seats": 6},
        )
        table_id = post_response.json()["id"]

        reservation_1 = await ac.post(
            "/api/v1/reservations/",
            json={
                "table_id": table_id,
                "customer_name": "Сергей",
                "reservation_time": "2025-04-13T15:00:00",
                "duration_minutes": 60,
            },
        )

        reservation_2 = await ac.post(
            "/api/v1/reservations/",
            json={
                "table_id": table_id,
                "customer_name": "Сергей",
                "reservation_time": "2025-04-13T14:00:00",
                "duration_minutes": 60,
            },
        )

        response_conflict_1 = await ac.post(
            "/api/v1/reservations/",
            json={
                "table_id": table_id,
                "customer_name": "Сергей",
                "reservation_time": "2025-04-13T15:59:59",
                "duration_minutes": 60,
            },
        )

        assert response_conflict_1.status_code == 409
        assert (
            response_conflict_1.json()["detail"]
            == "Время брони пересекается с существующей бронью"
        )

        response_conflict_2 = await ac.post(
            "/api/v1/reservations/",
            json={
                "table_id": table_id,
                "customer_name": "Сергей",
                "reservation_time": "2025-04-13T13:01:00",
                "duration_minutes": 60,
            },
        )
        assert response_conflict_2.status_code == 409
        assert (
            response_conflict_2.json()["detail"]
            == "Время брони пересекается с существующей бронью"
        )


@pytest.mark.asyncio
async def test_customer_name_in_title_case():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        post_response = await ac.post(
            "/api/v1/tables/",
            json={"name": "Cтолик 4", "location": "подвал", "seats": 6},
        )
        table_id = post_response.json()["id"]

        response = await ac.post(
            "/api/v1/reservations/",
            json={
                "table_id": table_id,
                "customer_name": "гРиШанЯ ЛюТЫй",
                "reservation_time": "2025-04-13T15:00:00",
                "duration_minutes": 60,
            },
        )
        assert response.json()["customer_name"] == "Гришаня Лютый"


@pytest.mark.asyncio
async def test_location_in_capitalize():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/tables/",
            json={"name": "Cтолик 1", "location": "терраса", "seats": 4},
        )
        data = response.json()
        assert data["location"] == "Терраса"
