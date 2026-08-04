# tests/test_mock_users.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from main import app
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

client = TestClient(app)


class TestUsersWithMocks:
    """Тесты для /users с моками."""

    # ============================================================
    # 1. УСПЕШНОЕ ПОЛУЧЕНИЕ ПОЛЬЗОВАТЕЛЯ
    # ============================================================

    @patch('main.users_db', new_callable=dict)
    def test_get_user_success(self, mock_users_db):
        """
        Тест: успешное получение пользователя.
        """
        # ✅ Наполняем мок-словарь данными
        mock_users_db[1] = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "created_at": "2026-08-04T12:00:00"
        }

        response = client.get("/users/1")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    # ============================================================
    # 2. ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН
    # ============================================================

    @patch('main.users_db', new_callable=dict)
    def test_get_user_not_found(self, mock_users_db):
        """
        Тест: пользователь не найден (404).
        """
        # ✅ Оставляем словарь пустым
        response = client.get("/users/999")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    # ============================================================
    # 3. УДАЛЕНИЕ НЕСУЩЕСТВУЮЩЕГО ПОЛЬЗОВАТЕЛЯ
    # ============================================================

    @patch('main.users_db', new_callable=dict)
    def test_delete_user_not_found(self, mock_users_db):
        """
        Тест: удаление несуществующего пользователя (404).
        """
        response = client.delete("/users/999")
        assert response.status_code == 404

    # ============================================================
    # 4. ПРОВЕРКИ ВЫЗОВОВ (с использованием Mock)
    # ============================================================

    @patch('main.users_db')
    def test_mock_called_once(self, mock_users_db):
        """
        Проверка: мок вызван ровно один раз.
        """
        # ✅ Создаем настоящий mock-словарь с методами
        mock_dict = MagicMock(spec=dict)
        mock_dict.__contains__.return_value = True
        mock_dict.__getitem__.return_value = {"id": 1, "username": "test"}

        # ✅ Подменяем users_db
        mock_users_db.return_value = mock_dict
        # Но важно: нам нужно подменить САМ объект, а не возвращаемое значение
        # В этом случае лучше использовать прямой доступ к патчу
        import main
        original_db = main.users_db
        main.users_db = mock_dict

        try:
            client.get("/users/1")
            mock_dict.__getitem__.assert_called_once_with(1)
        finally:
            main.users_db = original_db

    @patch('main.users_db')
    def test_mock_not_called(self, mock_users_db):
        """
        Проверка: мок НЕ был вызван.
        """
        mock_dict = MagicMock(spec=dict)
        mock_users_db.return_value = mock_dict

        import main
        original_db = main.users_db
        main.users_db = mock_dict

        try:
            response = client.get("/ok")
            assert response.status_code == 200
            mock_dict.__getitem__.assert_not_called()
        finally:
            main.users_db = original_db

    @patch('main.users_db')
    def test_mock_called_with_correct_args(self, mock_users_db):
        """
        Проверка: мок вызван с правильными аргументами.
        """
        mock_dict = MagicMock(spec=dict)
        mock_dict.__contains__.return_value = True
        mock_dict.__getitem__.return_value = {"id": 1, "username": "test"}

        import main
        original_db = main.users_db
        main.users_db = mock_dict

        try:
            client.get("/users/42")
            mock_dict.__getitem__.assert_called_with(42)
        finally:
            main.users_db = original_db

    # ============================================================
    # 5. СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ
    # ============================================================

    @patch('main.users_db', new_callable=dict)
    def test_create_user_success(self, mock_users_db):
        """
        Тест: успешное создание пользователя.
        """
        response = client.post("/users", json={
            "username": "testuser",
            "age": 25,
            "email": "test@example.com",
            "password": "securepass",
            "phone": "1234567890"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data

    # ============================================================
    # 6. НЕВАЛИДНЫЕ ДАННЫЕ
    # ============================================================

    def test_create_user_missing_fields(self):
        """Тест: отсутствуют обязательные поля → 422."""
        response = client.post("/users", json={"username": "testuser"})
        assert response.status_code == 422

    def test_create_user_invalid_email(self):
        """Тест: невалидный email → 422."""
        response = client.post("/users", json={
            "username": "testuser",
            "age": 25,
            "email": "invalid-email",
            "password": "securepass"
        })
        assert response.status_code == 422

    def test_create_user_invalid_age(self):
        """Тест: невалидный возраст → 422."""
        response = client.post("/users", json={
            "username": "testuser",
            "age": 15,
            "email": "test@example.com",
            "password": "securepass"
        })
        assert response.status_code == 422