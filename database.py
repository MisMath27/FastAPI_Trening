import asyncpg
from contextlib import asynccontextmanager

DATABASE_URL = "postgresql://postgres:secret@localhost:5432/todo_db"

@asynccontextmanager
async def get_db_connection():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()

async def init_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            # Создаем таблицу если ее нет
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print('Таблица todos создана в PostgreSQL!')
        finally:
            await conn.close()
    except Exception as e:
        print(f'Ошибка: {e}')
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())