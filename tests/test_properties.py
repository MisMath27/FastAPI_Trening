# tests/test_properties.py
import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, precondition
from httpx import AsyncClient, ASGITransport
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, db


# ============================================================
# СТРАТЕГИИ ДЛЯ ГЕНЕРАЦИИ ДАННЫХ
# ============================================================

@st.composite
def valid_user_data(draw):
    username = draw(
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=3,
            max_size=50
        )
    )
    age = draw(st.integers(min_value=19, max_value=119))
    email = draw(st.emails())
    password = draw(st.text(min_size=8, max_size=16))

    return {
        "username": username.lower(),  # ← Приводим к нижнему регистру!
        "age": age,
        "email": email,
        "password": password
    }


@st.composite
def invalid_user_data(draw):
    """Стратегия для генерации НЕвалидных данных пользователя."""
    error_type = draw(st.sampled_from([
        "empty_username", "short_username", "invalid_age",
        "invalid_email", "short_password", "long_password"
    ]))

    base = {
        "username": draw(st.text(min_size=3, max_size=50)),
        "age": draw(st.integers(min_value=19, max_value=119)),
        "email": draw(st.emails()),
        "password": draw(st.text(min_size=8, max_size=16))
    }

    if error_type == "empty_username":
        base["username"] = ""
    elif error_type == "short_username":
        base["username"] = draw(st.text(min_size=1, max_size=2))
    elif error_type == "invalid_age":
        base["age"] = draw(st.one_of(
            st.integers(min_value=0, max_value=18),
            st.integers(min_value=120, max_value=200)
        ))
    elif error_type == "invalid_email":
        base["email"] = draw(st.text(min_size=5, max_size=20))
    elif error_type == "short_password":
        base["password"] = draw(st.text(min_size=1, max_size=7))
    elif error_type == "long_password":
        base["password"] = draw(st.text(min_size=17, max_size=30))

    return base, error_type


# ============================================================
# 1. СВОЙСТВО: «создание и чтение совпадают»
# ============================================================

@pytest.mark.asyncio
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]  # ← ДОБАВИТЬ!
)
@given(user=valid_user_data())
async def test_create_and_read_match(user, async_client):
    """
    Свойство: POST /users → GET /users/{id} возвращают те же данные.
    """
    db.clear()
    # 1. Создаем пользователя
    post_response = await async_client.post("/users", json=user)
    assert post_response.status_code == 200
    created = post_response.json()

    # 2. Получаем пользователя по id
    user_id = created["id"]
    get_response = await async_client.get(f"/users/{user_id}")
    assert get_response.status_code == 200
    retrieved = get_response.json()

    # 3. Сравниваем поля
    assert retrieved["id"] == created["id"]
    assert retrieved["username"] == created["username"]
    assert retrieved["email"] == created["email"]

    # 4. Проверяем, что данные сохранились в БД
    assert db[user_id]["username"] == user["username"]
    assert db[user_id]["age"] == user["age"]
    assert db[user_id]["email"] == user["email"]


# ============================================================
# 2. СВОЙСТВО: «уникальные и монотонно возрастающие id»
# ============================================================

@pytest.mark.asyncio
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]  # ← ДОБАВИТЬ!
)
@given(users=st.lists(valid_user_data(), min_size=2, max_size=10))
async def test_unique_monotonic_ids(users, async_client):
    """
    Свойство: id уникальны и монотонно возрастают.
    """
    db.clear()
    ids = []

    for user in users:
        response = await async_client.post("/users", json=user)
        assert response.status_code == 200
        data = response.json()
        ids.append(data["id"])

    # Проверяем уникальность
    assert len(ids) == len(set(ids))

    # Проверяем монотонность (возрастание)
    for i in range(1, len(ids)):
        assert ids[i] > ids[i - 1]


# ============================================================
# 3. СВОЙСТВО: удаление
# ============================================================

@pytest.mark.asyncio
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]  # ← ДОБАВИТЬ!
)
@given(user=valid_user_data())
async def test_delete_properties(user, async_client):
    """
    Свойства удаления: после DELETE ресурс исчезает.
    """
    db.clear()
    # 1. Создаем пользователя
    post_response = await async_client.post("/users", json=user)
    assert post_response.status_code == 200
    user_id = post_response.json()["id"]

    # 2. Первое удаление - должно быть 204
    delete1 = await async_client.delete(f"/users/{user_id}")
    assert delete1.status_code == 204

    # 3. Проверяем, что пользователь удален
    get_response = await async_client.get(f"/users/{user_id}")
    assert get_response.status_code == 404

    # 4. Второе удаление - должно быть 404
    delete2 = await async_client.delete(f"/users/{user_id}")
    assert delete2.status_code == 404


# ============================================================
# 4. НЕГАТИВНЫЕ ГРАНИЦЫ (robustness)
# ============================================================

