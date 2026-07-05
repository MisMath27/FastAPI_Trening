from imports import *
from models import AuthUserInDB, Users
from security import hash_password
import secrets


USERS_DATA = [
    {
        "username": "admin",
        "password": "adminpass",
        "roles": ["admin"],
        "full_name": "Admin User",
        "email": "admin@example.com",
        "disabled": False
    },
    {
        "username": "user",
        "password": "userpass",
        "roles": ["user"],
        "full_name": "Regular User",
        "email": "user@example.com",
        "disabled": False
    },
    {
        "username": "guest",
        "password": "guestpass",
        "roles": ["guest"],
        "full_name": "Guest User",
        "email": "guest@example.com",
        "disabled": False
    },
]

def get_user(username: str):
    """
    Функция для поиска пользователя по имени пользователя.
    В реальном проекте это должно быть запросом к базе данных.
    """
    for user in USERS_DATA:
        if user.get("username") == username:
            return user
    return None


def authenticate_user(username: str, password: str) -> bool:
    """
    Проверка учетных данных
    """
    for user in USERS_DATA:
        if user.get("username") == username and user.get("password") == password:
            return True

    return False






def get_user_by_username(username: str) -> Optional[AuthUserInDB]:
    for stored_username in fake_users_db:
        if secrets.compare_digest(stored_username, username):
            return fake_users_db[stored_username]
    return None


def user_exists(username: str) -> bool:
    return get_user_by_username(username) is not None


def create_user(username: str, hashed_password: str) -> AuthUserInDB:
    user = AuthUserInDB(username=username, hashed_password=hashed_password)
    fake_users_db[username] = user
    return user





def safe_refresh_token(username: str, refresh_token: str) -> None:
    refresh_tokens_store[username] = refresh_token


def get_refresh_token(username: str) -> Optional[str]:
    return refresh_tokens_store.get(username)


def delete_refresh_token(username: str) -> None:
    if username in refresh_tokens_store:
        del refresh_tokens_store[username]


def validate_refresh_token(username: str, refresh_token: str) -> bool:
    stored_token = get_refresh_token(username)
    if stored_token is None:
        return False
    return secrets.compare_digest(stored_token, refresh_token)


def get_user(username: str):
    """
    Функция для поиска пользователя по имени пользователя.
    Сначала проверяет fake_users_db, потом USERS_DATA.
    """
    if username in fake_users_db:
        user = fake_users_db[username]
        return {
            "username": user.username,
            "hashed_password": user.hashed_password,
            "roles": getattr(user, 'roles', ['user']),
            "full_name": user.username,
            "email": f"{user.username}@example.com",
            "disabled": False
        }
    for user in USERS_DATA:
        if user.get("username") == username:
            return user

    return None


fake_users_db: dict[str, AuthUserInDB] = {}
refresh_tokens_store: dict[str, str] = {}


if "admin_test" not in fake_users_db:
    fake_users_db["admin_test"] = AuthUserInDB(
        username="admin_test",
        hashed_password=hash_password("admin123"),
        roles=["admin"]
    )
    print("Admin user 'admin_test' created with admin role")

if "user_test" not in fake_users_db:
    fake_users_db["user_test"] = AuthUserInDB(
        username="user_test",
        hashed_password=hash_password("user123"),
        roles=["user"]
    )
    print("User 'user_test' created with user role")

if "guest_test" not in fake_users_db:
    fake_users_db["guest_test"] = AuthUserInDB(
        username="guest_test",
        hashed_password=hash_password("guest123"),
        roles=["guest"]  # ← ГОСТЬ
    )
    print("Guest 'guest_test' created with guest role")