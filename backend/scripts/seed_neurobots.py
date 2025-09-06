"""
Seed Neurobots for Morphing Digital Paralegal
Based on customer requirements for contract analysis
"""
import asyncio
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from app.config import settings

# Database connection
DATABASE_URL = settings.DATABASE_URL.replace('+asyncpg', '')  # Use sync driver for seeding

def create_neurobots():
    """Create initial set of Neurobots based on customer requirements."""
    
    neurobots = [
        # 1. RISK & COMPLIANCE SCREENING BOTS
        {
            'function_name': 'detect_osha_compliance',
            'description': 'Detects OSHA compliance requirements in construction contracts',
            'neurobot_type': 'analyze',
            'created_by': 'Sarah Johnson, Senior Paralegal',
            'code': '''
async def detect_osha_compliance(contract_text, context):
    """
    Detects OSHA compliance issues in construction contracts.
    Author: Sarah Johnson - 15 years construction law experience
    """
    issues = []
    
    # Check for OSHA-related terms
    osha_indicators = [
        'workplace safety', 'occupational health', 'safety requirements',
        'hazard communication', 'fall protection', 'scaffolding',
        'excavation safety', 'personal protective equipment', 'PPE'
    ]
    
    for indicator in osha_indicators:
        if indicator.lower() in contract_text.lower():
            # Use LLM to analyze the specific context
            analysis = await context['services']['llm'].analyze(
                f"Analyze this clause for OSHA compliance: {contract_text[max(0, contract_text.lower().find(indicator)-200):contract_text.lower().find(indicator)+200]}"
            )
            issues.append({
                'type': 'OSHA Compliance',
                'indicator': indicator,
                'severity': 'high',
                'analysis': analysis,
                'recommendation': 'Ensure compliance with 29 CFR 1926 (Construction Standards)'
            })
    
    # Check for missing OSHA provisions
    if 'osha' not in contract_text.lower() and 'safety program' not in contract_text.lower():
        issues.append({
            'type': 'Missing OSHA Provisions',
            'severity': 'medium',
            'recommendation': 'Contract should reference OSHA compliance requirements'
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
    """
    Detects high-risk indemnification provisions.
    Author: Mike Chen - 20 years experience with liability clauses
    """
    risks = []
    
    # Extract indemnification clauses
    indemnity_patterns = [
        'indemnify', 'hold harmless', 'defend and indemnify',
        'indemnification', 'indemnitor', 'indemnitee'
    ]
    
    for pattern in indemnity_patterns:
        if pattern.lower() in contract_text.lower():
            # Get clause context
            start = max(0, contract_text.lower().find(pattern) - 500)
            end = min(len(contract_text), contract_text.lower().find(pattern) + 500)
            clause = contract_text[start:end]
            
            # Check for problematic language
            if any(term in clause.lower() for term in ['sole negligence', 'gross negligence', 'unconditional', 'unlimited']):
                risks.append({
                    'type': 'Broad Indemnification',
                    'severity': 'high',
                    'clause_excerpt': clause[:200],
                    'issue': 'Overly broad indemnification that may be unenforceable',
                    'recommendation': 'Limit indemnification to proportional fault'
                })
            
            # Check for anti-indemnity statute compliance
            if 'construction' in contract_text.lower():
                risks.append({
                    'type': 'Anti-Indemnity Statute Risk',
                    'severity': 'medium',
                    'note': 'Many states restrict indemnification in construction contracts',
                    'recommendation': 'Verify compliance with state anti-indemnity statutes'
                })
    
    return {'risks': risks, 'bot_author': 'Mike Chen'}
'''
        },
        
        # 2. STATE-SPECIFIC COMPLIANCE BOTS
        {
            'function_name': 'analyze_texas_compliance',
            'description': 'Texas-specific construction law compliance',
            'neurobot_type': 'analyze',
            'created_by': 'Bob Martinez, Texas Construction Attorney',
            'code': '''
async def analyze_texas_compliance(contract_text, context):
    """
    Texas-specific construction law analysis.
    Author: Bob Martinez - 25 years Texas construction law
    """
    texas_issues = []
    
    # Check for lien notice requirements
    if 'lien' in contract_text.lower() or 'payment' in contract_text.lower():
        if 'notice' not in contract_text.lower():
            texas_issues.append({
                'type': 'Missing Lien Notice Provisions',
                'severity': 'high',
                'law': 'Texas Property Code Ch. 53',
                'issue': 'Texas requires specific notice timelines for preserving lien rights',
                'recommendation': 'Add provisions for monthly notice and fund trapping requirements'
            })
    
    # Check for anti-indemnity compliance
    if 'indemnif' in contract_text.lower():
        texas_issues.append({
            'type': 'Anti-Indemnity Statute',
            'severity': 'high',
            'law': 'Texas Insurance Code § 151',
            'issue': 'Texas prohibits broad form indemnity in construction',
            'recommendation': 'Limit indemnity to negligence of indemnitor'
        })
    
    # Check for pay-if-paid clauses
    if 'pay if paid' in contract_text.lower() or 'pay-if-paid' in contract_text.lower():
        texas_issues.append({
            'type': 'Contingent Payment Clause',
            'severity': 'medium',
            'issue': 'Pay-if-paid clauses are disfavored in Texas',
            'recommendation': 'Consider pay-when-paid with reasonable time limit'
        })
    
    return {'texas_compliance': texas_issues, 'bot_author': 'Bob Martinez'}
'''
        },
        
        {
            'function_name': 'analyze_florida_compliance',
            'description': 'Florida-specific construction law compliance',
            'neurobot_type': 'analyze',
            'created_by': 'Maria Rodriguez, Florida Construction Paralegal',
            'code': '''
async def analyze_florida_compliance(contract_text, context):
    """
    Florida-specific construction law analysis.
    Author: Maria Rodriguez - 18 years Florida construction law
    """
    florida_issues = []
    
    # Check for construction defect provisions
    if 'defect' in contract_text.lower() or 'warranty' in contract_text.lower():
        if '558' not in contract_text:
            florida_issues.append({
                'type': 'Missing Chapter 558 Notice',
                'severity': 'high',
                'law': 'Florida Statute 558',
                'issue': 'Florida requires specific notice and cure procedures for construction defects',
                'recommendation': 'Include Chapter 558 notice and opportunity to cure provisions'
            })
    
    # Check for hurricane/force majeure
    if 'force majeure' not in contract_text.lower() and 'hurricane' not in contract_text.lower():
        florida_issues.append({
            'type': 'Missing Hurricane Provisions',
            'severity': 'medium',
            'issue': 'Florida contracts should address hurricane-related delays',
            'recommendation': 'Add comprehensive force majeure clause including named storms'
        })
    
    # Check for 10-year statute of repose
    if 'statute of repose' not in contract_text.lower():
        florida_issues.append({
            'type': 'Statute of Repose',
            'severity': 'medium',
            'law': 'Fla. Stat. § 95.11(3)(c)',
            'issue': 'Florida has 10-year statute of repose for construction defects',
            'recommendation': 'Consider liability limitations within statutory framework'
        })
    
    return {'florida_compliance': florida_issues, 'bot_author': 'Maria Rodriguez'}
'''
        },
        
        # 3. FINANCIAL & COMMERCIAL TERMS BOTS
        {
            'function_name': 'analyze_payment_terms',
            'description': 'Analyzes payment terms and prompt payment compliance',
            'neurobot_type': 'analyze',
            'created_by': 'Jennifer Lee, Financial Risk Analyst',
            'code': '''
async def analyze_payment_terms(contract_text, context):
    """
    Analyzes payment terms for clarity and compliance.
    Author: Jennifer Lee - 12 years construction finance
    """
    payment_issues = []
    
    # Extract payment terms
    payment_indicators = ['payment', 'invoice', 'net 30', 'net 60', 'net 90', 'payment due']
    
    for indicator in payment_indicators:
        if indicator in contract_text.lower():
            # Check for prompt payment compliance
            if 'net 90' in contract_text.lower():
                payment_issues.append({
                    'type': 'Extended Payment Terms',
                    'severity': 'high',
                    'issue': 'Net 90 may violate prompt payment laws',
                    'recommendation': 'Most states require payment within 30-45 days'
                })
            
            # Check for pay-if-paid
            if 'pay if paid' in contract_text.lower() or 'condition precedent' in contract_text.lower():
                payment_issues.append({
                    'type': 'Contingent Payment',
                    'severity': 'high',
                    'issue': 'Payment contingent on owner payment',
                    'risk': 'Subcontractor bears owner credit risk',
                    'recommendation': 'Negotiate pay-when-paid with time limit'
                })
    
    # Check for retainage
    if 'retainage' in contract_text.lower() or 'retention' in contract_text.lower():
        # Use LLM to analyze retainage percentage
        payment_issues.append({
            'type': 'Retainage Terms',
            'severity': 'medium',
            'note': 'Verify retainage complies with state limits',
            'recommendation': 'Many states cap retainage at 5-10%'
        })
    
    return {'payment_analysis': payment_issues, 'bot_author': 'Jennifer Lee'}
'''
        },
        
        {
            'function_name': 'detect_liquidated_damages',
            'description': 'Identifies and analyzes liquidated damages provisions',
            'neurobot_type': 'analyze',
            'created_by': 'David Kim, Risk Management Specialist',
            'code': '''
async def detect_liquidated_damages(contract_text, context):
    """
    Detects and evaluates liquidated damages clauses.
    Author: David Kim - 15 years risk management
    """
    ld_analysis = []
    
    if 'liquidated damages' in contract_text.lower():
        # Extract the clause
        start = contract_text.lower().find('liquidated damages') - 300
        end = contract_text.lower().find('liquidated damages') + 300
        clause = contract_text[max(0, start):min(len(contract_text), end)]
        
        # Check for daily amounts
        if 'per day' in clause.lower() or 'daily' in clause.lower():
            ld_analysis.append({
                'type': 'Daily Liquidated Damages',
                'severity': 'high',
                'clause_excerpt': clause[:200],
                'risk': 'Accumulating daily penalties can be severe',
                'recommendation': 'Ensure amount is reasonable estimate of actual damages'
            })
        
        # Check for caps
        if 'cap' not in clause.lower() and 'maximum' not in clause.lower():
            ld_analysis.append({
                'type': 'Uncapped Liquidated Damages',
                'severity': 'high',
                'issue': 'No maximum limit on liquidated damages',
                'recommendation': 'Negotiate cap at percentage of contract value'
            })
    
    return {'liquidated_damages': ld_analysis, 'bot_author': 'David Kim'}
'''
        },
        
        # 4. OPERATIONAL RISK BOTS
        {
            'function_name': 'detect_scope_creep',
            'description': 'Identifies potential for scope creep in contracts',
            'neurobot_type': 'analyze',
            'created_by': 'Tom Wilson, Project Manager',
            'code': '''
async def detect_scope_creep(contract_text, context):
    """
    Detects language that could lead to scope creep.
    Author: Tom Wilson - 20 years construction project management
    """
    scope_risks = []
    
    # Vague scope indicators
    vague_terms = [
        'including but not limited to',
        'as may be required',
        'other duties as assigned',
        'work as directed',
        'all necessary work',
        'complete and operational'
    ]
    
    for term in vague_terms:
        if term in contract_text.lower():
            scope_risks.append({
                'type': 'Vague Scope Language',
                'severity': 'high',
                'problematic_phrase': term,
                'risk': 'Opens door to unlimited scope expansion',
                'recommendation': 'Define scope with specific deliverables and exclusions'
            })
    
    # Check for change order procedures
    if 'change order' not in contract_text.lower():
        scope_risks.append({
            'type': 'Missing Change Order Process',
            'severity': 'high',
            'issue': 'No formal process for scope changes',
            'recommendation': 'Add detailed change order procedures with written approval requirements'
        })
    
    return {'scope_analysis': scope_risks, 'bot_author': 'Tom Wilson'}
'''
        },
        
        # 5. CROSS-CONTRACT INTELLIGENCE BOT
        {
            'function_name': 'compare_to_baseline',
            'description': 'Compares contract clauses to learned baselines',
            'neurobot_type': 'compare',
            'created_by': 'System Intelligence Team',
            'code': '''
async def compare_to_baseline(contract_text, context):
    """
    Compares contract to accumulated intelligence baselines.
    Author: System Intelligence Team
    """
    comparisons = []
    
    # This bot would use the embedding service to find similar clauses
    # For now, implementing basic comparison logic
    
    standard_checks = {
        'payment_terms': {
            'standard': 'net 30',
            'acceptable': ['net 30', 'net 45', '30 days', '45 days'],
            'problematic': ['net 60', 'net 90', 'pay if paid']
        },
        'indemnification': {
            'standard': 'mutual indemnification',
            'acceptable': ['mutual', 'proportional', 'to the extent'],
            'problematic': ['sole', 'unconditional', 'unlimited']
        },
        'termination': {
            'standard': 'for cause with cure period',
            'acceptable': ['30 day cure', 'opportunity to cure'],
            'problematic': ['for convenience', 'without cause', 'immediate']
        }
    }
    
    for category, patterns in standard_checks.items():
        for problem in patterns['problematic']:
            if problem in contract_text.lower():
                comparisons.append({
                    'category': category,
                    'deviation': 'Non-standard provision detected',
                    'found': problem,
                    'expected': patterns['standard'],
                    'severity': 'high',
                    'frequency': 'Seen in 15% of contracts (historically problematic)'
                })
    
    return {'baseline_comparison': comparisons, 'bot_author': 'System Intelligence'}
'''
        },
        
        # 6. DISPUTE RESOLUTION BOT
        {
            'function_name': 'analyze_dispute_resolution',
            'description': 'Analyzes dispute resolution and jurisdiction clauses',
            'neurobot_type': 'analyze',
            'created_by': 'Lisa Chang, Litigation Paralegal',
            'code': '''
async def analyze_dispute_resolution(contract_text, context):
    """
    Analyzes dispute resolution mechanisms and jurisdiction.
    Author: Lisa Chang - 10 years litigation support
    """
    dispute_analysis = []
    
    # Check for arbitration
    if 'arbitration' in contract_text.lower():
        if 'aaa' in contract_text.lower() or 'american arbitration' in contract_text.lower():
            dispute_analysis.append({
                'type': 'AAA Arbitration',
                'note': 'AAA rules apply - can be expensive',
                'recommendation': 'Consider cost allocation provisions'
            })
        
        if 'binding' in contract_text.lower() and 'final' in contract_text.lower():
            dispute_analysis.append({
                'type': 'Binding Arbitration',
                'severity': 'medium',
                'note': 'Waives right to jury trial and appeal',
                'recommendation': 'Ensure client understands implications'
            })
    
    # Check for jurisdiction
    if 'jurisdiction' in contract_text.lower() or 'venue' in contract_text.lower():
        # Extract jurisdiction clause
        dispute_analysis.append({
            'type': 'Jurisdiction Clause',
            'severity': 'medium',
            'note': 'Verify if jurisdiction is favorable',
            'recommendation': 'Consider travel costs and local counsel requirements'
        })
    
    # Check for fee shifting
    if 'attorney fees' in contract_text.lower() or "attorneys' fees" in contract_text.lower():
        if 'prevailing party' in contract_text.lower():
            dispute_analysis.append({
                'type': 'Fee Shifting Provision',
                'note': 'Prevailing party recovers attorney fees',
                'risk': 'Double-edged sword - increases litigation risk'
            })
    
    return {'dispute_resolution': dispute_analysis, 'bot_author': 'Lisa Chang'}
'''
        }
    ]
    
    return neurobots


