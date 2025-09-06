# backend/app/db/migrations.py
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def run_migrations(db: AsyncSession):
    """Run database migrations to create/update schema for Morphing Digital Paralegal"""
    
    try:
        # Enable pgvector extension
        logger.info("Enabling pgvector extension...")
        await db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        # Create neurobots table
        logger.info("Creating neurobots table...")
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS neurobots (
                id SERIAL PRIMARY KEY,
                function_name VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                code TEXT NOT NULL,
                neurobot_type VARCHAR(50) DEFAULT 'analyze',
                created_by VARCHAR(255),
                is_active BOOLEAN DEFAULT true,
                run_count INTEGER DEFAULT 0,
                feedback_plus INTEGER DEFAULT 0,
                feedback_minus INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create clause_embeddings table
        logger.info("Creating clause_embeddings table...")
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS clause_embeddings (
                id SERIAL PRIMARY KEY,
                clause_text TEXT NOT NULL,
                embedding vector(1536),
                clause_type VARCHAR(100),
                risk_level VARCHAR(50),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create clause_patterns table
        logger.info("Creating clause_patterns table...")
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS clause_patterns (
                id SERIAL PRIMARY KEY,
                pattern_name VARCHAR(255) NOT NULL,
                pattern_regex TEXT,
                clause_type VARCHAR(100),
                risk_indicators JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create contracts table
        logger.info("Creating contracts table...")
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS contracts (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255),
                content TEXT,
                analysis_results JSONB,
                uploaded_by VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        await db.commit()
        logger.info("All migrations completed successfully")
            
    except Exception as e:
        logger.error(f"Migration error: {e}")
        await db.rollback()
        raise