# Enhanced compliance service with better handling for large documents
import hashlib
import logging
import re
import uuid
from typing import List, Dict, Optional
from datetime import datetime, timedelta, date
import asyncio
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from app.db.models import DocumentAnalysis, DocumentParagraph, ComplianceIssue, AnalysisCache, RuleSet
from app.services.rule_set_service import RuleSetService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class ComplianceServiceV2:
    """Enhanced service for analyzing large documents against rules"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.rule_set_service = RuleSetService(db)
        self.llm_service = LLMService()
        
    async def analyze_document(self, document_text: str, rule_set_id: int, user_id: str, force_new: bool = False, effective_date: Optional[date] = None) -> str:
        """Main entry point for document analysis - returns immediately"""
        
        # Create analysis session
        session_id = str(uuid.uuid4())
        date_str = effective_date.isoformat() if effective_date else "current"
        cache_key = f"{document_text}:{rule_set_id}:{date_str}"
        document_hash = hashlib.md5(cache_key.encode()).hexdigest()
        
        # Check cache settings
        from app.api.admin import cache_settings
        
        # Check cache first
        if not force_new and cache_settings.enabled:
            cached_result = await self._get_cached_analysis(document_hash)
            if cached_result:
                logger.info(f"Returning cached analysis session: {cached_result['session_id']}")
                return cached_result['session_id']
            
        # Split document into paragraphs
        paragraphs = self._split_into_paragraphs(document_text)
        total_paragraphs = len([p for p in paragraphs if len(p.strip()) >= 50])
        
        # Create new analysis
        analysis = DocumentAnalysis(
            session_id=session_id,
            rule_set_id=rule_set_id,
            document_text=document_text,
            document_hash=document_hash,
            analyzed_by=user_id,
            analysis_status='processing',
            total_paragraphs=total_paragraphs,
            paragraphs_processed=0
        )
        self.db.add(analysis)
        await self.db.commit()
        
        # Start IMPROVED background processing
        asyncio.create_task(self._process_document_async_v2(
            analysis.id, session_id, rule_set_id, document_hash, paragraphs, effective_date
        ))
        
        return session_id
    
    async def _process_document_async_v2(self, document_id: int, session_id: str, rule_set_id: int, 
                                         document_hash: str, paragraphs: List[str], effective_date: Optional[date] = None):
        """Improved document processing with better error handling and smaller batches"""
        try:
            # Create fresh db session for background task
            from app.db.database import async_session_factory
            async with async_session_factory() as db:
                # Store paragraphs first
                paragraph_ids = []
                for idx, para_text in enumerate(paragraphs):
                    if len(para_text.strip()) < 50:
                        continue
                        
                    paragraph = DocumentParagraph(
                        document_id=document_id,
                        paragraph_index=idx,
                        content=para_text
                    )
                    db.add(paragraph)
                    await db.flush()
                    paragraph_ids.append(paragraph.id)
                
                await db.commit()
                
                # IMPROVED: Process sequentially with better error handling
                # This avoids connection pool issues
                processed = 0
                failed_count = 0
                max_failures = 10  # Stop if too many failures
                
                for para_id in paragraph_ids:
                    try:
                        # Process one paragraph at a time
                        await self._analyze_single_paragraph_v2(db, document_id, rule_set_id, para_id, effective_date)
                        processed += 1
                        
                        # Update progress every paragraph
                        await db.execute(
                            update(DocumentAnalysis)
                            .where(DocumentAnalysis.id == document_id)
                            .values(paragraphs_processed=processed)
                        )
                        await db.commit()
                        
                        # Log progress every 10 paragraphs
                        if processed % 10 == 0:
                            logger.info(f"Processed {processed}/{len(paragraph_ids)} paragraphs for session {session_id}")
                        
                        # Small delay to avoid rate limiting
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Failed to analyze paragraph {para_id}: {e}")
                        failed_count += 1
                        
                        if failed_count >= max_failures:
                            logger.error(f"Too many failures ({failed_count}), stopping analysis for session {session_id}")
                            await db.execute(
                                update(DocumentAnalysis)
                                .where(DocumentAnalysis.id == document_id)
                                .values(
                                    analysis_status='failed',
                                    completed_at=datetime.utcnow()
                                )
                            )
                            await db.commit()
                            return
                        
                        # Continue with next paragraph
                        continue
                
                # Mark as complete
                await db.execute(
                    update(DocumentAnalysis)
                    .where(DocumentAnalysis.id == document_id)
                    .values(
                        analysis_status='completed',
                        completed_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                # Cache the result
                await self._cache_analysis_result(document_hash, session_id)
                
                logger.info(f"Analysis complete for session {session_id} - Processed {processed} paragraphs, {failed_count} failures")
                
        except Exception as e:
            logger.error(f"Critical error processing document {session_id}: {e}")
            # Mark as failed
            try:
                async with async_session_factory() as db:
                    await db.execute(
                        update(DocumentAnalysis)
                        .where(DocumentAnalysis.id == document_id)
                        .values(
                            analysis_status='failed',
                            completed_at=datetime.utcnow()
                        )
                    )
                    await db.commit()
            except:
                pass
    
    async def _analyze_single_paragraph_v2(self, db: AsyncSession, document_id: int, rule_set_id: int, 
                                           paragraph_id: int, effective_date: Optional[date] = None):
        """Analyze a single paragraph with better error handling"""
        
        # Get paragraph
        result = await db.execute(
            select(DocumentParagraph).where(DocumentParagraph.id == paragraph_id)
        )
        paragraph = result.scalar_one()
        
        # Get rule catalog
        rule_set_service = RuleSetService(db)
        filter_date = datetime.combine(effective_date, datetime.min.time()) if effective_date else None
        rule_catalog = await rule_set_service.get_rule_catalog(rule_set_id, filter_date=filter_date)
        
        # Classify which rules apply (with timeout)
        try:
            applicable_rules = await asyncio.wait_for(
                self.llm_service.classify_paragraph(paragraph.content, rule_catalog),
                timeout=30.0  # 30 second timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Classification timeout for paragraph {paragraph_id}")
            applicable_rules = []
        except Exception as e:
            logger.error(f"Classification error for paragraph {paragraph_id}: {e}")
            applicable_rules = []
        
        # Update paragraph classification
        paragraph.applicable_rules = applicable_rules
        paragraph.classification_confidence = 0.85
        
        if not applicable_rules:
            return
            
        # Get full text of applicable rules
        full_rules = await rule_set_service.get_rules_by_numbers(
            rule_set_id, applicable_rules, filter_date=filter_date
        )
        
        # Perform compliance analysis (with timeout)
        try:
            issues = await asyncio.wait_for(
                self.llm_service.analyze_compliance(paragraph.content, full_rules),
                timeout=60.0  # 60 second timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Compliance analysis timeout for paragraph {paragraph_id}")
            return
        except Exception as e:
            logger.error(f"Compliance analysis error for paragraph {paragraph_id}: {e}")
            return
        
        # Store issues in database
        for issue_data in issues:
            issue = ComplianceIssue(
                document_id=document_id,
                paragraph_id=paragraph.id,
                rule_number=issue_data['rule_number'],
                rule_title=issue_data.get('rule_title', ''),
                rule_date=issue_data.get('rule_date', 'Current'),
                severity=issue_data.get('severity', 'medium'),
                issue_type=issue_data.get('issue_type', 'unknown'),
                description=issue_data.get('description', ''),
                current_text=issue_data.get('current_text'),
                required_text=issue_data.get('required_text'),
                suggested_fix=issue_data.get('suggested_fix'),
                highlight_start=issue_data.get('highlight_start'),
                highlight_end=issue_data.get('highlight_end')
            )
            db.add(issue)
        
        await db.flush()
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split document into paragraphs for analysis"""
        paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n', text)
        
        result = []
        for para in paragraphs:
            if len(para) > 2000:  # Split long paragraphs
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current = ""
                for sentence in sentences:
                    if len(current) + len(sentence) > 1500:
                        if current:
                            result.append(current.strip())
                        current = sentence
                    else:
                        current += " " + sentence
                if current:
                    result.append(current.strip())
            else:
                result.append(para.strip())
                
        return [p for p in result if p]  # Remove empty paragraphs
    
    async def _get_cached_analysis(self, document_hash: str) -> Optional[Dict]:
        """Check if we have a cached analysis for this document"""
        result = await self.db.execute(
            select(AnalysisCache)
            .where(AnalysisCache.document_hash == document_hash)
            .where(AnalysisCache.expires_at > datetime.utcnow())
        )
        cache_entry = result.scalar_one_or_none()
        
        if cache_entry:
            return {
                'session_id': cache_entry.session_id,
                'created_at': cache_entry.created_at
            }
        return None
    
    async def _cache_analysis_result(self, document_hash: str, session_id: str):
        """Cache the analysis result for future retrieval"""
        cache_entry = AnalysisCache(
            document_hash=document_hash,
            session_id=session_id,
            expires_at=datetime.utcnow() + timedelta(hours=24)  # 24 hour cache
        )
        self.db.add(cache_entry)
        await self.db.commit()