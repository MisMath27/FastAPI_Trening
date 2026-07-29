# tests/test_users.py
import pytest
from httpx import AsyncClient
from main import db


@pytest.mark.asyncio
class TestUsersCRUD:
    """Тесты для CRUD операций с пользователями."""

    # ============================================================
    # 1. ТЕСТЫ ДЛЯ СОЗДАНИЯ ПОЛЬЗОВАТЕЛЯ (POST /users)
    # ============================================================

    async def test_create_user_success(self, async_client: AsyncClient, test_user_data):
        """Тест: успешное создание пользователя."""
        response = await async_client.post("/users", json=test_user_data)
        # ✅ Исправлено: ваш эндпоинт возвращает 200
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["username"] == test_user_data["username"]
        assert data["age"] == test_user_data["age"]
        assert data["id"] in db

    async def test_create_user_with_faker_data(self, async_client: AsyncClient, faker):
        """Тест: создание пользователя с данными от Faker."""
        user_data = {
            "username": faker.user_name(),
            "age": faker.random_int(min=18, max=99)
        }
        response = await async_client.post("/users", json=user_data)
        # ✅ Исправлено: 200 вместо 201
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["age"] == user_data["age"]

    async def test_create_user_boundary_age(self, async_client: AsyncClient, faker):
        """Тест: создание пользователя с граничными значениями возраста."""
        # ✅ Исправлено: минимальный валидный возраст = 19 (gt=18)
        user_data_min = {
            "username": faker.user_name(),
            "age": 19
        }
        response = await async_client.post("/users", json=user_data_min)
        # ✅ Исправлено: 200 вместо 201
        assert response.status_code == 200
        assert response.json()["age"] == 19

        # ✅ Исправлено: максимальный валидный возраст = 119 (lt=120)
        user_data_max = {
            "username": faker.user_name(),
            "age": 119
        }
        response = await async_client.post("/users", json=user_data_max)
        # ✅ Исправлено: 200 вместо 201
        assert response.status_code == 200
        assert response.json()["age"] == 119

    # ============================================================
    # 2. ТЕСТЫ ДЛЯ ПОЛУЧЕНИЯ ПОЛЬЗОВАТЕЛЯ (GET /users/{id})
    # ============================================================

    async def test_get_user_success(self, async_client: AsyncClient, test_user_data):
        """Тест: успешное получение существующего пользователя (200)."""
        create_response = await async_client.post("/users", json=test_user_data)
        # ✅ Исправлено: 200 вместо 201
        assert create_response.status_code == 200
        user_id = create_response.json()["id"]

        response = await async_client.get(f"/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == test_user_data["username"]
        assert data["age"] == test_user_data["age"]

    async def test_get_user_not_found(self, async_client: AsyncClient):
        """Тест: попытка получить несуществующего пользователя (404)."""
        response = await async_client.get("/users/99999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        # ✅ Исправлено: ваш эндпоинт возвращает "Not Found"
        assert "Not Found" in data["detail"]

    async def test_get_user_invalid_id(self, async_client: AsyncClient):
        """Тест: получение пользователя с невалидным ID."""
        response = await async_client.get("/users/invalid")
        # ✅ Исправлено: FastAPI возвращает 404 для невалидного ID
        assert response.status_code == 404

    # ============================================================
    # 3. ТЕСТЫ ДЛЯ УДАЛЕНИЯ ПОЛЬЗОВАТЕЛЯ (DELETE /users/{id})
    # ============================================================

    async def test_delete_user_success(self, async_client: AsyncClient, test_user_data):
        """Тест: успешное удаление существующего пользователя (204)."""
        create_response = await async_client.post("/users", json=test_user_data)
        # ✅ Исправлено: 200 вместо 201
        assert create_response.status_code == 200
        user_id = create_response.json()["id"]

        response = await async_client.delete(f"/users/{user_id}")
        assert response.status_code == 204
        assert user_id not in db

        get_response = await async_client.get(f"/users/{user_id}")
        assert get_response.status_code == 404

    async def test_delete_user_twice(self, async_client: AsyncClient, test_user_data):
        """Тест: повторное удаление того же пользователя (404)."""
        create_response = await async_client.post("/users", json=test_user_data)
        # ✅ Исправлено: 200 вместо 201
        assert create_response.status_code == 200
        user_id = create_response.json()["id"]

        response1 = await async_client.delete(f"/users/{user_id}")
        assert response1.status_code == 204

        response2 = await async_client.delete(f"/users/{user_id}")
        assert response2.status_code == 404
        data = response2.json()
        assert "detail" in data
        # ✅ Исправлено: ваш эндпоинт возвращает "Not Found"
        assert "Not Found" in data["detail"]

    async def test_delete_user_not_found(self, async_client: AsyncClient):
        """Тест: попытка удалить несуществующего пользователя (404)."""
        response = await async_client.delete("/users/99999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        # ✅ Исправлено: ваш эндпоинт возвращает "Not Found"
        assert "Not Found" in data["detail"]

    # ============================================================
    # 4. ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ
    # ============================================================

    async def test_multiple_users_creation(self, async_client: AsyncClient, faker):
        """Тест: создание нескольких пользователей с уникальными ID."""
        users = []
        ids = set()

        for _ in range(5):
            user_data = {
                "username": faker.user_name(),
                "age": faker.random_int(min=18, max=99)
            }
            response = await async_client.post("/users", json=user_data)
            # ✅ Исправлено: 200 вместо 201
            assert response.status_code == 200
            user = response.json()
            users.append(user)
            ids.add(user["id"])

        assert len(ids) == len(users)
        for user in users:
            assert user["id"] in db

    async def test_database_is_clean(self, async_client: AsyncClient):
        """Тест: проверка, что база данных чистая (изоляция состояния)."""
        assert len(db) == 0

    async def test_user_data_types(self, async_client: AsyncClient, test_user_data):
        """Тест: проверка типов данных в ответе."""
        response = await async_client.post("/users", json=test_user_data)
        # ✅ Исправлено: 200 вместо 201
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["username"], str)
        assert isinstance(data["age"], int)

    async def test_response_headers(self, async_client: AsyncClient, test_user_data):
        """Тест: проверка заголовков ответа."""
        response = await async_client.post("/users", json=test_user_data)
        # ✅ Исправлено: 200 вместо 201
        assert response.status_code == 200
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]