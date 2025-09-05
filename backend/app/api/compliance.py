# backend/app/api/compliance.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import date, datetime
import logging

from app.db.database import get_db
from app.api.auth import get_current_user
from app.services.compliance_service import ComplianceService
from app.services.rule_set_service import RuleSetService
from app.services.docx_export_service import DocxExportService

logger = logging.getLogger(__name__)

router = APIRouter()

class AnalyzeDocumentRequest(BaseModel):
    document_text: str
    rule_set_id: int
    effective_date: Optional[date] = None
    force_new: bool = False
    
class AnalyzeDocumentResponse(BaseModel):
    session_id: str
    status: str
    message: str

@router.post("/analyze", response_model=AnalyzeDocumentResponse)
async def analyze_document(
    request: AnalyzeDocumentRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Analyze a document for compliance against a rule set"""
    
    if not request.document_text or len(request.document_text.strip()) < 100:
        raise HTTPException(400, "Document text must be at least 100 characters")
        
    if len(request.document_text) > 500000:  # ~500KB limit
        raise HTTPException(400, "Document text is too large (max 500KB)")
    
    # Verify rule set exists
    rule_set_service = RuleSetService(db)
    rule_set = await rule_set_service.get_rule_set(request.rule_set_id)
    if not rule_set:
        raise HTTPException(404, "Rule set not found")
        
    try:
        compliance_service = ComplianceService(db)
        
        # Start analysis (returns immediately with session ID)
        session_id = await compliance_service.analyze_document(
            request.document_text,
            request.rule_set_id,
            current_user.id if hasattr(current_user, 'id') else "anonymous",
            force_new=request.force_new,
            effective_date=request.effective_date
        )
        
        return AnalyzeDocumentResponse(
            session_id=session_id,
            status="processing",
            message="Document analysis started. Use the session ID to check results."
        )
        
    except Exception as e:
        logger.error(f"Error analyzing document: {e}")
        raise HTTPException(500, "Failed to analyze document")

@router.get("/results/{session_id}")
async def get_analysis_results(
    session_id: str,
    current_user: Dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get analysis results by session ID"""
    
    try:
        compliance_service = ComplianceService(db)
        results = await compliance_service.get_analysis_results(session_id)
        
        if not results:
            raise HTTPException(404, "Analysis session not found")
            
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        raise HTTPException(500, "Failed to retrieve results")

@router.get("/history")
async def get_analysis_history(
    limit: int = 20,
    offset: int = 0,
    current_user: Dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get list of past analysis sessions for the current user"""
    
    try:
        compliance_service = ComplianceService(db)
        user_id = current_user.id if hasattr(current_user, 'id') else "anonymous"
        
        history = await compliance_service.get_user_analysis_history(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return history
        
    except Exception as e:
        logger.error(f"Error getting analysis history: {e}")
        raise HTTPException(500, "Failed to retrieve analysis history")

@router.delete("/history/{session_id}")
async def delete_analysis(
    session_id: str,
    current_user: Dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Delete an analysis session"""
    
    try:
        compliance_service = ComplianceService(db)
        user_id = current_user.id if hasattr(current_user, 'id') else "anonymous"
        
        deleted = await compliance_service.delete_analysis(session_id, user_id)
        
        if not deleted:
            raise HTTPException(404, "Analysis session not found or unauthorized")
            
        return {"message": "Analysis deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting analysis: {e}")
        raise HTTPException(500, "Failed to delete analysis")

@router.patch("/history/{session_id}")
async def update_analysis_title(
    session_id: str,
    title: str,
    current_user: Dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update the title of an analysis session"""
    
    try:
        compliance_service = ComplianceService(db)
        user_id = current_user.id if hasattr(current_user, 'id') else "anonymous"
        
        updated = await compliance_service.update_analysis_title(session_id, user_id, title)
        
        if not updated:
            raise HTTPException(404, "Analysis session not found or unauthorized")
            
        return {"message": "Analysis title updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating analysis title: {e}")
        raise HTTPException(500, "Failed to update analysis title")

@router.get("/results/{session_id}/export/docx")
async def export_results_to_docx(
    session_id: str,
    current_user: Dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Export analysis results to Word document"""
    from fastapi.responses import Response
    
    try:
        # Get the analysis results
        compliance_service = ComplianceService(db)
        results = await compliance_service.get_analysis_results(session_id)
        
        if not results:
            raise HTTPException(404, "Analysis session not found")
        
        # Get rule set name
        rule_set_service = RuleSetService(db)
        rule_set = await rule_set_service.get_rule_set(results.get('rule_set_id'))
        rule_set_name = rule_set.name if rule_set else "Unknown Rule Set"
        
        # Generate the Word document
        docx_service = DocxExportService()
        docx_bytes = await docx_service.export_analysis(results, rule_set_name)
        
        # Return as downloadable file
        filename = f"compliance_analysis_{session_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting to Word: {e}")
        raise HTTPException(500, "Failed to export document")

@router.post("/analysis/{session_id}/stop")
async def stop_analysis(
    session_id: str,
    current_user: Dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Stop an ongoing analysis"""
    
    try:
        compliance_service = ComplianceService(db)
        user_id = current_user.id if hasattr(current_user, 'id') else "anonymous"
        
        stopped = await compliance_service.stop_analysis(session_id, user_id)
        
        if not stopped:
            raise HTTPException(404, "Analysis session not found, unauthorized, or already completed")
            
        return {"message": "Analysis stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping analysis: {e}")
        raise HTTPException(500, "Failed to stop analysis")

# Deprecated endpoints - replaced by rule sets functionality
# These can be removed once the frontend is updated