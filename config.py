import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:123@localhost:5432/todo_db")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    MODE: str = os.getenv("MODE", "DEV")
    DOCS_USER: str = os.getenv("DOCS_USER", "admin")
    DOCS_PASSWORD: str = os.getenv("DOCS_PASSWORD", "secret")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


import os
from dotenv import load_dotenv


load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "secret")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"



settings = Settings()



