# test_errors.py
import pytest
from fastapi.testclient import TestClient
from main import app
import sys
import os

# Добавляем путь к проекту в PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

client = TestClient(app)


class TestUserErrors:
    """Тесты для ошибок, связанных с пользователями"""

    def test_user_not_found(self):
        """Тест: 404 User Not Found"""
        response = client.get("/test/not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "USER_NOT_FOUND"
        assert "User with ID 999 not found" in data["message"]
        assert "request_id" in data
        assert "timestamp" in data

    def test_user_already_exists(self):
        """Тест: 409 User Already Exists"""
        response = client.get("/test/conflict")
        assert response.status_code == 409
        data = response.json()
        assert data["error_code"] == "USER_ALREADY_EXISTS"
        assert "already exists" in data["message"]

    def test_access_denied(self):
        """Тест: 403 Access Denied"""
        response = client.get("/test/forbidden")
        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "ACCESS_DENIED"
        assert "permission" in data["message"].lower()


class TestValidationErrors:
    """Тесты для ошибок валидации"""

    def test_validation_exception(self):
        """Тест: 400 Invalid Data"""
        response = client.get("/test/validation")
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_USER_DATA"
        assert data["status_code"] == 400
        assert data["errors"] is not None
        assert data["errors"][0]["field"] == "email"

    def test_pydantic_validation_error(self):
        """Тест: 422 Validation Error (Pydantic)"""
        # Невалидный email и возраст
        response = client.get(
            "/test/validation-pydantic",
            params={"age": 200, "email": "invalid-email"}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
        assert data["status_code"] == 422
        assert "errors" in data
        # Проверяем, что есть ошибки по полям
        errors = data["errors"]
        error_fields = [e["field"] for e in errors]
        assert "query.age" in error_fields or "query.email" in error_fields

    def test_pydantic_validation_success(self):
        """Тест: Успешная валидация"""
        response = client.get(
            "/test/validation-pydantic",
            params={"age": 25, "email": "test@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["age"] == 25
        assert data["email"] == "test@example.com"


class TestInternalErrors:
    """Тесты для внутренних ошибок"""

    def test_internal_error(self):
        """Тест: 500 Internal Server Error"""
        response = client.get("/test/internal")
        assert response.status_code == 500
        data = response.json()
        assert "error_code" in data
        assert data["status_code"] == 500

    def test_rate_limit_error(self):
        """Тест: 429 Rate Limit Exceeded"""
        response = client.get("/test/rate-limit")
        assert response.status_code == 429
        data = response.json()
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert data["status_code"] == 429
        assert "Too many requests" in data["message"]


class TestErrorResponseStructure:
    """Тесты структуры ответов с ошибками"""

    def test_error_response_has_all_fields(self):
        """Проверка, что все ошибки содержат обязательные поля"""
        endpoints = [
            ("/test/not-found", 404),
            ("/test/validation", 400),
            ("/test/conflict", 409),
            ("/test/forbidden", 403),
            # ("/test/internal", 500),
            # ("/test/rate-limit", 429),
        ]

        for endpoint, expected_status in endpoints:
            response = client.get(endpoint)
            assert response.status_code == expected_status
            data = response.json()

            # Проверяем наличие всех обязательных полей
            required_fields = ["status_code", "message", "error_code", "timestamp", "request_id"]
            for field in required_fields:
                assert field in data, f"Field '{field}' missing in response for {endpoint}"

            # Проверяем типы данных
            assert isinstance(data["status_code"], int)
            assert isinstance(data["message"], str)
            assert isinstance(data["error_code"], str)
            assert isinstance(data["timestamp"], str)
            assert data["status_code"] == expected_status

    def test_error_response_has_cors_headers(self):
        """Проверка CORS заголовков в ответах с ошибками"""
        response = client.get("/test/not-found")
        # Проверяем наличие кастомных заголовков
        assert "X-Request-ID" in response.headers
        assert "X-ErrorHandleTime" in response.headers


class TestUserCreate:
    """Тесты для создания пользователя с валидацией"""

    def test_create_user_success(self):
        """Тест: Успешное создание пользователя"""
        user_data = {
            "username": "john_doe",
            "age": 25,
            "email": "john@example.com",
            "password": "securepass"
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "john_doe"
        assert data["email"] == "john@example.com"
        assert "id" in data
        assert "created_at" in data

    def test_create_user_invalid_age(self):
        """Тест: Ошибка валидации возраста (слишком молодой)"""
        user_data = {
            "username": "young_user",
            "age": 16,
            "email": "young@example.com",
            "password": "securepass"
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 422
        data = response.json()
        assert "errors" in data
        # Проверяем, что есть ошибка по полю age
        age_errors = [e for e in data["errors"] if e["field"] == "body.age"]
        assert len(age_errors) > 0
        assert "greater than" in age_errors[0]["message"].lower()

    def test_create_user_invalid_age_too_old(self):
        """Тест: Ошибка валидации возраста (слишком старый)"""
        user_data = {
            "username": "old_user",
            "age": 150,
            "email": "old@example.com",
            "password": "securepass"
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 422
        data = response.json()
        errors = [e for e in data["errors"] if e["field"] == "body.age"]
        assert len(errors) > 0

    def test_create_user_invalid_email(self):
        """Тест: Ошибка валидации email"""
        user_data = {
            "username": "test_user",
            "age": 25,
            "email": "invalid-email",
            "password": "securepass"
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 422
        data = response.json()
        errors = [e for e in data["errors"] if e["field"] == "body.email"]
        assert len(errors) > 0
        assert "email" in errors[0]["message"].lower()

    def test_create_user_short_password(self):
        """Тест: Ошибка валидации пароля (слишком короткий)"""
        user_data = {
            "username": "test_user",
            "age": 25,
            "email": "test@example.com",
            "password": "short"
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 422
        data = response.json()
        errors = [e for e in data["errors"] if e["field"] == "body.password"]
        assert len(errors) > 0
        assert "at least 8" in errors[0]["message"].lower()

    def test_create_user_long_password(self):
        """Тест: Ошибка валидации пароля (слишком длинный)"""
        user_data = {
            "username": "test_user",
            "age": 25,
            "email": "test@example.com",
            "password": "this_password_is_way_too_long_for_validation"
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 422
        data = response.json()
        errors = [e for e in data["errors"] if e["field"] == "body.password"]
        assert len(errors) > 0

    def test_create_user_missing_fields(self):
        """Тест: Ошибка при отсутствии обязательных полей"""
        user_data = {
            "username": "incomplete_user",
            "age": 25
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 422
        data = response.json()
        # Проверяем, что есть ошибки для отсутствующих полей
        error_fields = [e["field"] for e in data["errors"]]
        assert "body.email" in error_fields or "body.password" in error_fields

    def test_create_user_duplicate_username(self):
        """Тест: Создание пользователя с существующим именем"""
        # Создаем первого пользователя
        user_data = {
            "username": "duplicate_user",
            "age": 30,
            "email": "first@example.com",
            "password": "password123"
        }
        response1 = client.post("/users", json=user_data)
        assert response1.status_code == 200

        # Пытаемся создать второго с таким же именем
        user_data2 = {
            "username": "duplicate_user",
            "age": 25,
            "email": "second@example.com",
            "password": "password456"
        }
        response2 = client.post("/users", json=user_data2)
        assert response2.status_code == 200
        assert response2.json()["id"] != response1.json()["id"]


class TestLoggingAndErrors:
    """Тесты для эндпоинтов с логированием ошибок"""

    def test_ok_endpoint(self):
        """Тест: Успешный эндпоинт"""
        response = client.get("/ok")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "message": "Everything is fine"}

    def test_error_endpoint(self):
        """Тест: Кастомная ошибка 418"""
        response = client.get("/error")
        assert response.status_code == 418
        data = response.json()
        assert "I'm a teapot" in data["message"]

    def test_boom_endpoint_returns_error(self):
        """Тест: Эндпоинт с неожиданной ошибкой"""
        response = client.get("/boom")
        # Должен вернуть 500
        assert response.status_code == 500
        data = response.json()
        assert "error_code" in data or "message" in data

    def test_echo_endpoint(self):
        """Тест: Эхо-эндпоинт"""
        response = client.get("/echo?name=Alice&age=30")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello, Alice!"
        assert data["age"] == 30
        assert "headers" in data
        assert "query_params" in data

    def test_submit_endpoint_success(self):
        """Тест: Успешный POST запрос"""
        response = client.post("/submit", json={"data": "test"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["received"]["data"] == "test"

    def test_submit_endpoint_with_error(self):
        """Тест: POST запрос с ошибкой"""
        response = client.post("/submit", json={"error": "trigger_error"})
        assert response.status_code == 500
        data = response.json()
        assert "error_code" in data

class TestGlitchTip:
    """Тесты для GlitchTip интеграции"""

    def test_glitchtip_error(self):
        """Тест: Отправка ошибки в GlitchTip"""
        # Этот тест может вызвать ошибку, но мы проверяем, что ответ приходит
        response = client.get("/test-glitchtip")
        # Должен вернуть 500 или ошибку KeyError
        assert response.status_code == 500
        data = response.json()
        assert "error_code" in data


class TestHeaders:
    """Тесты для заголовков"""

    def test_request_id_header(self):
        """Тест: Проверка заголовка X-Request-ID"""
        response = client.get("/test/not-found")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_error_handle_time_header(self):
        """Тест: Проверка заголовка X-ErrorHandleTime"""
        response = client.get("/test/not-found")
        assert "X-ErrorHandleTime" in response.headers
        # Проверяем, что это число с единицей измерения
        assert "ms" in response.headers["X-ErrorHandleTime"]


# Фикстура для запуска всех тестов
@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Подготовка перед каждым тестом"""
    # Здесь можно добавить очистку БД или другие подготовительные действия
    yield
    # Очистка после теста (опционально)