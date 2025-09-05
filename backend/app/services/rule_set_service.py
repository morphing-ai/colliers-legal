# backend/app/services/rule_set_service.py
import json
import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, delete
from app.db.models import RuleSet, Rule
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class RuleSetService:
    """Service for managing rule sets and rules"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_service = LLMService()
        
    async def create_rule_set(
        self, 
        name: str, 
        description: Optional[str],
        created_by: str,
        preprocessing_prompt: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> RuleSet:
        """Create a new rule set"""
        rule_set = RuleSet(
            name=name,
            description=description,
            created_by=created_by,
            preprocessing_prompt=preprocessing_prompt,
            rule_set_metadata=metadata or {},
            is_active=True
        )
        self.db.add(rule_set)
        await self.db.commit()
        await self.db.refresh(rule_set)
        return rule_set
        
    async def get_rule_sets(self, user_id: Optional[str] = None) -> List[RuleSet]:
        """Get all rule sets, optionally filtered by user"""
        from sqlalchemy.orm import selectinload
        
        query = select(RuleSet).options(selectinload(RuleSet.rules)).where(RuleSet.is_active == True)
        if user_id:
            query = query.where(RuleSet.created_by == user_id)
        query = query.order_by(RuleSet.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().unique())
        
    async def get_rule_set(self, rule_set_id: int) -> Optional[RuleSet]:
        """Get a specific rule set by ID"""
        result = await self.db.execute(
            select(RuleSet).where(RuleSet.id == rule_set_id)
        )
        return result.scalar_one_or_none()
        
    async def delete_rule_set(self, rule_set_id: int) -> bool:
        """Delete a rule set and all its rules"""
        rule_set = await self.get_rule_set(rule_set_id)
        if not rule_set:
            return False
            
        await self.db.delete(rule_set)
        await self.db.commit()
        return True
        
    async def add_rules_from_json(
        self, 
        rule_set_id: int,
        json_data: List[Dict[str, Any]]
    ) -> int:
        """Add rules to a rule set from JSON data"""
        rule_set = await self.get_rule_set(rule_set_id)
        if not rule_set:
            raise ValueError(f"Rule set {rule_set_id} not found")
            
        rules_added = 0
        
        for rule_data in json_data:
            try:
                # Process each rule
                processed_rule = await self._process_rule_data(
                    rule_data, 
                    rule_set
                )
                if processed_rule:
                    self.db.add(processed_rule)
                    rules_added += 1
            except Exception as e:
                logger.error(f"Error processing rule: {e}")
                continue
                
        await self.db.commit()
        return rules_added
        
    async def add_rule_manually(
        self,
        rule_set_id: int,
        rule_number: str,
        rule_title: str,
        rule_text: str,
        category: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Rule:
        """Add a single rule manually"""
        rule_set = await self.get_rule_set(rule_set_id)
        if not rule_set:
            raise ValueError(f"Rule set {rule_set_id} not found")
            
        # Apply preprocessing and summarization
        processed_data = await self._preprocess_and_summarize_rule(
            rule_text,
            rule_title,
            rule_set.preprocessing_prompt
        )
        processed_text = processed_data.get('cleaned_text', rule_text)
        summary = processed_data.get('summary', '')
            
        rule = Rule(
            rule_set_id=rule_set_id,
            rule_number=rule_number,
            rule_title=rule_title,
            rule_text=processed_text,
            original_rule_text=rule_text if processed_text != rule_text else None,
            category=category or self._determine_category(rule_title, processed_text),
            summary=summary or self._create_summary(rule_title, processed_text),
            keywords=self._extract_keywords(rule_title, processed_text),
            rule_metadata=metadata or {},
            is_current=True
        )
        
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule
        
    async def _process_rule_data(
        self,
        rule_data: Dict[str, Any],
        rule_set: RuleSet
    ) -> Optional[Rule]:
        """Process rule data from JSON and create Rule object"""
        try:
            # Handle different JSON formats
            rule_number = (
                rule_data.get('ruleNumber') or 
                rule_data.get('rule_number') or
                rule_data.get('id') or
                rule_data.get('number')
            )
            
            rule_title = (
                rule_data.get('ruleTitle') or
                rule_data.get('rule_title') or
                rule_data.get('title') or
                rule_data.get('name')
            )
            
            rule_text = (
                rule_data.get('ruleTextAscii') or
                rule_data.get('rule_text_ascii') or
                rule_data.get('rule_text') or
                rule_data.get('text') or
                rule_data.get('content') or
                rule_data.get('description')
            )
            
            # Clean the rule text from metadata patterns
            if rule_text:
                rule_text = self._clean_rule_text(rule_text)
            
            if not rule_number or not rule_text:
                return None
                
            # Check if rule already exists in this set
            existing = await self.db.execute(
                select(Rule).where(
                    Rule.rule_set_id == rule_set.id,
                    Rule.rule_number == rule_number
                )
            )
            if existing.scalar_one_or_none():
                logger.info(f"Rule {rule_number} already exists in set {rule_set.name}")
                return None
                
            # Apply preprocessing - either custom or default cleaning
            processed_data = await self._preprocess_and_summarize_rule(
                rule_text,
                rule_title,
                rule_set.preprocessing_prompt
            )
            processed_text = processed_data.get('cleaned_text', rule_text)
            summary = processed_data.get('summary', '')
                
            # Parse dates if present
            effective_start = self._parse_date(
                rule_data.get('effectiveStartDate') or
                rule_data.get('effective_start_date') or
                rule_data.get('start_date')
            )
            
            effective_end = self._parse_date(
                rule_data.get('effectiveEndDate') or
                rule_data.get('effective_end_date') or
                rule_data.get('end_date')
            )
            
            # Get hierarchy
            hierarchy = (
                rule_data.get('rulebookHierarchy') or 
                rule_data.get('rulebook_hierarchy') or
                rule_data.get('hierarchy')
            )
            
            # Store additional metadata
            metadata = rule_data.get('metadata', {})
            metadata['detailedTopics'] = rule_data.get('detailedTopics')
            metadata['summaryTopics'] = rule_data.get('summaryTopics')
            if rule_data.get('ruleTextHtml'):
                metadata['hasHtmlVersion'] = True
            
            rule = Rule(
                rule_set_id=rule_set.id,
                rule_number=rule_number,
                rule_title=rule_title or f"Rule {rule_number}",
                rule_text=processed_text,
                original_rule_text=rule_text if processed_text != rule_text else None,
                effective_start_date=effective_start,
                effective_end_date=effective_end,
                rulebook_hierarchy=hierarchy,
                category=self._determine_category(rule_title, processed_text),
                summary=summary or self._create_summary(rule_title, processed_text),
                keywords=self._extract_keywords(rule_title, processed_text),
                rule_metadata=metadata,
                is_current=effective_end is None
            )
            
            return rule
            
        except Exception as e:
            logger.error(f"Error processing rule data: {e}")
            return None
            
    async def _preprocess_and_summarize_rule(
        self,
        rule_text: str,
        rule_title: Optional[str],
        custom_prompt: Optional[str] = None
    ) -> Dict[str, str]:
        """Clean and summarize rule text using LLM in a single pass"""
        try:
            if custom_prompt:
                # Use custom preprocessing if provided
                prompt = f"{custom_prompt}\n\nRule text:\n{rule_text}"
                processed = await self.llm_service.preprocess_rule(prompt)
                return {
                    'cleaned_text': processed or rule_text,
                    'summary': self._create_summary(rule_title, processed or rule_text)
                }
            else:
                # Default intelligent cleaning and summarization
                prompt = f"""Process this FINRA rule text by:
