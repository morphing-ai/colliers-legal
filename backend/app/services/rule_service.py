# backend/app/services/rule_service.py
import json
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.db.models import FinraRule

logger = logging.getLogger(__name__)

class RuleService:
    """Service for managing FINRA rules"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.rules_path = os.getenv("FINRA_RULES_PATH", "/app/data/dmp-finra/FinraRulesBook-set")
        
    async def load_rules_from_json(self) -> int:
        """Load all FINRA rules from JSON files into database"""
        rules_loaded = 0
        rules_dir = Path(self.rules_path)
        
        if not rules_dir.exists():
            logger.error(f"Rules directory not found: {rules_dir}")
            return 0
            
        # Get all JSON files
        json_files = list(rules_dir.glob("*.json"))
        logger.info(f"Found {len(json_files)} rule files to process")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    rules_data = json.load(f)
                    
                # Handle both single rule and array of rules
                if isinstance(rules_data, list):
                    for rule_data in rules_data:
                        if await self._process_rule(rule_data):
                            rules_loaded += 1
                else:
                    if await self._process_rule(rules_data):
                        rules_loaded += 1
                        
            except Exception as e:
                logger.error(f"Error processing {json_file}: {e}")
                continue
                
        await self.db.commit()
        logger.info(f"Loaded {rules_loaded} rules into database")
        return rules_loaded
        
    async def _process_rule(self, rule_data: Dict) -> bool:
        """Process a single rule and store in database"""
        try:
            rule_number = rule_data.get('ruleNumber')
            if not rule_number:
                return False
                
            # Check if rule already exists
            existing = await self.db.execute(
                select(FinraRule).where(FinraRule.rule_number == rule_number)
            )
            if existing.scalar_one_or_none():
                return False
                
            # Extract and process rule data
            rule = FinraRule(
                rule_number=rule_number,
                rule_title=rule_data.get('ruleTitle', ''),
                effective_start_date=self._parse_date(rule_data.get('effectiveStartDate')),
                effective_end_date=self._parse_date(rule_data.get('effectiveEndDate')),
                rulebook_hierarchy=rule_data.get('rulebookHierarchy', ''),
                rule_text_ascii=rule_data.get('ruleTextAscii', ''),
                rule_text_html=rule_data.get('ruleTextHtml', ''),
                summary=self._create_summary(rule_data),
                category=self._determine_category(rule_data),
                keywords=self._extract_keywords(rule_data),
                is_current=rule_data.get('effectiveEndDate') is None
            )
            
            self.db.add(rule)
            return True
            
        except Exception as e:
            logger.error(f"Error processing rule: {e}")
            return False
            
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            return None
            
    def _create_summary(self, rule_data: Dict) -> str:
        """Create a concise summary of the rule for LLM classification"""
        rule_text = rule_data.get('ruleTextAscii', '')[:500]
        title = rule_data.get('ruleTitle', '')
        
        # Extract first meaningful sentences
        sentences = re.split(r'[.!?]+', rule_text)
        summary = f"{title}. "
        
        for sentence in sentences[:2]:
            if len(sentence.strip()) > 20:
                summary += sentence.strip() + ". "
                
        return summary[:300]  # Keep it concise
        
    def _determine_category(self, rule_data: Dict) -> str:
        """Determine the category of the rule based on its number and content"""
        rule_number = rule_data.get('ruleNumber', '')
        hierarchy = (rule_data.get('rulebookHierarchy') or '').lower()
        
        # Category mapping based on rule number ranges
        if rule_number.startswith('31'):
            return 'supervision'
        elif rule_number.startswith('32'):
            return 'responsibilities'
        elif rule_number.startswith('33'):
            return 'aml'
        elif rule_number.startswith('22'):
            return 'communications'
        elif rule_number.startswith('23'):
            return 'customer_accounts'
        elif rule_number.startswith('45') or rule_number.startswith('451'):
            return 'recordkeeping'
        elif rule_number.startswith('5'):
            return 'trading'
        elif hierarchy and 'supervision' in hierarchy:
            return 'supervision'
        elif hierarchy and ('trading' in hierarchy or 'market' in hierarchy):
            return 'trading'
        else:
            return 'general'
            
    def _extract_keywords(self, rule_data: Dict) -> List[str]:
        """Extract keywords from rule text for searching"""
        text = ((rule_data.get('ruleTextAscii') or '') + ' ' + (rule_data.get('ruleTitle') or '')).lower()
        
        # Common compliance keywords to look for
        keywords = []
        keyword_patterns = [
            'supervision', 'compliance', 'trading', 'customer', 'account',
            'recordkeeping', 'books and records', 'anti-money laundering', 'aml',
            'communication', 'advertisement', 'correspondence', 'best execution',
            'suitability', 'know your customer', 'kyc', 'disclosure', 'conflict',
            'principal', 'registration', 'continuing education', 'audit'
        ]
        
        for pattern in keyword_patterns:
            if pattern in text:
                keywords.append(pattern)
                
        return keywords[:10]  # Limit to top 10 keywords
        
    async def get_rule_catalog(self) -> List[Dict]:
        """Get lightweight catalog of all rules for LLM classification"""
        result = await self.db.execute(
            select(
                FinraRule.rule_number,
                FinraRule.rule_title,
                FinraRule.summary,
                FinraRule.category,
                FinraRule.is_current,
                FinraRule.effective_start_date
            ).where(FinraRule.is_current == True)
        )
        
        rules = []
        for row in result:
            rules.append({
                'number': row.rule_number,
                'title': row.rule_title,
                'summary': row.summary,
                'category': row.category,
                'date': row.effective_start_date.strftime("%Y-%m-%d") if row.effective_start_date else "N/A"
            })
            
        return rules
        
    async def get_rules_by_numbers(self, rule_numbers: List[str]) -> List[Dict]:
        """Get full rule details for specific rule numbers"""
        result = await self.db.execute(
            select(FinraRule).where(FinraRule.rule_number.in_(rule_numbers))
        )
        
        rules = []
        for rule in result.scalars():
            rules.append({
                'rule_number': rule.rule_number,
                'rule_title': rule.rule_title,
                'rule_text': rule.rule_text_ascii,
                'effective_date': rule.effective_start_date.strftime("%Y-%m-%d") if rule.effective_start_date else "N/A",
                'category': rule.category,
                'is_current': rule.is_current
            })
            
        return rules