@pytest.mark.asyncio
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]  # ← ДОБАВИТЬ!
)
@given(data=invalid_user_data())
async def test_negative_boundaries(data, async_client):
    """
    Свойство: невалидные данные отвергаются с корректным кодом.
    """
    db.clear()
    user_data, error_type = data

    response = await async_client.post("/users", json=user_data)

    # Невалидные данные должны возвращать 422
    assert response.status_code == 422
    data = response.json()
    assert "errors" in data or "detail" in data


@pytest.mark.asyncio
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(user=valid_user_data())
async def test_valid_data_accepted(user, async_client):
    db.clear()
    response = await async_client.post("/users", json=user)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["username"] == user["username"]
    # Сравниваем в нижнем регистре
    assert data["email"].lower() == user["email"].lower()

# ============================================================
# 5. STATEFUL ТЕСТИРОВАНИЕ (последовательностное свойство)
# ============================================================

class UserStateMachine(RuleBasedStateMachine):
    """
    Stateful тест: проверяем последовательности операций.
    Используем "теневой" словарь-оракул.
    """

    def __init__(self):
        super().__init__()
        self.oracle = {}  # Теневой словарь для сравнения
        self.next_id = 1
        self.client = None

    def _get_client(self):
        """Ленивая инициализация клиента."""
        if self.client is None:
            import asyncio
            # Создаем клиент в основном потоке
            self.client = AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://testserver"
            )
        return self.client

    # Действия

    @rule(user=valid_user_data())
    async def create(self, user):
        """Действие: создать пользователя."""
        # Очищаем перед каждым запуском
        if not hasattr(self, '_initialized'):
            db.clear()
            self.oracle.clear()
            self.next_id = 1
            self._initialized = True

        client = self._get_client()
        response = await client.post("/users", json=user)

        if response.status_code == 200:
            data = response.json()
            user_id = data["id"]
            # Обновляем оракул
            self.oracle[user_id] = {
                "username": user["username"],
                "age": user["age"],
                "email": user["email"]
            }
            # Проверяем, что id соответствует ожидаемому
            assert user_id == self.next_id
            self.next_id += 1
        else:
            assert response.status_code == 422
        return


    @rule(user_id=st.integers(min_value=1, max_value=50))
    async def read(self, user_id):
        """Действие: прочитать пользователя."""
        client = self._get_client()
        response = await client.get(f"/users/{user_id}")

        if user_id in self.oracle:
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == self.oracle[user_id]["username"]
            assert data["email"] == self.oracle[user_id]["email"]
        else:
            assert response.status_code == 404

    @rule(user_id=st.integers(min_value=1, max_value=50))
    async def delete(self, user_id):
        """Действие: удалить пользователя."""
        client = self._get_client()
        response = await client.delete(f"/users/{user_id}")

        if user_id in self.oracle:
            assert response.status_code == 204
            del self.oracle[user_id]
        else:
            assert response.status_code == 404

    @invariant()
    def check_invariant(self):
        """Инвариант: оракул и БД должны быть согласованы."""
        if hasattr(self, '_initialized'):
            for user_id in self.oracle:
                assert user_id in db
                assert db[user_id]["username"] == self.oracle[user_id]["username"]
                assert db[user_id]["email"] == self.oracle[user_id]["email"]


# Регистрируем stateful тест
TestUserStateMachine = UserStateMachine.TestCase


# ============================================================
# 6. ДОПОЛНИТЕЛЬНЫЕ СВОЙСТВА
# ============================================================

@pytest.mark.asyncio
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]  # ← ДОБАВИТЬ!
)
@given(user=valid_user_data())
async def test_delete_idempotence(user, async_client):
    """
    Свойство: удаление идемпотентно (второй DELETE = 404).
    """
    db.clear()
    # Создаем пользователя
    post_response = await async_client.post("/users", json=user)
    assert post_response.status_code == 200
    user_id = post_response.json()["id"]

    # Удаляем несколько раз
    for i in range(3):
        response = await async_client.delete(f"/users/{user_id}")
        if i == 0:
            assert response.status_code == 204
        else:
            assert response.status_code == 404


@pytest.mark.asyncio
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]  # ← ДОБАВИТЬ!
)
@given(user_id=st.integers(min_value=1000, max_value=9999))
async def test_get_nonexistent(user_id, async_client):
    """
    Свойство: GET несуществующего пользователя возвращает 404.
    """
    db.clear()
    response = await async_client.get(f"/users/{user_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]  # ← ДОБАВИТЬ!
)
@given(user=valid_user_data())
async def test_created_user_in_db(user, async_client):
    """
    Свойство: после создания пользователь есть в БД.
    """
    db.clear()
    response = await async_client.post("/users", json=user)
    assert response.status_code == 200
    data = response.json()
    user_id = data["id"]

    # Проверяем, что пользователь есть в БД
    assert user_id in db
    assert db[user_id]["username"] == user["username"]
    assert db[user_id]["age"] == user["age"]
    assert db[user_id]["email"] == user["email"]