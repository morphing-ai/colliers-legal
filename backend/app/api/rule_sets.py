# backend/app/api/rule_sets.py
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import json
import logging

from app.db.database import get_db
from app.services.rule_set_service import RuleSetService
from app.api.auth import get_current_user, User
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class RuleSetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    preprocessing_prompt: Optional[str] = None
    rule_set_metadata: Optional[Dict[str, Any]] = None

class RuleSetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_by: str
    is_active: bool
    preprocessing_prompt: Optional[str]
    rule_set_metadata: Dict[str, Any]
    rule_count: Optional[int] = 0
    created_at: str
    updated_at: Optional[str]

class RuleCreate(BaseModel):
    rule_number: str = Field(..., min_length=1)
    rule_title: str = Field(..., min_length=1)
    rule_text: str = Field(..., min_length=1)
    category: Optional[str] = None
    rule_metadata: Optional[Dict[str, Any]] = None

class RuleUpdate(BaseModel):
    rule_title: Optional[str] = None
    rule_text: Optional[str] = None
    category: Optional[str] = None
    rule_metadata: Optional[Dict[str, Any]] = None

class RuleResponse(BaseModel):
    id: int
    rule_set_id: int
    rule_number: str
    rule_title: str
    rule_text: str
    effective_start_date: Optional[str]
    effective_end_date: Optional[str]
    rulebook_hierarchy: Optional[str]
    category: Optional[str]
    summary: Optional[str]
    is_current: bool
    rule_metadata: Optional[Dict[str, Any]]
    created_at: str

