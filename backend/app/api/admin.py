# backend/app/api/admin.py
import logging
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, update
from app.db.database import get_db
from app.db.models import AnalysisCache, DocumentAnalysis, ComplianceIssue
from app.api.auth import get_current_user, User
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

# Global cache settings (could move to database or config)
class CacheSettings:
    enabled: bool = True
    ttl_hours: int = 24

cache_settings = CacheSettings()

class CacheConfig(BaseModel):
    enabled: bool
    ttl_hours: int = 24

@router.get("/cache/status")
async def get_cache_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current cache status and statistics"""
    
    # Check if user is admin (you might want to add proper role checking)
    if current_user.email not in ['luca@gibelli.it', 'admin@finra.com']:
        raise HTTPException(403, "Admin access required")
    
    # Get cache statistics
    total_result = await db.execute(select(AnalysisCache))
    total_cache = len(total_result.scalars().all())
    
    valid_result = await db.execute(
        select(AnalysisCache).where(AnalysisCache.expires_at > datetime.utcnow())
    )
    valid_cache = len(valid_result.scalars().all())
    
    expired_cache = total_cache - valid_cache
    
    return {
        "cache_enabled": cache_settings.enabled,
        "ttl_hours": cache_settings.ttl_hours,
        "total_entries": total_cache,
        "valid_entries": valid_cache,
        "expired_entries": expired_cache
    }

@router.post("/cache/configure")
async def configure_cache(
    config: CacheConfig,
    current_user: User = Depends(get_current_user)
):
    """Enable/disable cache and set TTL"""
    
    # Check if user is admin
    if current_user.email not in ['luca@gibelli.it', 'admin@finra.com']:
        raise HTTPException(403, "Admin access required")
    
    cache_settings.enabled = config.enabled
    cache_settings.ttl_hours = config.ttl_hours
    
    logger.info(f"Cache settings updated by {current_user.email}: enabled={config.enabled}, ttl={config.ttl_hours}h")
    
    return {
        "message": "Cache settings updated",
        "enabled": cache_settings.enabled,
        "ttl_hours": cache_settings.ttl_hours
    }

@router.post("/cache/clear")
async def clear_cache(
    expired_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clear cache entries"""
    
    # Check if user is admin
    if current_user.email not in ['luca@gibelli.it', 'admin@finra.com']:
        raise HTTPException(403, "Admin access required")
    
    if expired_only:
        result = await db.execute(
            delete(AnalysisCache).where(AnalysisCache.expires_at <= datetime.utcnow())
        )
    else:
        result = await db.execute(delete(AnalysisCache))
    
    await db.commit()
    
    logger.info(f"Cache cleared by {current_user.email}: {result.rowcount} entries deleted (expired_only={expired_only})")
    
    return {
        "message": f"Cleared {result.rowcount} cache entries",
        "expired_only": expired_only
    }

@router.delete("/analyses/cleanup")
async def cleanup_invalid_analyses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clean up analyses with invalid/hallucinated rule numbers"""
    
    # Check if user is admin
    if current_user.email not in ['luca@gibelli.it', 'admin@finra.com']:
        raise HTTPException(403, "Admin access required")
    
    # Get valid rule numbers
    from app.db.models import Rule
    valid_rules_result = await db.execute(select(Rule.rule_number))
    valid_rules = [r[0] for r in valid_rules_result]
    
    # Find and delete invalid compliance issues
    all_issues_result = await db.execute(select(ComplianceIssue.rule_number).distinct())
    all_issue_rules = [r[0] for r in all_issues_result]
    invalid_rules = [r for r in all_issue_rules if r not in valid_rules]
    
    deleted_count = 0
    if invalid_rules:
        result = await db.execute(
            delete(ComplianceIssue).where(ComplianceIssue.rule_number.in_(invalid_rules))
        )
        deleted_count = result.rowcount
        await db.commit()
    
    logger.info(f"Cleanup by {current_user.email}: deleted {deleted_count} issues with invalid rules {invalid_rules}")
    
    return {
        "message": f"Deleted {deleted_count} compliance issues",
        "invalid_rules": invalid_rules
    }

@router.get("/cache/settings")
async def get_cache_settings():
    """Get current cache settings (public endpoint for services)"""
    return {
        "enabled": cache_settings.enabled,
        "ttl_hours": cache_settings.ttl_hours
    }