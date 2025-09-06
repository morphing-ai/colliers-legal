"""
Neurobot API endpoints for Morphing Digital Paralegal
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from app.db.database import get_db
from app.services.neurobot_service import neurobot_service
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class NeurobotCreateRequest(BaseModel):
    function_name: str
    description: str
    code: str
    neurobot_type: str = "analyze"
    example_usage: Optional[str] = None
    expected_parameters: Optional[Dict] = None


class NeurobotUpdateRequest(BaseModel):
    code: str
    change_notes: Optional[str] = None


class NeurobotExecuteRequest(BaseModel):
    function_name: str
    contract_text: str
    parameters: Optional[Dict] = None


class ContractAnalysisRequest(BaseModel):
    contract_text: str
    analysis_types: Optional[List[str]] = None


@router.get("/neurobots")
async def list_neurobots(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all available Neurobots."""
    try:
        query = "SELECT function_name, description, neurobot_type, created_by, run_count FROM neurobots WHERE is_active = true ORDER BY created_at DESC"
        result = await db.execute(query)
        neurobots = []
        for row in result:
            neurobots.append({
                'function_name': row[0],
                'description': row[1],
                'type': row[2],
                'author': row[3],
                'usage_count': row[4]
            })
        return {'neurobots': neurobots}
    except Exception as e:
        logger.error(f"Error listing neurobots: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/neurobots")
async def create_neurobot(
    request: NeurobotCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new Neurobot."""
    try:
        result = await neurobot_service.create_neurobot(
            db=db,
            function_name=request.function_name,
            description=request.description,
            code=request.code,
            neurobot_type=request.neurobot_type,
            created_by=current_user.get('email', 'unknown'),
            example_usage=request.example_usage,
            expected_parameters=request.expected_parameters
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
    except Exception as e:
        logger.error(f"Error creating neurobot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/neurobots/{function_name}")
async def update_neurobot(
    function_name: str,
    request: NeurobotUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an existing Neurobot."""
    try:
        result = await neurobot_service.update_neurobot(
            db=db,
            function_name=function_name,
            code=request.code,
            updated_by=current_user.get('email', 'unknown'),
            change_notes=request.change_notes
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
    except Exception as e:
        logger.error(f"Error updating neurobot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/neurobots/execute")
async def execute_neurobot(
    request: NeurobotExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Execute a specific Neurobot on contract text."""
    try:
        result = await neurobot_service.execute_neurobot(
            db=db,
            function_name=request.function_name,
            params={'contract_text': request.contract_text, **request.parameters} if request.parameters else {'contract_text': request.contract_text},
            contract_context={'user': current_user.get('email')}
        )
        
        return result
    except Exception as e:
        logger.error(f"Error executing neurobot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-contract")
async def analyze_contract(
    request: ContractAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Run comprehensive contract analysis using multiple Neurobots."""
    try:
        # Default analysis types if not specified
        if not request.analysis_types:
            analysis_types = [
                'detect_osha_compliance',
                'detect_indemnification_risks',
                'analyze_payment_terms',
                'detect_liquidated_damages',
                'detect_scope_creep',
                'analyze_dispute_resolution',
                'compare_to_baseline'
            ]
        else:
            analysis_types = request.analysis_types
        
        # Check for state-specific bots based on contract content
        contract_lower = request.contract_text.lower()
        if 'texas' in contract_lower or ' tx ' in contract_lower:
            analysis_types.append('analyze_texas_compliance')
        if 'florida' in contract_lower or ' fl ' in contract_lower:
            analysis_types.append('analyze_florida_compliance')
        
        # Execute all relevant Neurobots
        results = {}
        for bot_name in analysis_types:
            try:
                bot_result = await neurobot_service.execute_neurobot(
                    db=db,
                    function_name=bot_name,
                    params={'contract_text': request.contract_text},
                    contract_context={'user': current_user.get('email')}
                )
                
                if bot_result['success']:
                    results[bot_name] = bot_result['result']
                else:
                    results[bot_name] = {'error': bot_result.get('error', 'Execution failed')}
            except Exception as e:
                logger.warning(f"Bot {bot_name} failed: {str(e)}")
                results[bot_name] = {'error': str(e)}
        
        # Calculate overall risk score
        risk_score = calculate_risk_score(results)
        
        return {
            'analysis_results': results,
            'risk_score': risk_score,
            'timestamp': datetime.utcnow().isoformat(),
            'analyzed_by': current_user.get('email')
        }
        
    except Exception as e:
        logger.error(f"Error analyzing contract: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-contract-file")
async def analyze_contract_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Upload and analyze a contract file."""
    try:
        # Read file content
        content = await file.read()
        
        # Convert to text based on file type
        if file.filename.endswith('.txt'):
            contract_text = content.decode('utf-8')
        elif file.filename.endswith('.docx'):
            from docx import Document
            import io
            doc = Document(io.BytesIO(content))
            contract_text = '\n'.join([p.text for p in doc.paragraphs])
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload .txt or .docx")
        
        # Store contract in database
        query = """
            INSERT INTO contracts (id, filename, content, uploaded_by, upload_date)
            VALUES (gen_random_uuid()::text, :filename, :content, :user, NOW())
            RETURNING id
        """
        result = await db.execute(query, {
            'filename': file.filename,
            'content': contract_text,
            'user': current_user.get('email')
        })
        contract_id = result.scalar()
        await db.commit()
        
        # Analyze the contract
        analysis_request = ContractAnalysisRequest(contract_text=contract_text)
        analysis_result = await analyze_contract(analysis_request, db, current_user)
        
        # Update contract with analysis results
        update_query = """
            UPDATE contracts 
            SET analysis_results = :results
            WHERE id = :id
        """
        await db.execute(update_query, {
            'id': contract_id,
            'results': json.dumps(analysis_result)
        })
        await db.commit()
        
        return {
            'contract_id': contract_id,
            'filename': file.filename,
            **analysis_result
        }
        
    except Exception as e:
        logger.error(f"Error analyzing contract file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def calculate_risk_score(results: Dict) -> Dict:
    """Calculate overall risk score from Neurobot results."""
    high_risks = 0
    medium_risks = 0
    low_risks = 0
    
    for bot_name, result in results.items():
        if isinstance(result, dict) and 'error' not in result:
            # Count severity levels
            for key, value in result.items():
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            severity = item.get('severity', '').lower()
                            if severity == 'high':
                                high_risks += 1
                            elif severity == 'medium':
                                medium_risks += 1
                            elif severity == 'low':
                                low_risks += 1
    
    # Calculate overall score (0-100, higher is riskier)
    score = min(100, (high_risks * 20) + (medium_risks * 10) + (low_risks * 5))
    
    # Determine risk level
    if score >= 70:
        level = 'HIGH'
        color = 'red'
    elif score >= 40:
        level = 'MEDIUM'
        color = 'amber'
    else:
        level = 'LOW'
        color = 'green'
    
    return {
        'score': score,
        'level': level,
        'color': color,
        'high_risks': high_risks,
        'medium_risks': medium_risks,
        'low_risks': low_risks
    }