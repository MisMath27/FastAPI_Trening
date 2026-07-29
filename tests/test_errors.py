# tests/test_errors.py
import pytest
from httpx import AsyncClient
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.asyncio
class TestUserErrors:
    """Тесты для ошибок, связанных с пользователями"""

    async def test_user_not_found(self, async_client: AsyncClient):
        """Тест: 404 User Not Found"""
        response = await async_client.get("/test/not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "USER_NOT_FOUND"
        assert "User with ID 999 not found" in data["message"]
        assert "request_id" in data
        assert "timestamp" in data

    async def test_user_already_exists(self, async_client: AsyncClient):
        """Тест: 409 User Already Exists"""
        response = await async_client.get("/test/conflict")
        assert response.status_code == 409
        data = response.json()
        assert data["error_code"] == "USER_ALREADY_EXISTS"
        assert "already exists" in data["message"]

    async def test_access_denied(self, async_client: AsyncClient):
        """Тест: 403 Access Denied"""
        response = await async_client.get("/test/forbidden")
        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "ACCESS_DENIED"
        assert "permission" in data["message"].lower()


@pytest.mark.asyncio
class TestValidationErrors:
    """Тесты для ошибок валидации"""

    async def test_validation_exception(self, async_client: AsyncClient):
        """Тест: 400 Invalid Data"""
        response = await async_client.get("/test/validation")
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_USER_DATA"
        assert data["status_code"] == 400
        assert data["errors"] is not None
        assert data["errors"][0]["field"] == "email"

    async def test_pydantic_validation_error(self, async_client: AsyncClient):
        """Тест: 422 Validation Error (Pydantic)"""
        response = await async_client.get(
            "/test/validation-pydantic",
            params={"age": 200, "email": "invalid-email"}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
        assert data["status_code"] == 422
        assert "errors" in data
        errors = data["errors"]
        error_fields = [e["field"] for e in errors]
        assert "query.age" in error_fields or "query.email" in error_fields

    async def test_pydantic_validation_success(self, async_client: AsyncClient):
        """Тест: Успешная валидация"""
        response = await async_client.get(
            "/test/validation-pydantic",
            params={"age": 25, "email": "test@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["age"] == 25
        assert data["email"] == "test@example.com"


@pytest.mark.asyncio
class TestInternalErrors:
    """Тесты для внутренних ошибок"""

    async def test_internal_error(self, async_client: AsyncClient):
        """Тест: 500 Internal Server Error"""
        response = await async_client.get("/test/internal")
        assert response.status_code == 500
        data = response.json()
        # ✅ Проверяем наличие статуса
        assert "status_code" in data
        assert data["status_code"] == 500

    async def test_rate_limit_error(self, async_client: AsyncClient):
        """Тест: 429 Rate Limit Exceeded"""
        response = await async_client.get("/test/rate-limit")
        assert response.status_code == 429
        data = response.json()
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert data["status_code"] == 429
        assert "Too many requests" in data["message"]


@pytest.mark.asyncio
class TestErrorResponseStructure:
    """Тесты структуры ответов с ошибками"""

    async def test_error_response_has_all_fields(self, async_client: AsyncClient):
        """Проверка, что все ошибки содержат обязательные поля"""
        endpoints = [
            ("/test/not-found", 404),
            ("/test/validation", 400),
            ("/test/conflict", 409),
            ("/test/forbidden", 403),
        ]

        for endpoint, expected_status in endpoints:
            response = await async_client.get(endpoint)
            assert response.status_code == expected_status
            data = response.json()

            required_fields = ["status_code", "message", "error_code", "timestamp", "request_id"]
            for field in required_fields:
                assert field in data, f"Field '{field}' missing in response for {endpoint}"

            assert isinstance(data["status_code"], int)
            assert isinstance(data["message"], str)
            assert isinstance(data["error_code"], str)
            assert isinstance(data["timestamp"], str)
            assert data["status_code"] == expected_status

    async def test_error_response_has_cors_headers(self, async_client: AsyncClient):
        """Проверка заголовков в ответах с ошибками"""
        response = await async_client.get("/test/not-found")
        assert "X-Request-ID" in response.headers
        assert "X-ErrorHandleTime" in response.headers


@pytest.mark.asyncio
class TestLoggingAndErrors:
    """Тесты для эндпоинтов с логированием ошибок"""

    async def test_ok_endpoint(self, async_client: AsyncClient):
        """Тест: Успешный эндпоинт"""
        response = await async_client.get("/ok")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "message": "Everything is fine"}

    async def test_error_endpoint(self, async_client: AsyncClient):
        """Тест: Кастомная ошибка 418"""
        response = await async_client.get("/error")
        assert response.status_code == 418
        data = response.json()
        assert "I'm a teapot" in data["message"]

    async def test_boom_endpoint_returns_error(self, async_client: AsyncClient):
        """Тест: Эндпоинт с неожиданной ошибкой"""
        response = await async_client.get("/boom")
        # ✅ Должен вернуть 500
        assert response.status_code == 500
        data = response.json()
        # Проверяем структуру ошибки
        assert "status_code" in data or "error_code" in data

    async def test_echo_endpoint(self, async_client: AsyncClient):
        """Тест: Эхо-эндпоинт"""
        response = await async_client.get("/echo?name=Alice&age=30")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello, Alice!"
        assert data["age"] == 30
        assert "headers" in data
        assert "query_params" in data

    async def test_submit_endpoint_success(self, async_client: AsyncClient):
        """Тест: Успешный POST запрос"""
        response = await async_client.post("/submit", json={"data": "test"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["received"]["data"] == "test"

    async def test_submit_endpoint_with_error(self, async_client: AsyncClient):
        """Тест: POST запрос с ошибкой"""
        response = await async_client.post("/submit", json={"error": "trigger_error"})
        # ✅ Может быть 400 или 500
        assert response.status_code in [400, 500]
        data = response.json()
        assert "status_code" in data or "error_code" in data


@pytest.mark.asyncio
class TestGlitchTip:
    """Тесты для GlitchTip интеграции"""

    async def test_glitchtip_error(self, async_client: AsyncClient):
        """Тест: Отправка ошибки в GlitchTip"""
        response = await async_client.get("/test-glitchtip")
        # ✅ Должен вернуть 500
        assert response.status_code == 500
        data = response.json()
        assert "status_code" in data or "error_code" in data


@pytest.mark.asyncio
class TestHeaders:
    """Тесты для заголовков"""

    async def test_request_id_header(self, async_client: AsyncClient):
        """Тест: Проверка заголовка X-Request-ID"""
        response = await async_client.get("/test/not-found")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    async def test_error_handle_time_header(self, async_client: AsyncClient):
        """Тест: Проверка заголовка X-ErrorHandleTime"""
        response = await async_client.get("/test/not-found")
        assert "X-ErrorHandleTime" in response.headers
        assert "ms" in response.headers["X-ErrorHandleTime"]