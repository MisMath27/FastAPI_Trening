import os
from dataclasses import dataclass

from dotenv import load_dotenv


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