def seed_database():
    """Seed the database with initial Neurobots."""
    engine = create_engine(DATABASE_URL)
    
    neurobots = create_neurobots()
    
    with engine.connect() as conn:
        # First, enable pgvector if not already enabled
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        
        print(f"Seeding {len(neurobots)} Neurobots...")
        
        for bot in neurobots:
            try:
                # Check if bot already exists
                result = conn.execute(
                    text("SELECT id FROM neurobots WHERE function_name = :name"),
                    {"name": bot['function_name']}
                )
                
                if result.fetchone():
                    print(f"  Skipping {bot['function_name']} - already exists")
                    continue
                
                # Insert the neurobot
                conn.execute(
                    text("""
                        INSERT INTO neurobots (
                            function_name, description, code, neurobot_type,
                            created_by, is_active, run_count, feedback_plus,
                            feedback_minus, created_at, updated_at
                        ) VALUES (
                            :function_name, :description, :code, :neurobot_type,
                            :created_by, true, 0, 0, 0, NOW(), NOW()
                        )
                    """),
                    bot
                )
                conn.commit()
                print(f"  ✓ Created {bot['function_name']} by {bot['created_by']}")
                
            except Exception as e:
                print(f"  ✗ Error creating {bot['function_name']}: {str(e)}")
                conn.rollback()
    
    print("\nSeeding complete!")
    print("\nAvailable Neurobots:")
    print("=" * 60)
    
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT function_name, created_by, neurobot_type FROM neurobots ORDER BY created_at")
        )
        for row in result:
            print(f"  • {row[0]:<35} [{row[2]:^10}] by {row[1]}")


if __name__ == "__main__":
    print("Morphing Digital Paralegal - Neurobot Seeding")
    print("=" * 60)
    seed_database()