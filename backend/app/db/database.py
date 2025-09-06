# backend/app/db/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# Create the SQLAlchemy async engine for PostgreSQL
# With --env-file option in uvicorn, DATABASE_URL is always available
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=25,  # Increased from 10 to 25 for parallel batch processing
    max_overflow=25,  # Increased from 20 to 25 for burst capacity
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create an async session factory
async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    """
    Dependency to get a DB session.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """
    Initialize the database and create tables.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)