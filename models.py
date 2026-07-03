from imports import *
from dotenv import load_dotenv
from dataclasses import dataclass
from pydantic_settings import BaseSettings
import os


ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
print(f"Loading .env from: {ENV_PATH}")
load_dotenv(ENV_PATH)



@dataclass
class DatabaseConfig:
    database_url: str


@dataclass
class Config:
    db: DatabaseConfig
    secret_key: str
    debug: bool


def load_config(path: str = None) -> Config:
    # Загружаем .env файл
    if path is None:
        path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(path)

    return Config(
        db=DatabaseConfig(database_url=os.getenv("DATABASE_URL")),
        secret_key=os.getenv("SECRET_KEY"),
        debug=os.getenv("DEBUG", "False").lower() == "true",
    )


class Settings(BaseSettings):
    MODE: str = "DEV"
    DOCS_USER: str = 'admin'
    DOCS_PASSWORD: str = 'secret'
    SECRET_KEY: str = "your-secret-key-here-change-in-production"

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True,
        extra = 'ignore'


settings = Settings()


class User(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class AuthUserRegister(BaseModel):
    username: str
    password: str


class AuthUserInDB(BaseModel):
    username: str
    hashed_password: str


class RefreshRequest(BaseModel):
    """Модель для запроса обновления токенов"""
    refresh_token: str

class TokenResponses(BaseModel):
    """Модель для ответа с токенами"""
    access_token: str
    refresh_token: str
    token_type: str