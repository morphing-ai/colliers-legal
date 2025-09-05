#!/usr/bin/env python3
"""
Clean HTML and metadata from existing rules in the database

Usage:
    python clean_existing_rules.py [--rule-set-id ID] [--dry-run]
"""

import asyncio
import sys
import argparse
import re
from html.parser import HTMLParser
import logging

# Setup path for imports
if '/app' not in sys.path:
    sys.path.insert(0, '/app')

from app.db.database import async_session_factory
from sqlalchemy import select, text, update
from app.db.models import Rule

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


def clean_rule_text(text: str) -> str:
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


async def clean_rules(rule_set_id: int = None, dry_run: bool = False):
    """Clean HTML and metadata from existing rules"""
    async with async_session_factory() as db:
        # Build query
        query = select(Rule)
        if rule_set_id:
            query = query.where(Rule.rule_set_id == rule_set_id)
            logger.info(f"Cleaning rules for rule set ID: {rule_set_id}")
        else:
            logger.info("Cleaning rules for all rule sets")
        
        # Fetch all rules
        result = await db.execute(query)
        rules = result.scalars().all()
        
        logger.info(f"Found {len(rules)} rules to process")
        
        cleaned_count = 0
        unchanged_count = 0
        
        for rule in rules:
            original_text = rule.rule_text
            cleaned_text = clean_rule_text(original_text)
            
            # Check if cleaning made a difference
            if original_text != cleaned_text:
                cleaned_count += 1
                
                # Show sample of changes in dry run
                if dry_run and cleaned_count <= 5:
                    logger.info(f"\nRule {rule.rule_number} - {rule.rule_title}")
                    logger.info(f"  Original length: {len(original_text)}")
                    logger.info(f"  Cleaned length: {len(cleaned_text)}")
                    
                    # Show first 200 chars of difference
                    if len(original_text) > 200:
                        logger.info(f"  Original preview: {original_text[:200]}...")
                    if len(cleaned_text) > 200:
                        logger.info(f"  Cleaned preview: {cleaned_text[:200]}...")
                
                # Update rule if not dry run
                if not dry_run:
                    rule.rule_text = cleaned_text
                    
                    # Also update original_rule_text if it exists
                    if rule.original_rule_text:
                        rule.original_rule_text = cleaned_text
            else:
                unchanged_count += 1
        
        # Report results
        logger.info(f"\n{'='*60}")
        logger.info("CLEANING SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total rules processed: {len(rules)}")
        logger.info(f"Rules cleaned: {cleaned_count}")
        logger.info(f"Rules unchanged: {unchanged_count}")
        
        if dry_run:
            logger.info("\nDRY RUN - No changes were saved to the database")
        else:
            # Commit changes
            await db.commit()
            logger.info("\nChanges saved to database")


async def main():
    parser = argparse.ArgumentParser(description='Clean HTML and metadata from existing rules')
    parser.add_argument('--rule-set-id', type=int, help='Rule set ID to clean (default: all)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be cleaned without saving')
    
    args = parser.parse_args()
    
    await clean_rules(args.rule_set_id, args.dry_run)


if __name__ == '__main__':
    asyncio.run(main())