import os

from fastapi import FastAPI

from config import load_config
from logger import logger


# Загружаем конфигурацию
config = load_config()

app = FastAPI()


@app.get("/")
def read_root():
    logger.info("Корневой маршрут вызван")
    return {"message": "Hello, World!"}


@app.get("/custom")
def read_custom_message():
    logger.info("Маршрут /custom вызван")
    return {"message": "This is a custom message!"}


@app.get("/config")
def get_config():
    """Маршрут для проверки конфигурации"""
    return {
        "secret_key": config.secret_key,
        "database_url": config.db.database_url,
        "debug": config.debug,
    }


@app.get("/hello/{name}")
def hello(name: str):
    logger.info(f"Приветствие для {name}")
    return {"message": f"Привет, {name}!"}


# Запуск (если файл выполняется напрямую)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=config.debug)