@router.post("/rule-sets", response_model=RuleSetResponse)
async def create_rule_set(
    rule_set: RuleSetCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new rule set"""
    service = RuleSetService(db)
    
    try:
        created = await service.create_rule_set(
            name=rule_set.name,
            description=rule_set.description,
            created_by=current_user.id,
            preprocessing_prompt=rule_set.preprocessing_prompt,
            metadata=rule_set.rule_set_metadata or {}
        )
        
        return RuleSetResponse(
            id=created.id,
            name=created.name,
            description=created.description,
            created_by=created.created_by,
            is_active=created.is_active,
            preprocessing_prompt=created.preprocessing_prompt,
            rule_set_metadata=created.rule_set_metadata or {},
            rule_count=0,
            created_at=created.created_at.isoformat(),
            updated_at=created.updated_at.isoformat() if created.updated_at else None
        )
    except Exception as e:
        logger.error(f"Error creating rule set: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rule-sets", response_model=List[RuleSetResponse])
async def get_rule_sets(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    include_all: bool = False
):
    """Get all rule sets (optionally filtered by user)"""
    service = RuleSetService(db)
    
    try:
        rule_sets = await service.get_rule_sets(
            user_id=None if include_all else current_user.id
        )
        
        result = []
        for rs in rule_sets:
            result.append(RuleSetResponse(
                id=rs.id,
                name=rs.name,
                description=rs.description,
                created_by=rs.created_by,
                is_active=rs.is_active,
                preprocessing_prompt=rs.preprocessing_prompt,
                rule_set_metadata=rs.rule_set_metadata or {},
                rule_count=len(rs.rules) if hasattr(rs, 'rules') and rs.rules else 0,
                created_at=rs.created_at.isoformat(),
                updated_at=rs.updated_at.isoformat() if rs.updated_at else None
            ))
            
        return result
    except Exception as e:
        logger.error(f"Error getting rule sets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rule-sets/{rule_set_id}", response_model=RuleSetResponse)
async def get_rule_set(
    rule_set_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific rule set"""
    service = RuleSetService(db)
    
    rule_set = await service.get_rule_set(rule_set_id)
    if not rule_set:
        raise HTTPException(status_code=404, detail="Rule set not found")
        
    return RuleSetResponse(
        id=rule_set.id,
        name=rule_set.name,
        description=rule_set.description,
        created_by=rule_set.created_by,
        is_active=rule_set.is_active,
        preprocessing_prompt=rule_set.preprocessing_prompt,
        rule_set_metadata=rule_set.rule_set_metadata or {},
        rule_count=len(rule_set.rules) if hasattr(rule_set, 'rules') else 0,
        created_at=rule_set.created_at.isoformat(),
        updated_at=rule_set.updated_at.isoformat() if rule_set.updated_at else None
    )

@router.delete("/rule-sets/{rule_set_id}")
async def delete_rule_set(
    rule_set_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a rule set and all its rules"""
    service = RuleSetService(db)
    
    rule_set = await service.get_rule_set(rule_set_id)
    if not rule_set:
        raise HTTPException(status_code=404, detail="Rule set not found")
        
    # Check if user owns the rule set
    if rule_set.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this rule set")
        
    deleted = await service.delete_rule_set(rule_set_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete rule set")
        
    return {"message": "Rule set deleted successfully"}

@router.post("/rule-sets/{rule_set_id}/rules/upload")
async def upload_rules(
    rule_set_id: int,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Upload JSON files containing rules"""
    service = RuleSetService(db)
    
    # Check rule set exists
    rule_set = await service.get_rule_set(rule_set_id)
    if not rule_set:
        raise HTTPException(status_code=404, detail="Rule set not found")
        
    total_added = 0
    errors = []
    
    for file in files:
        if not file.filename.endswith('.json'):
            errors.append(f"{file.filename}: Not a JSON file")
            continue
            
        try:
            content = await file.read()
            json_data = json.loads(content)
            
            # Handle both single rule and array of rules
            if not isinstance(json_data, list):
                json_data = [json_data]
                
            added = await service.add_rules_from_json(rule_set_id, json_data)
            total_added += added
            
        except json.JSONDecodeError:
            errors.append(f"{file.filename}: Invalid JSON")
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
            
    return {
        "message": f"Added {total_added} rules to rule set",
        "rules_added": total_added,
        "errors": errors if errors else None
    }

@router.post("/rule-sets/{rule_set_id}/rules", response_model=RuleResponse)
async def add_rule_manually(
    rule_set_id: int,
    rule: RuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Add a rule manually"""
    service = RuleSetService(db)
    
    # Check rule set exists
    rule_set = await service.get_rule_set(rule_set_id)
    if not rule_set:
        raise HTTPException(status_code=404, detail="Rule set not found")
        
    try:
        created = await service.add_rule_manually(
            rule_set_id=rule_set_id,
            rule_number=rule.rule_number,
            rule_title=rule.rule_title,
            rule_text=rule.rule_text,
            category=rule.category,
            metadata=rule.rule_metadata
        )
        
        return RuleResponse(
            id=created.id,
            rule_set_id=created.rule_set_id,
            rule_number=created.rule_number,
            rule_title=created.rule_title,
            rule_text=created.rule_text,
            category=created.category,
            summary=created.summary,
            is_current=created.is_current,
            created_at=created.created_at.isoformat()
        )
    except Exception as e:
        logger.error(f"Error adding rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rule-sets/{rule_set_id}/rules", response_model=List[RuleResponse])
async def get_rules(
    rule_set_id: int,
    limit: int = 100,
    offset: int = 0,
    filter_date: Optional[str] = None,
    search_text: Optional[str] = None,
    rule_number: Optional[str] = None,  # Exact rule number match
    include_superseded: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get rules in a rule set with optional date filtering
    
    By default, excludes superseded rules (those with an end date).
    Set include_superseded=true to include historical rules.
    """
    from datetime import datetime
    
    service = RuleSetService(db)
    
    # Parse filter date if provided
    filter_date_obj = None
    if filter_date:
        try:
            filter_date_obj = datetime.strptime(filter_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # If rule_number is provided, do exact match instead of search
    if rule_number:
        rules = await service.get_rule_by_number(rule_set_id, rule_number)
        rules = [rules] if rules else []
    else:
        rules = await service.get_rules_in_set(
            rule_set_id, 
            limit, 
            offset, 
            filter_date_obj, 
            search_text,
            include_superseded
        )
    
    return [
        RuleResponse(
            id=rule.id,
            rule_set_id=rule.rule_set_id,
            rule_number=rule.rule_number,
            rule_title=rule.rule_title,
            rule_text=rule.rule_text,
            effective_start_date=rule.effective_start_date.isoformat() if rule.effective_start_date else None,
            effective_end_date=rule.effective_end_date.isoformat() if rule.effective_end_date else None,
            rulebook_hierarchy=rule.rulebook_hierarchy,
            category=rule.category,
            summary=rule.summary,
            is_current=rule.is_current,
            rule_metadata=rule.rule_metadata,
            created_at=rule.created_at.isoformat()
        )
        for rule in rules
    ]

@router.put("/rule-sets/{rule_set_id}/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_set_id: int,
    rule_id: int,
    rule_update: RuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a rule"""
    service = RuleSetService(db)
    
    updated = await service.update_rule(
        rule_id=rule_id,
        rule_title=rule_update.rule_title,
        rule_text=rule_update.rule_text,
        category=rule_update.category,
        metadata=rule_update.metadata
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    return RuleResponse(
        id=updated.id,
        rule_set_id=updated.rule_set_id,
        rule_number=updated.rule_number,
        rule_title=updated.rule_title,
        rule_text=updated.rule_text,
        category=updated.category,
        summary=updated.summary,
        is_current=updated.is_current,
        created_at=updated.created_at.isoformat()
    )

@router.delete("/rule-sets/{rule_set_id}/rules/{rule_id}")
async def delete_rule(
    rule_set_id: int,
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a rule"""
    service = RuleSetService(db)
    
    deleted = await service.delete_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    return {"message": "Rule deleted successfully"}

@router.get("/rule-sets/{rule_set_id}/catalog")
async def get_rule_catalog(
    rule_set_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get lightweight catalog of rules for LLM classification"""
    service = RuleSetService(db)
    
    catalog = await service.get_rule_catalog(rule_set_id)
    return {"catalog": catalog, "count": len(catalog)}