#!/usr/bin/env python3
"""
Unified FINRA Rules Loader
Handles all JSON formats and loads rules into the database

Usage:
    python load_finra_rules.py [options]
    
Options:
    --rule-set-id ID   Rule set ID to load into (default: 5)
    --batch-size N      Number of rules to process before committing (default: 20)
    --skip-preprocessing  Disable GPT preprocessing (recommended for bulk loads)
    --verbose           Show detailed progress
"""

import asyncio
import json
import sys
import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from html.parser import HTMLParser

# Setup path for imports
if '/app' not in sys.path:
    sys.path.insert(0, '/app')

from app.db.database import async_session_factory
from sqlalchemy import select, func, text
from app.db.models import Rule, RuleSet
from app.services.rule_set_service import RuleSetService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HTMLStripper(HTMLParser):
    """Strip HTML tags from text"""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, d):
        self.text.append(d)

    def get_data(self):
        return ''.join(self.text)


class FinraRulesLoader:
    """Unified loader for FINRA rules from JSON files"""
    
    def __init__(self, rule_set_id: int = 5, batch_size: int = 20, skip_preprocessing: bool = True):
        self.rule_set_id = rule_set_id
        self.batch_size = batch_size
        self.skip_preprocessing = skip_preprocessing
        self.rules_dir = Path("/app/data/dmp-finra/FinraRulesBook-set")
        
        # If running locally (not in Docker)
        if not self.rules_dir.exists():
            self.rules_dir = Path("/home/nervous/finra-compliance/data/dmp-finra/FinraRulesBook-set")
        
        self.loaded_rules = set()
        self.stats = {
            'initial_count': 0,
            'files_processed': 0,
            'array_files': 0,
            'object_files': 0,
            'rules_added': 0,
            'rules_skipped': 0,
            'errors': 0,
            'error_details': []
        }
    
    async def load_all(self):
        """Main entry point - load all FINRA rules"""
        logger.info("="*60)
        logger.info("FINRA Rules Loader Starting")
        logger.info("="*60)
        
        async with async_session_factory() as db:
            # Verify rule set exists
            rule_set = await self._verify_rule_set(db)
            if not rule_set:
                logger.error(f"Rule set {self.rule_set_id} not found!")
                return False
            
            logger.info(f"Loading into rule set: {rule_set.name}")
            
            # Optionally disable preprocessing
            if self.skip_preprocessing and rule_set.preprocessing_prompt:
                await db.execute(
                    text("UPDATE rule_sets SET preprocessing_prompt = NULL WHERE id = :id"),
                    {"id": self.rule_set_id}
                )
                await db.commit()
                logger.info("Disabled preprocessing for faster loading")
            
            # Get initial state
            await self._get_initial_state(db)
            
            # Process all JSON files
            await self._process_all_files(db)
            
            # Final report
            await self._print_final_report(db)
        
        return True
    
    async def _verify_rule_set(self, db) -> Optional[RuleSet]:
        """Verify the rule set exists"""
        result = await db.execute(
            select(RuleSet).where(RuleSet.id == self.rule_set_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_initial_state(self, db):
        """Get current state of rules in database"""
        # Count existing rules
        self.stats['initial_count'] = await db.scalar(
            select(func.count(Rule.id)).where(Rule.rule_set_id == self.rule_set_id)
        )
        
        # Get list of loaded rule numbers
        result = await db.execute(
            select(Rule.rule_number).where(Rule.rule_set_id == self.rule_set_id)
        )
        self.loaded_rules = set(r[0] for r in result)
        
        logger.info(f"Starting with {self.stats['initial_count']} rules already loaded")
    
    async def _process_all_files(self, db):
        """Process all JSON files in the rules directory"""
        if not self.rules_dir.exists():
            logger.error(f"Rules directory not found: {self.rules_dir}")
            return
        
        json_files = sorted(self.rules_dir.glob("*.json"))
        total_files = len(json_files)
        logger.info(f"Found {total_files} JSON files to process")
        
        batch_count = 0
        
        for i, json_file in enumerate(json_files, 1):
            self.stats['files_processed'] += 1
            
            # Progress indicator
            if i % 50 == 0:
                logger.info(f"Progress: {i}/{total_files} files processed...")
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Process based on format
                if isinstance(data, list):
                    self.stats['array_files'] += 1
                    for rule_data in data:
                        if await self._process_rule(db, rule_data, json_file.stem):
                            batch_count += 1
                else:
                    self.stats['object_files'] += 1
                    if await self._process_rule(db, data, json_file.stem):
                        batch_count += 1
                
                # Commit batch
                if batch_count >= self.batch_size:
                    await db.commit()
                    logger.debug(f"Committed batch of {batch_count} rules")
                    batch_count = 0
                    
            except json.JSONDecodeError as e:
                self.stats['errors'] += 1
                self.stats['error_details'].append(f"{json_file.name}: Invalid JSON")
                logger.debug(f"Invalid JSON in {json_file.name}")
            except Exception as e:
                self.stats['errors'] += 1
                error_msg = f"{json_file.name}: {str(e)[:100]}"
                if "duplicate key" not in str(e).lower():
                    self.stats['error_details'].append(error_msg)
                    logger.debug(f"Error processing {json_file.name}: {e}")
                await db.rollback()
                batch_count = 0
        
        # Final commit
        if batch_count > 0:
            await db.commit()
            logger.debug(f"Committed final batch of {batch_count} rules")
    
    async def _process_rule(self, db, rule_data: Any, filename_stem: str) -> bool:
        """Process a single rule data object"""
        if not isinstance(rule_data, dict):
            return False
        
        # Extract rule number
        rule_number = (
            rule_data.get('ruleNo') or 
            rule_data.get('rule_number') or 
            rule_data.get('id') or
            rule_data.get('number') or
            filename_stem.replace('_finraRulebook', '')
        )
        
        if not rule_number:
            return False
        
        # Skip if already loaded
        if rule_number in self.loaded_rules:
            self.stats['rules_skipped'] += 1
            return False
        
        # Extract rule content
        rule_title = (
            rule_data.get('ruleTitle') or
            rule_data.get('rule_title') or
            rule_data.get('title') or
            rule_data.get('name') or
            f"Rule {rule_number}"
        )
        
        rule_text = (
            rule_data.get('ruleTextAscii') or
            rule_data.get('rule_text_ascii') or
            rule_data.get('rule_text') or
            rule_data.get('text') or
            rule_data.get('content') or
            rule_data.get('description') or
            ""
        )
        
        # Clean HTML and metadata from rule text
        rule_text = self._clean_rule_text(rule_text)
        
        # Skip empty rules after cleaning
        if not rule_text or len(rule_text.strip()) < 10:
            self.stats['rules_skipped'] += 1
            return False
        
        # Create rule
        try:
            new_rule = Rule(
                rule_set_id=self.rule_set_id,
                rule_number=str(rule_number),
                rule_title=rule_title[:500] if rule_title else f"Rule {rule_number}",
                rule_text=rule_text,
                original_rule_text=None if self.skip_preprocessing else rule_text,
                summary=rule_title[:200] if rule_title else "",
                category=rule_data.get('category', 'general'),
                is_current=rule_data.get('is_current', True),
                rulebook_hierarchy=rule_data.get('rulebookHierarchy') or rule_data.get('parentTopic', ''),
                rule_metadata=rule_data.get('metadata', {})
            )
            
            db.add(new_rule)
            self.loaded_rules.add(rule_number)
            self.stats['rules_added'] += 1
            return True
            
        except Exception as e:
            logger.debug(f"Failed to create rule {rule_number}: {e}")
            return False
    
    def _clean_rule_text(self, text: str) -> str:
        """Remove HTML tags, metadata patterns, and clean up rule text"""
        if not text:
            return ""
        
        # Step 1: Strip HTML tags
        s = HTMLStripper()
        s.feed(text)
        cleaned = s.get_data()
        
        # Step 2: Remove common metadata patterns
        patterns_to_remove = [
            # Version/effective date notices
            r'This version of the rule.*?does not become effective until.*?\.(\ *To view other versions.*?\.)? ',
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
            # Footnote references
            r'\[Footnote \d+\]',
            r'Footnote \d+:',
            # Rule number prefix (e.g., "Rule 3110." at the beginning)
            r'^Rule \d{4}[a-z]?\.\s*',
            # Supplementary material headers
            r'Supplementary Material:?',
            r'\. 0[1-9]\d* ',  # Numbered subsection markers like ".01"
        ]
        
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        
        # Step 3: Clean up whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Collapse multiple spaces
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # Limit consecutive newlines
        cleaned = cleaned.strip()
        
        # Step 4: Fix common HTML entity issues
        cleaned = cleaned.replace('&nbsp;', ' ')
        cleaned = cleaned.replace('&amp;', '&')
        cleaned = cleaned.replace('&lt;', '<')
        cleaned = cleaned.replace('&gt;', '>')
        cleaned = cleaned.replace('&quot;', '"')
        cleaned = cleaned.replace("&apos;", "'")
        
        return cleaned
    
    async def _print_final_report(self, db):
        """Print final loading report"""
        # Get final count
        final_count = await db.scalar(
            select(func.count(Rule.id)).where(Rule.rule_set_id == self.rule_set_id)
        )
        
        logger.info("\n" + "="*60)
        logger.info("LOADING COMPLETE")
        logger.info("="*60)
        logger.info(f"Files processed: {self.stats['files_processed']}")
        logger.info(f"  - Array format: {self.stats['array_files']}")
        logger.info(f"  - Object format: {self.stats['object_files']}")
        logger.info(f"Rules:")
        logger.info(f"  - Started with: {self.stats['initial_count']}")
        logger.info(f"  - Added: {self.stats['rules_added']}")
        logger.info(f"  - Skipped: {self.stats['rules_skipped']}")
        logger.info(f"  - Total now: {final_count}")
        logger.info(f"Errors: {self.stats['errors']}")
        
        if self.stats['error_details'] and len(self.stats['error_details']) <= 10:
            logger.info("Error details:")
            for error in self.stats['error_details']:
                logger.info(f"  - {error}")
        
        # Check for key rules
        logger.info("\nKey Rules Check:")
        key_rules = ['2010', '2111', '2210', '3150', '3160', '4512', '4513', '5210']
        for rule_num in key_rules:
            exists = await db.scalar(
                select(func.count(Rule.id)).where(
                    Rule.rule_set_id == self.rule_set_id,
                    Rule.rule_number == rule_num
                )
            )
            if exists:
                logger.info(f"  ✓ Rule {rule_num}")
            else:
                logger.info(f"  ✗ Rule {rule_num} (not found)")


async def main():
    """Main entry point with CLI arguments"""
    parser = argparse.ArgumentParser(description='Load FINRA rules into database')
    parser.add_argument('--rule-set-id', type=int, default=5,
                        help='Rule set ID to load into (default: 5)')
    parser.add_argument('--batch-size', type=int, default=20,
                        help='Number of rules to process before committing (default: 20)')
    parser.add_argument('--skip-preprocessing', action='store_true', default=True,
                        help='Skip GPT preprocessing (faster loading)')
    parser.add_argument('--verbose', action='store_true',
                        help='Show detailed progress')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    loader = FinraRulesLoader(
        rule_set_id=args.rule_set_id,
        batch_size=args.batch_size,
        skip_preprocessing=args.skip_preprocessing
    )
    
    success = await loader.load_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())