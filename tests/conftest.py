import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from faker import Faker
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Инициализируем Faker
fake = Faker()


@pytest.fixture(scope="function")
async def async_client():
    """
    Асинхронный клиент для тестирования.
    Использует ASGITransport для прямого вызова приложения.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture(scope="function")
def faker():
    """Фикстура для генерации тестовых данных."""
    return fake


@pytest.fixture(scope="function")
def test_user_data(faker):
    """Генерирует тестовые данные пользователя."""
    return {
        "username": faker.user_name(),
        "age": faker.random_int(min=18, max=99),
        "email": faker.email(),
        "password": faker.password(length=10)
    }


@pytest.fixture(scope="function", autouse=True)
async def clean_database():
    """
    Автоматически очищает базу данных перед каждым тестом.
    """
    from main import db
    db.clear()
    yield
    db.clear()