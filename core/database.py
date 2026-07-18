from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import settings
import os


db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
if ":" in db_path or "//" in db_path:
    db_path = "./todo.db"
db_dir = os.path.dirname(db_path)
if db_dir:
    try:
        os.makedirs(db_dir, exist_ok=True)
    except OSError:
        db_path = "./todo.db"

ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False}
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()