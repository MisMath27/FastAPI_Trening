import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from config import settings


class Database:
    _pool = None

    @classmethod
    async def get_pool(cls):
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            print("PostgreSQL pool created")
        return cls._pool

    @classmethod
    async def close_pool(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            print("PostgreSQL pool closed")


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator:
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        yield conn


async def init_db():
    """Инициализация базы данных с проверкой существования"""
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        table_exists = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users')"
        )

        if not table_exists:
            print("Creating tables...")
            # Создаем таблицы
            await conn.execute('''
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await conn.execute('''
                CREATE TABLE todos (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    completed BOOLEAN DEFAULT FALSE,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

            await conn.execute('CREATE INDEX idx_todos_user_id ON todos(user_id)')
            await conn.execute('CREATE INDEX idx_todos_completed ON todos(completed)')
            await conn.execute('CREATE INDEX idx_todos_created_at ON todos(created_at)')

            await conn.execute('''
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql'
            ''')

            await conn.execute('''
                CREATE TRIGGER update_todos_updated_at 
                    BEFORE UPDATE ON todos 
                    FOR EACH ROW 
                    EXECUTE FUNCTION update_updated_at_column()
            ''')

            await conn.execute('''
                CREATE OR REPLACE FUNCTION set_completed_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    IF NEW.completed = TRUE AND (OLD.completed = FALSE OR OLD.completed IS NULL) THEN
                        NEW.completed_at = CURRENT_TIMESTAMP;
                    ELSIF NEW.completed = FALSE AND OLD.completed = TRUE THEN
                        NEW.completed_at = NULL;
                    END IF;
                    RETURN NEW;
                END;
                $$ language 'plpgsql'
            ''')

            await conn.execute('''
                CREATE TRIGGER set_todos_completed_at
                    BEFORE UPDATE ON todos
                    FOR EACH ROW
                    EXECUTE FUNCTION set_completed_at()
            ''')

            print("Tables created successfully")
        else:
            print("Tables already exist, skipping creation")

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
    finally:
        await conn.close()