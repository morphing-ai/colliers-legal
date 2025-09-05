# backend/app/db/migrations.py
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def run_migrations(db: AsyncSession):
    """Run database migrations to update schema"""
    
    try:
        # Check if paragraphs_processed column exists
        result = await db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'document_analyses' 
            AND column_name = 'paragraphs_processed'
        """))
        
        if not result.scalar():
            # Add the paragraphs_processed column
            logger.info("Adding paragraphs_processed column to document_analyses table")
            await db.execute(text("""
                ALTER TABLE document_analyses 
                ADD COLUMN IF NOT EXISTS paragraphs_processed INTEGER DEFAULT 0
            """))
            await db.commit()
            logger.info("Migration completed: Added paragraphs_processed column")
        else:
            logger.info("Migration check: paragraphs_processed column already exists")
            
    except Exception as e:
        logger.error(f"Migration error: {e}")
        await db.rollback()
        raise