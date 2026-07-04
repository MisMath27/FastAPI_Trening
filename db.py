from imports import *
from models import AuthUserInDB, Users

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


fake_users_db: dict[str, AuthUserInDB] = {}

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


refresh_tokens_store: dict[str, str] = {}

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


def get_users(username: str) -> Users:
    for user_data in USERS_DATA:
        if user_data["username"] == username:
            return Users(**{k: v for k, v in user_data.items() if k != "password"})
    return None
