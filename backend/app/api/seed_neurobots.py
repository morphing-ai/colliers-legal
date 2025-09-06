"""
Seed endpoint to populate initial Neurobots
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.database import get_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def get_seed_neurobots():
    """Get the initial set of Neurobots."""
    return [
        {
            'function_name': 'detect_osha_compliance',
            'description': 'Detects OSHA compliance requirements in construction contracts',
            'neurobot_type': 'analyze',
            'created_by': 'Sarah Johnson, Senior Paralegal',
            'code': '''
async def detect_osha_compliance(contract_text, context):
    """Detects OSHA compliance issues. Author: Sarah Johnson - 15 years experience"""
    issues = []
    osha_indicators = ['workplace safety', 'occupational health', 'safety requirements', 'PPE']
    for indicator in osha_indicators:
        if indicator.lower() in contract_text.lower():
            issues.append({
                'type': 'OSHA Compliance',
                'indicator': indicator,
                'severity': 'high',
                'recommendation': 'Ensure compliance with 29 CFR 1926'
            })
    if 'osha' not in contract_text.lower():
        issues.append({
            'type': 'Missing OSHA Provisions',
            'severity': 'medium',
            'recommendation': 'Contract should reference OSHA compliance'
        })
    return {'issues': issues, 'bot_author': 'Sarah Johnson'}
'''
        },
        {
            'function_name': 'detect_indemnification_risks',
            'description': 'Identifies problematic indemnification clauses',
            'neurobot_type': 'analyze',
            'created_by': 'Mike Chen, Contract Specialist',
            'code': '''
async def detect_indemnification_risks(contract_text, context):
    """Detects high-risk indemnification. Author: Mike Chen - 20 years experience"""
    risks = []
    if 'indemnif' in contract_text.lower():
        clause_start = max(0, contract_text.lower().find('indemnif') - 200)
        clause_end = min(len(contract_text), contract_text.lower().find('indemnif') + 200)
        clause = contract_text[clause_start:clause_end]
        if any(term in clause.lower() for term in ['sole negligence', 'unconditional', 'unlimited']):
            risks.append({
                'type': 'Broad Indemnification',
                'severity': 'high',
                'issue': 'Overly broad indemnification',
                'recommendation': 'Limit to proportional fault'
            })
    return {'risks': risks, 'bot_author': 'Mike Chen'}
'''
        },
        {
            'function_name': 'analyze_payment_terms',
            'description': 'Analyzes payment terms and prompt payment compliance',
            'neurobot_type': 'analyze',
            'created_by': 'Jennifer Lee, Financial Analyst',
            'code': '''
async def analyze_payment_terms(contract_text, context):
    """Analyzes payment terms. Author: Jennifer Lee - 12 years experience"""
    payment_issues = []
    if 'net 90' in contract_text.lower():
        payment_issues.append({
            'type': 'Extended Payment Terms',
            'severity': 'high',
            'issue': 'Net 90 may violate prompt payment laws',
            'recommendation': 'Most states require payment within 30-45 days'
        })
    if 'pay if paid' in contract_text.lower():
        payment_issues.append({
            'type': 'Contingent Payment',
            'severity': 'high',
            'issue': 'Payment contingent on owner payment',
            'recommendation': 'Negotiate pay-when-paid with time limit'
        })
    return {'payment_analysis': payment_issues, 'bot_author': 'Jennifer Lee'}
'''
        },
        {
            'function_name': 'detect_scope_creep',
            'description': 'Identifies potential for scope creep in contracts',
            'neurobot_type': 'analyze',
            'created_by': 'Tom Wilson, Project Manager',
            'code': '''
async def detect_scope_creep(contract_text, context):
    """Detects scope creep potential. Author: Tom Wilson - 20 years PM experience"""
    scope_risks = []
    vague_terms = ['including but not limited to', 'as may be required', 'work as directed']
    for term in vague_terms:
        if term in contract_text.lower():
            scope_risks.append({
                'type': 'Vague Scope Language',
                'severity': 'high',
                'problematic_phrase': term,
                'recommendation': 'Define scope with specific deliverables'
            })
    if 'change order' not in contract_text.lower():
        scope_risks.append({
            'type': 'Missing Change Order Process',
            'severity': 'high',
            'recommendation': 'Add detailed change order procedures'
        })
    return {'scope_analysis': scope_risks, 'bot_author': 'Tom Wilson'}
'''
        },
        {
            'function_name': 'detect_liquidated_damages',
            'description': 'Identifies and analyzes liquidated damages provisions',
            'neurobot_type': 'analyze',
            'created_by': 'David Kim, Risk Manager',
            'code': '''
async def detect_liquidated_damages(contract_text, context):
    """Detects liquidated damages. Author: David Kim - 15 years risk management"""
    ld_analysis = []
    if 'liquidated damages' in contract_text.lower():
        ld_analysis.append({
            'type': 'Liquidated Damages Present',
            'severity': 'high',
            'risk': 'Potential for significant penalties',
            'recommendation': 'Ensure amount is reasonable estimate of actual damages'
        })
        if 'per day' in contract_text.lower() or 'daily' in contract_text.lower():
            ld_analysis.append({
                'type': 'Daily Liquidated Damages',
                'severity': 'high',
                'risk': 'Accumulating daily penalties',
                'recommendation': 'Negotiate cap at percentage of contract value'
            })
    return {'liquidated_damages': ld_analysis, 'bot_author': 'David Kim'}
'''
        },
        {
            'function_name': 'analyze_dispute_resolution',
            'description': 'Analyzes dispute resolution and jurisdiction clauses',
            'neurobot_type': 'analyze',
            'created_by': 'Lisa Chang, Litigation Paralegal',
            'code': '''
async def analyze_dispute_resolution(contract_text, context):
    """Analyzes dispute resolution. Author: Lisa Chang - 10 years litigation"""
    dispute_analysis = []
    if 'arbitration' in contract_text.lower():
        dispute_analysis.append({
            'type': 'Arbitration Clause',
            'severity': 'medium',
            'note': 'Binding arbitration waives jury trial',
            'recommendation': 'Ensure client understands implications'
        })
    if 'attorney fees' in contract_text.lower() or "attorneys' fees" in contract_text.lower():
        dispute_analysis.append({
            'type': 'Fee Shifting Provision',
            'note': 'Prevailing party recovers fees',
            'risk': 'Increases litigation risk'
        })
    return {'dispute_resolution': dispute_analysis, 'bot_author': 'Lisa Chang'}
'''
        },
        {
            'function_name': 'compare_to_baseline',
            'description': 'Compares contract clauses to learned baselines',
            'neurobot_type': 'compare',
            'created_by': 'System Intelligence',
            'code': '''
async def compare_to_baseline(contract_text, context):
    """Compares to baseline patterns. Author: System Intelligence"""
    comparisons = []
    problematic_terms = {
        'payment': ['net 60', 'net 90', 'pay if paid'],
        'indemnification': ['sole', 'unconditional', 'unlimited'],
        'termination': ['for convenience', 'without cause']
    }
    for category, terms in problematic_terms.items():
        for term in terms:
            if term in contract_text.lower():
                comparisons.append({
                    'category': category,
                    'found': term,
                    'severity': 'high',
                    'deviation': 'Non-standard provision'
                })
    return {'baseline_comparison': comparisons}
'''
        }
    ]

@router.post("/seed")
async def seed_neurobots(db: AsyncSession = Depends(get_db)):
    """Seed the database with initial Neurobots."""
    try:
        # First check if we already have neurobots
        check_query = text("SELECT COUNT(*) FROM neurobots")
        result = await db.execute(check_query)
        count = result.scalar()
        
        if count > 0:
            return {"message": f"Database already has {count} Neurobots"}
        
        # Get seed neurobots
        neurobots = get_seed_neurobots()
        
        # Insert each neurobot
        inserted = 0
        for bot in neurobots:
            try:
                insert_query = text("""
                    INSERT INTO neurobots (
                        function_name, description, code, neurobot_type,
                        created_by, is_active, run_count, feedback_plus,
                        feedback_minus, created_at, updated_at
                    ) VALUES (
                        :function_name, :description, :code, :neurobot_type,
                        :created_by, true, 0, 0, 0, NOW(), NOW()
                    )
                """)
                await db.execute(insert_query, bot)
                inserted += 1
                logger.info(f"Created Neurobot: {bot['function_name']}")
            except Exception as e:
                logger.error(f"Error creating {bot['function_name']}: {str(e)}")
        
        await db.commit()
        
        return {
            "message": f"Successfully seeded {inserted} Neurobots",
            "neurobots": [bot['function_name'] for bot in neurobots[:inserted]]
        }
        
    except Exception as e:
        logger.error(f"Error seeding neurobots: {str(e)}")
        await db.rollback()
        raise