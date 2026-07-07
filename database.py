import sqlite3
import aiosqlite
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")


def get_db_connection_sync():
    """Синхронное подключение для инициализации БД"""
    return sqlite3.connect("app.db")


def init_db():
    """Инициализация базы данных с правильной структурой"""
    conn = get_db_connection_sync()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT 0,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute("PRAGMA foreign_keys = ON")

    conn.commit()
    conn.close()
    print("База данных инициализирована с поддержкой каскадного удаления")


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator:
    """Асинхронное подключение к SQLite"""
    conn = await aiosqlite.connect("app.db")
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        await conn.close()


init_db()