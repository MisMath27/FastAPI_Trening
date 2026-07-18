from imports import *
from dotenv import load_dotenv
from dataclasses import dataclass
from pydantic_settings import BaseSettings
import os
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Enum


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


class Users(BaseModel):
    username: str
    full_name: str | None = None
    email: EmailStr | None = None
    disabled: bool = False
    roles: list[str] = ["user"]


class UserLogin(BaseModel):
    username: str
    password: str


class Item(BaseModel):
    name: str


class UserRegister(BaseModel):
    username: str
    password: str


class TodoCreate(BaseModel):
    """Модель для создания Todo"""
    title: str = Field(..., min_length=1, max_length=200, description="Заголовок задачи")
    description: Optional[str] = Field(None, max_length=1000, description="Описание задачи")

class TodoUpdate(BaseModel):
    """Модель для обновления Todo"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    completed: Optional[bool] = None

class TodoResponse(BaseModel):
    """Модель для ответа"""
    id: int
    title: str
    description: Optional[str]
    completed: bool
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TodoCreated(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    user_id: int


class TodoUpdated(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    completed: Optional[bool] = None
    user_id: Optional[int] = None


class TodoResponses(BaseModel):
    id: int
    title: str
    description: Optional[str]
    completed: bool
    user_id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TodoAnalyticsResponse(BaseModel):
    total: int
    completed_status: Dict[str, int]
    avg_completion_time_hours: Optional[float] = None
    weekday_distribution: Dict[str, int]


class BulkUpdateResponse(BaseModel):
    updated_count: int



