1. Remove all metadata that doesn't belong in the rule content (effective dates, version notices, footnote markers, amendment notices, etc.)
2. Keep only the actual regulatory requirements and procedures
3. Create a 2-3 sentence summary for LLM classification

Rule Title: {rule_title or 'N/A'}
Rule Text: {rule_text}

Return JSON with:
- "cleaned_text": The cleaned rule text
- "summary": A 2-3 sentence summary focusing on what the rule requires"""
                
                result = await self.llm_service.preprocess_rule_with_structure(prompt)
                if result and isinstance(result, dict):
                    return {
                        'cleaned_text': result.get('cleaned_text', rule_text),
                        'summary': result.get('summary', '')
                    }
                else:
                    # Fallback to basic cleaning
                    cleaned = self._clean_rule_text(rule_text)
                    return {
                        'cleaned_text': cleaned,
                        'summary': self._create_summary(rule_title, cleaned)
                    }
        except Exception as e:
            logger.error(f"Error preprocessing rule: {e}")
            # Fallback to basic cleaning
            cleaned = self._clean_rule_text(rule_text)
            return {
                'cleaned_text': cleaned,
                'summary': self._create_summary(rule_title, cleaned)
            }
            
    def _clean_rule_text(self, text: str) -> str:
        """Remove metadata patterns from rule text"""
        import re
        
        # Patterns to remove (metadata that belongs in rule_metadata, not in text)
        patterns_to_remove = [
            # Version/effective date notices
            r'This version of the rule.*?does not become effective until.*?\.(\s*To view other versions.*?\.)?',
            r'This rule.*?becomes effective on.*?\.',
            r'Effective Date:.*?\.',
            r'Adopted by SR-FINRA-\d{4}-\d{3,4}.*?\.',
            r'Approved by SEC.*?\.',
            r'Filed with SEC.*?\.',
            # Version dropdown instructions
            r'To view other versions.*?dropdown.*?\.',
            r'View previous versions.*?\.',
            # Amendment notices
            r'Amended by SR-FINRA.*?\.',
            r'As amended.*?\.',
            # Other administrative text
            r'See Regulatory Notice \d{2}-\d{2}.*?\.',
            r'See Notice to Members \d{2}-\d{2}.*?\.',
            # Footnote references (keep the content but remove "Footnote 1:" style markers)
            r'\[Footnote \d+\]',
            r'Footnote \d+:',
        ]
        
        cleaned = text
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None
        try:
            # Try different date formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except:
                    continue
            return None
        except:
            return None
            
    def _create_summary(self, title: str, text: str) -> str:
        """Create a concise summary of the rule for LLM classification"""
        # Take first 500 chars of text
        text_snippet = text[:500] if text else ""
        
        # Extract first meaningful sentences
        sentences = re.split(r'[.!?]+', text_snippet)
        summary = f"{title}. " if title else ""
        
        for sentence in sentences[:2]:
            if len(sentence.strip()) > 20:
                summary += sentence.strip() + ". "
                
        return summary[:300]  # Keep it concise
        
    def _determine_category(self, title: str, text: str) -> str:
        """Determine the category of the rule based on content"""
        combined = ((title or '') + ' ' + (text or '')).lower()
        
        # Category keywords mapping
        categories = {
            'supervision': ['supervision', 'supervisory', 'wsp', 'review', 'oversight'],
            'trading': ['trading', 'trade', 'execution', 'order', 'market'],
            'compliance': ['compliance', 'regulatory', 'requirement', 'violation'],
            'aml': ['anti-money', 'aml', 'laundering', 'suspicious', 'sar'],
            'customer': ['customer', 'client', 'account', 'suitability'],
            'communication': ['communication', 'correspondence', 'email', 'message'],
            'recordkeeping': ['record', 'retention', 'books', 'documentation'],
            'registration': ['registration', 'license', 'qualification'],
            'disclosure': ['disclosure', 'conflict', 'interest', 'material']
        }
        
        # Find best matching category
        for category, keywords in categories.items():
            if any(keyword in combined for keyword in keywords):
                return category
                
        return 'general'
        
    def _extract_keywords(self, title: str, text: str) -> List[str]:
        """Extract keywords from rule text for searching"""
        combined = ((title or '') + ' ' + (text or '')).lower()
        
        # Common compliance keywords to look for
        keywords = []
        keyword_patterns = [
            'supervision', 'compliance', 'trading', 'customer', 'account',
            'recordkeeping', 'books and records', 'anti-money laundering', 'aml',
            'communication', 'advertisement', 'correspondence', 'best execution',
            'suitability', 'know your customer', 'kyc', 'disclosure', 'conflict',
            'principal', 'registration', 'continuing education', 'audit',
            'violation', 'requirement', 'procedure', 'policy', 'review'
        ]
        
        for pattern in keyword_patterns:
            if pattern in combined:
                keywords.append(pattern)
                
        return keywords[:10]  # Limit to top 10 keywords
        
    async def get_rule_catalog(self, rule_set_id: int, filter_date: Optional[datetime] = None, include_superseded: bool = False) -> List[Dict]:
        """Get lightweight catalog of all rules in a set for LLM classification
        
        Args:
            rule_set_id: The ID of the rule set
            filter_date: Optional date to filter rules (only rules effective on this date)
            include_superseded: If False (default), exclude rules with an end date (superseded rules)
        """
        from sqlalchemy import and_, or_
        
        query = select(
            Rule.rule_number,
            Rule.rule_title,
            Rule.summary,
            Rule.category,
            Rule.is_current,
            Rule.effective_start_date,
            Rule.effective_end_date,
            Rule.rulebook_hierarchy
        ).where(
            Rule.rule_set_id == rule_set_id
        )
        
        # Apply date filtering if provided
        if filter_date:
            query = query.where(
                and_(
                    or_(Rule.effective_start_date == None, Rule.effective_start_date <= filter_date),
                    or_(Rule.effective_end_date == None, Rule.effective_end_date > filter_date)
                )
            )
        else:
            # Default to current rules only (no end date)
            if not include_superseded:
                query = query.where(Rule.effective_end_date == None)
            else:
                query = query.where(Rule.is_current == True)
            
        result = await self.db.execute(query)
        
        rules = []
        for row in result:
            rules.append({
                'number': row.rule_number,
                'title': row.rule_title,
                'summary': row.summary,
                'category': row.category,
                'hierarchy': row.rulebook_hierarchy,
                'start_date': row.effective_start_date.strftime("%Y-%m-%d") if row.effective_start_date else None,
                'end_date': row.effective_end_date.strftime("%Y-%m-%d") if row.effective_end_date else None,
                'is_current': row.is_current
            })
            
        return rules
        
    async def get_rule_by_number(self, rule_set_id: int, rule_number: str) -> Optional[Rule]:
        """Get a single rule by exact rule number"""
        result = await self.db.execute(
            select(Rule).where(
                Rule.rule_set_id == rule_set_id,
                Rule.rule_number == rule_number
            )
        )
        return result.scalar_one_or_none()
    
    async def get_rules_by_numbers(
        self,
        rule_set_id: int,
        rule_numbers: List[str],
        filter_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Get full rule details for specific rule numbers in a set"""
        query = select(Rule).where(
            Rule.rule_set_id == rule_set_id,
            Rule.rule_number.in_(rule_numbers)
        )
        
        # Apply date filter if provided
        if filter_date:
            query = query.where(
                (Rule.effective_start_date <= filter_date) | (Rule.effective_start_date.is_(None)),
                (Rule.effective_end_date >= filter_date) | (Rule.effective_end_date.is_(None))
            )
        
        result = await self.db.execute(query)
        
        rules = []
        for rule in result.scalars():
            rules.append({
                'rule_number': rule.rule_number,
                'rule_title': rule.rule_title,
                'rule_text': rule.rule_text,
                'effective_date': rule.effective_start_date.strftime("%Y-%m-%d") if rule.effective_start_date else "N/A",
                'category': rule.category,
                'is_current': rule.is_current
            })
            
        return rules
        
    async def get_rules_in_set(
        self,
        rule_set_id: int,
        limit: int = 100,
        offset: int = 0,
        filter_date: Optional[datetime] = None,
        search_text: Optional[str] = None,
        include_superseded: bool = False
    ) -> List[Rule]:
        """Get paginated list of rules in a set with optional filtering"""
        from sqlalchemy import and_, or_
        
        query = select(Rule).where(Rule.rule_set_id == rule_set_id)
        
        # Apply date filtering if provided
        if filter_date:
            query = query.where(
                and_(
                    or_(Rule.effective_start_date == None, Rule.effective_start_date <= filter_date),
                    or_(Rule.effective_end_date == None, Rule.effective_end_date > filter_date)
                )
            )
        elif not include_superseded:
            # By default, exclude superseded rules (those with an end date)
            query = query.where(Rule.effective_end_date == None)
        
        # Apply text search if provided - prioritize title/number matches
        if search_text:
            search_pattern = f"%{search_text}%"
            
            # First check if it's an exact rule number match
            exact_number_match = search_text.strip()
            
            # Create a CASE statement for ordering to prioritize matches
            from sqlalchemy import case
            
            # Priority ordering:
            # 1. Exact rule number match (priority 1)
            # 2. Rule number starts with search (priority 2)
            # 3. Rule title contains search (priority 3)
            # 4. Rule text contains search (priority 4)
            order_priority = case(
                (Rule.rule_number == exact_number_match, 1),
                (Rule.rule_number.ilike(f"{search_text}%"), 2),
                (Rule.rule_title.ilike(search_pattern), 3),
                (Rule.rule_text.ilike(search_pattern), 4),
                else_=5
            )
            
            query = query.where(
                or_(
                    Rule.rule_number.ilike(search_pattern),
                    Rule.rule_title.ilike(search_pattern),
                    Rule.rule_text.ilike(search_pattern)
                )
            ).order_by(order_priority, Rule.rule_number)
        else:
            query = query.order_by(Rule.rule_number)
        
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()
        
    async def delete_rule(self, rule_id: int) -> bool:
        """Delete a specific rule"""
        result = await self.db.execute(
            delete(Rule).where(Rule.id == rule_id)
        )
        await self.db.commit()
        return result.rowcount > 0
        
    async def update_rule(
        self,
        rule_id: int,
        rule_title: Optional[str] = None,
        rule_text: Optional[str] = None,
        category: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Rule]:
        """Update an existing rule"""
        result = await self.db.execute(
            select(Rule).where(Rule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            return None
            
        if rule_title is not None:
            rule.rule_title = rule_title
        if rule_text is not None:
            rule.rule_text = rule_text
            rule.summary = self._create_summary(rule.rule_title, rule_text)
            rule.keywords = self._extract_keywords(rule.rule_title, rule_text)
        if category is not None:
            rule.category = category
        if metadata is not None:
            rule.rule_metadata = metadata
            
        rule.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(rule)
        return rule