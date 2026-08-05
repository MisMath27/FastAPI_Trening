# tests/test_mock_weather.py
import pytest
import httpx
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


class TestWeatherEndpoint:
    """Тесты для эндпоинта /weather с моками функции get_weather."""

    @pytest.fixture
    async def client(self):
        """Асинхронный клиент для тестирования."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver"
        ) as client:
            yield client

    # ============================================================
    # 1. СЧАСТЛИВЫЙ ПУТЬ
    # ============================================================

    @pytest.mark.asyncio
    async def test_weather_success(self, client):
        """
        Сценарий: внешнее API возвращает 200 с валидным JSON.
        Ожидание: эндпоинт возвращает 200 и правильное тело.
        """
        with patch('main.get_weather') as mock_get_weather:
            mock_get_weather.return_value = {"city": "London", "temp_c": 15.5}

            response = await client.get("/weather?city=London")

            assert response.status_code == 200
            data = response.json()
            assert data["city"] == "London"
            assert data["temp_c"] == 15.5

            mock_get_weather.assert_called_once_with("London")

    # ============================================================
    # 2. ОШИБКА 5xx
    # ============================================================

    @pytest.mark.asyncio
    async def test_weather_500_error(self, client):
        """
        Сценарий: внешнее API возвращает 500.
        Ожидание: эндпоинт возвращает 502.
        """
        with patch('main.get_weather') as mock_get_weather:
            mock_response = httpx.Response(500, text="Internal Server Error")
            mock_get_weather.side_effect = httpx.HTTPStatusError(
                "500 Error",
                request=httpx.Request("GET", "https://api.example.com/weather"),
                response=mock_response
            )

            response = await client.get("/weather?city=Paris")

            assert response.status_code == 502
            data = response.json()
            # ✅ Проверяем 'message' вместо 'detail'
            assert "message" in data
            assert "500" in data["message"]

            mock_get_weather.assert_called_once_with("Paris")

    # ============================================================
    # 3. ТАЙМАУТ
    # ============================================================

    @pytest.mark.asyncio
    async def test_weather_timeout(self, client):
        """
        Сценарий: внешнее API не отвечает (таймаут).
        Ожидание: эндпоинт возвращает 504.
        """
        with patch('main.get_weather') as mock_get_weather:
            mock_get_weather.side_effect = httpx.ReadTimeout("Timeout occurred")

            response = await client.get("/weather?city=Berlin")

            assert response.status_code == 504
            data = response.json()
            # ✅ Проверяем 'message' вместо 'detail'
            assert "message" in data
            assert "timeout" in data["message"].lower()

            mock_get_weather.assert_called_once_with("Berlin")

    # ============================================================
    # 4. НЕОЖИДАННЫЙ ОТВЕТ (отсутствует temp_c)
    # ============================================================

    @pytest.mark.asyncio
    async def test_weather_missing_temp(self, client):
        """
        Сценарий: внешнее API вернуло 200, но без поля temp_c.
        Ожидание: эндпоинт возвращает 502.
        """
        with patch('main.get_weather') as mock_get_weather:
            mock_get_weather.side_effect = KeyError("temp_c")

            response = await client.get("/weather?city=Rome")

            assert response.status_code == 502
            data = response.json()
            # ✅ Проверяем 'message' вместо 'detail'
            assert "message" in data
            assert "missing" in data["message"].lower()

            mock_get_weather.assert_called_once_with("Rome")

    # ============================================================
    # 5. ОШИБКА ПОДКЛЮЧЕНИЯ
    # ============================================================

    @pytest.mark.asyncio
    async def test_weather_connection_error(self, client):
        """
        Сценарий: ошибка подключения к внешнему API.
        Ожидание: эндпоинт возвращает 502.
        """
        with patch('main.get_weather') as mock_get_weather:
            mock_get_weather.side_effect = httpx.ConnectError("Connection failed")

            response = await client.get("/weather?city=Madrid")

            assert response.status_code == 502
            data = response.json()
            # ✅ Проверяем 'message' вместо 'detail'
            assert "message" in data
            assert "connection" in data["message"].lower()

            mock_get_weather.assert_called_once_with("Madrid")

    # ============================================================
    # 6. ПРОВЕРКА НЕСКОЛЬКИХ ЗАПРОСОВ
    # ============================================================

    @pytest.mark.asyncio
    async def test_multiple_weather_requests(self, client):
        """
        Проверка: два разных запроса.
        """
        with patch('main.get_weather') as mock_get_weather:
            mock_get_weather.side_effect = [
                {"city": "Moscow", "temp_c": -5.0},
                {"city": "Dubai", "temp_c": 35.0}
            ]

            response1 = await client.get("/weather?city=Moscow")
            response2 = await client.get("/weather?city=Dubai")

            assert response1.status_code == 200
            assert response1.json()["temp_c"] == -5.0
            assert response2.status_code == 200
            assert response2.json()["temp_c"] == 35.0

            assert mock_get_weather.call_count == 2
            mock_get_weather.assert_any_call("Moscow")
            mock_get_weather.assert_any_call("Dubai")