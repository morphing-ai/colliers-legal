# backend/app/services/compliance_service.py
import hashlib
import logging
import re
import uuid
from typing import List, Dict, Optional
from datetime import datetime, timedelta, date
import asyncio
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.models import DocumentAnalysis, DocumentParagraph, ComplianceIssue, AnalysisCache, RuleSet
from app.services.rule_set_service import RuleSetService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class ComplianceService:
    """Service for analyzing documents against rules in a rule set"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.rule_set_service = RuleSetService(db)
        self.llm_service = LLMService()
        
    async def analyze_document(self, document_text: str, rule_set_id: int, user_id: str, force_new: bool = False, effective_date: Optional[date] = None) -> str:
        """Main entry point for document analysis - returns immediately"""
        logger.info(f"[ANALYZE-DOC] Starting document analysis: rule_set_id={rule_set_id}, user_id={user_id}, doc_length={len(document_text)}, force_new={force_new}, effective_date={effective_date}")
        
        # Create analysis session
        session_id = str(uuid.uuid4())
        logger.info(f"[ANALYZE-DOC] Created session_id: {session_id}")
        # Include rule_set_id and effective_date in hash so different dates get different analyses
        date_str = effective_date.isoformat() if effective_date else "current"
        cache_key = f"{document_text}:{rule_set_id}:{date_str}"
        document_hash = hashlib.md5(cache_key.encode()).hexdigest()
        
        # Check cache settings
        from app.api.admin import cache_settings
        
        # Check cache first (skip if force_new or cache disabled)
        if not force_new and cache_settings.enabled:
            cached_result = await self._get_cached_analysis(document_hash)
            if cached_result:
                logger.info(f"Returning cached analysis session: {cached_result['session_id']}")
                return cached_result['session_id']
        elif force_new:
            logger.info("Force new analysis requested, skipping cache")
        elif not cache_settings.enabled:
            logger.info("Cache is disabled, performing new analysis")
            
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
        
        # Start background processing
        asyncio.create_task(self._process_document_async(
            analysis.id, session_id, rule_set_id, document_hash, paragraphs, effective_date
        ))
        
        # Return immediately with session ID
        return session_id
    
    async def _process_document_async(self, document_id: int, session_id: str, rule_set_id: int, document_hash: str, paragraphs: List[str], effective_date: Optional[date] = None):
        """Process document in background with batch processing"""
        logger.info(f"[PROCESS-START] Starting async processing for session {session_id}, document_id={document_id}, rule_set_id={rule_set_id}")
        logger.info(f"[PROCESS-START] Total paragraphs to process: {len(paragraphs)}")
        
        try:
            # Create fresh db session for background task
            from app.db.database import async_session_factory
            async with async_session_factory() as db:
                # Store paragraphs first
                paragraph_ids = []
                skipped_count = 0
                for idx, para_text in enumerate(paragraphs):
                    if len(para_text.strip()) < 50:
                        skipped_count += 1
                        logger.debug(f"[PROCESS] Skipping short paragraph {idx} (length={len(para_text.strip())})")
                        continue
                        
                    paragraph = DocumentParagraph(
                        document_id=document_id,
                        paragraph_index=idx,
                        content=para_text
                    )
                    db.add(paragraph)
                    await db.flush()
                    paragraph_ids.append(paragraph.id)
                    logger.debug(f"[PROCESS] Added paragraph {idx} with id {paragraph.id}")
                
                await db.commit()
                logger.info(f"[PROCESS] Stored {len(paragraph_ids)} paragraphs, skipped {skipped_count} short ones")
                
                # Now we can use parallel processing for ALL document sizes!
                # Each task has its own DB session, no more conflicts
                batch_size = 20  # Increased back to 20 for maximum parallelization
                total_paras = len(paragraph_ids)
                logger.info(f"[PROCESS-BATCH] Starting batch processing: {total_paras} paragraphs with batch size {batch_size}")
                
                if total_paras == 0:
                    logger.warning(f"[PROCESS-BATCH] No paragraphs to process! Marking as complete.")
                    await db.execute(
                        update(DocumentAnalysis)
                        .where(DocumentAnalysis.id == document_id)
                        .values(
                            analysis_status='completed',
                            completed_at=datetime.utcnow()
                        )
                    )
                    await db.commit()
                    return
                
                processed = 0
                failed_paragraphs = []
                
                for i in range(0, len(paragraph_ids), batch_size):
                    # Check if analysis was stopped
                    check_result = await db.execute(
                        select(DocumentAnalysis.analysis_status)
                        .where(DocumentAnalysis.id == document_id)
                    )
                    current_status = check_result.scalar_one()
                    if current_status == 'stopped':
                        logger.info(f"Analysis {session_id} was stopped by user")
                        return
                    
                    batch = paragraph_ids[i:i+batch_size]
                    
                    # Process batch with timeout protection
                    tasks = []
                    for para_id in batch:
                        # Note: no 'db' passed - each task creates its own session
                        tasks.append(self._analyze_paragraph_with_retry(document_id, rule_set_id, para_id, effective_date))
                    
                    # Wait for batch to complete with timeout
                    try:
                        results = await asyncio.wait_for(
                            asyncio.gather(*tasks, return_exceptions=True),
                            timeout=90.0  # 90 second timeout per batch
                        )
                        # Track failures
                        for idx, result in enumerate(results):
                            if isinstance(result, Exception):
                                failed_paragraphs.append(batch[idx])
                                logger.error(f"Failed to process paragraph {batch[idx]}: {result}")
                    except asyncio.TimeoutError:
                        logger.error(f"Batch timeout at paragraphs {batch}")
                        failed_paragraphs.extend(batch)
                    
                    # Update progress
                    processed += len(batch)
                    await db.execute(
                        update(DocumentAnalysis)
                        .where(DocumentAnalysis.id == document_id)
                        .values(paragraphs_processed=processed)
                    )
                    await db.commit()
                    
                    # No delay between batches - full speed ahead!
                    # if i < len(paragraph_ids) - batch_size:
                    #     await asyncio.sleep(3.0)  # Removed delay for maximum speed
                    
                    # Progress logging every 10 paragraphs
                    if processed % 10 == 0 or processed == len(paragraph_ids):
                        logger.info(f"Processed {processed}/{len(paragraph_ids)} paragraphs for session {session_id}")
                
                # Mark as complete
                await db.execute(
                    update(DocumentAnalysis)
                    .where(DocumentAnalysis.id == document_id)
                    .values(
                        analysis_status='completed',
                        completed_at=datetime.utcnow()
                    )
                )
                
                # Cache the result if caching is enabled
                from app.api.admin import cache_settings
                if cache_settings.enabled:
                    cache = AnalysisCache(
                        cache_key=f"doc_analysis:{document_hash}",
                        cached_data={'session_id': session_id},
                        expires_at=datetime.utcnow() + timedelta(hours=cache_settings.ttl_hours)
                    )
                    db.add(cache)
                    await db.commit()
                    logger.info(f"Cached analysis for {cache_settings.ttl_hours} hours")
                
                if failed_paragraphs:
                    logger.warning(f"Analysis complete with {len(failed_paragraphs)} failed paragraphs for session {session_id}")
                else:
                    logger.info(f"Analysis complete for session {session_id}")
                
        except Exception as e:
            logger.error(f"Error in background processing: {e}")
            # Mark as failed
            async with async_session_factory() as db:
                await db.execute(
                    update(DocumentAnalysis)
                    .where(DocumentAnalysis.id == document_id)
                    .values(analysis_status='failed')
                )
                await db.commit()
        
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split document into paragraphs for analysis"""
        logger.info(f"[SPLIT] Starting to split document of length {len(text)}")
        
        # Split by double newlines or common section markers
        paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n', text)
        logger.info(f"[SPLIT] Initial split resulted in {len(paragraphs)} paragraphs")
        
        # Further split very long paragraphs
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
        
        final_result = [p for p in result if p]  # Remove empty paragraphs
        logger.info(f"[SPLIT] Final result: {len(final_result)} non-empty paragraphs")
        
        # Log paragraph lengths
        valid_count = len([p for p in final_result if len(p.strip()) >= 50])
        logger.info(f"[SPLIT] Paragraphs with length >= 50 chars: {valid_count}")
        
        return final_result
        
    async def _analyze_paragraph_with_retry(self, document_id: int, rule_set_id: int, paragraph_id: int, effective_date: Optional[date] = None, max_retries: int = 2):
        """Analyze paragraph with retry logic - creates its own DB session"""
        from app.db.database import async_session_factory
        
        for attempt in range(max_retries):
            try:
                # Each task gets its OWN database session!
                async with async_session_factory() as db:
                    result = await db.execute(
                        select(DocumentParagraph).where(DocumentParagraph.id == paragraph_id)
                    )
                    paragraph = result.scalar_one()
                    
                    await self._analyze_paragraph(db, document_id, rule_set_id, paragraph, effective_date)
                    await db.commit()
                    return
            except Exception as e:
                error_msg = str(e).lower()
                # Check if it's a timeout or rate limit error that should be retried
                if 'timeout' in error_msg or 'rate' in error_msg or '429' in error_msg:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to analyze paragraph {paragraph_id} after {max_retries} attempts: {e}")
                        raise  # This will mark the paragraph as failed
                    else:
                        wait_time = 3.0 * (attempt + 1)  # 3, 6 seconds
                        logger.warning(f"Retrying paragraph {paragraph_id} due to timeout/rate limit (attempt {attempt+2}/{max_retries}), waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                else:
                    # Non-retryable error
                    logger.error(f"Non-retryable error for paragraph {paragraph_id}: {e}")
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def _analyze_paragraph(self, db: AsyncSession, document_id: int, rule_set_id: int, paragraph: DocumentParagraph, effective_date: Optional[date] = None):
        """Analyze a single paragraph for compliance"""
        logger.info(f"[ANALYZE-PARA] Starting analysis for paragraph {paragraph.id}, rule_set_id={rule_set_id}")
        
        # Step 1: Get rule catalog for classification
        rule_set_service = RuleSetService(db)
        # Convert date to datetime if provided
        filter_date = datetime.combine(effective_date, datetime.min.time()) if effective_date else None
        logger.info(f"[ANALYZE-PARA] Getting rule catalog for rule_set_id={rule_set_id}, filter_date={filter_date}")
        rule_catalog = await rule_set_service.get_rule_catalog(rule_set_id, filter_date=filter_date)
        logger.info(f"[ANALYZE-PARA] Got catalog with {len(rule_catalog)} rules")
        
        # Step 2: Classify which rules apply to this paragraph (with retry on timeout)
        max_retries = 2
        applicable_rules = None
        
        for attempt in range(max_retries):
            try:
                applicable_rules = await asyncio.wait_for(
                    self.llm_service.classify_paragraph(paragraph.content, rule_catalog),
                    timeout=45.0  # 45 second timeout per attempt
                )
                break  # Success, exit retry loop
            except asyncio.TimeoutError:
                logger.warning(f"Classification timeout for paragraph {paragraph.id}, attempt {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    # Final attempt failed, raise exception to fail this paragraph
                    raise Exception(f"Classification failed after {max_retries} attempts due to timeout")
                else:
                    # Wait before retry with exponential backoff
                    await asyncio.sleep(2.0 * (attempt + 1))
            except Exception as e:
                logger.error(f"Classification failed for paragraph {paragraph.id}: {e}")
                if attempt == max_retries - 1:
                    raise  # Re-raise on final attempt
                else:
                    await asyncio.sleep(2.0 * (attempt + 1))
        
        paragraph.applicable_rules = applicable_rules
        paragraph.classification_confidence = 0.85  # Placeholder
        
        if not applicable_rules:
            return
            
        # Step 3: Get full text of applicable rules
        full_rules = await rule_set_service.get_rules_by_numbers(rule_set_id, applicable_rules, filter_date=filter_date)
        
        # Step 4: Perform deep compliance analysis (with retry on timeout)
        max_retries = 2
        issues = None
        
        for attempt in range(max_retries):
            try:
                issues = await asyncio.wait_for(
                    self.llm_service.analyze_compliance(paragraph.content, full_rules),
                    timeout=60.0  # 60 second timeout per attempt
                )
                break  # Success, exit retry loop
            except asyncio.TimeoutError:
                logger.warning(f"Compliance analysis timeout for paragraph {paragraph.id}, attempt {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    # Final attempt failed, raise exception to fail this paragraph
                    raise Exception(f"Compliance analysis failed after {max_retries} attempts due to timeout")
                else:
                    # Wait before retry with exponential backoff
                    await asyncio.sleep(3.0 * (attempt + 1))
            except Exception as e:
                logger.error(f"Compliance analysis failed for paragraph {paragraph.id}: {e}")
                if attempt == max_retries - 1:
                    raise  # Re-raise on final attempt
                else:
                    await asyncio.sleep(3.0 * (attempt + 1))
        
        # Step 5: Store issues in database
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
        
        await db.commit()
    
    async def _get_cached_analysis(self, document_hash: str) -> Optional[Dict]:
        """Check if we have a cached analysis for this document"""
        result = await self.db.execute(
            select(AnalysisCache).where(
                AnalysisCache.cache_key == f"doc_analysis:{document_hash}",
                AnalysisCache.expires_at > datetime.utcnow()
            )
        )
        cache = result.scalar_one_or_none()
        return cache.cached_data if cache else None
        
    async def _cache_analysis(self, document_hash: str, session_id: str):
        """Cache analysis result"""
        cache = AnalysisCache(
            cache_key=f"doc_analysis:{document_hash}",
            cached_data={'session_id': session_id},
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        self.db.add(cache)
        
    async def get_analysis_results(self, session_id: str) -> Optional[Dict]:
        """Get analysis results by session ID - includes partial results"""
        result = await self.db.execute(
            select(DocumentAnalysis).where(DocumentAnalysis.session_id == session_id)
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            return None
            
        # Get all paragraphs that have been processed so far
        paragraphs_result = await self.db.execute(
            select(DocumentParagraph)
            .where(DocumentParagraph.document_id == analysis.id)
            .order_by(DocumentParagraph.paragraph_index)
        )
        paragraphs_list = list(paragraphs_result.scalars())
        
        # Get all issues and group by paragraph_id for O(n) lookup
        issues_result = await self.db.execute(
            select(ComplianceIssue)
            .where(ComplianceIssue.document_id == analysis.id)
        )
        
        # Create a dictionary to group issues by paragraph_id
        issues_by_paragraph = {}
        for issue in issues_result.scalars():
            if issue.paragraph_id not in issues_by_paragraph:
                issues_by_paragraph[issue.paragraph_id] = []
            issues_by_paragraph[issue.paragraph_id].append({
                'rule_number': issue.rule_number,
                'rule_title': issue.rule_title,
                'rule_date': issue.rule_date,
                'severity': issue.severity,
                'issue_type': issue.issue_type,
                'description': issue.description,
                'current_text': issue.current_text,
                'required_text': issue.required_text,
                'suggested_fix': issue.suggested_fix,
                'highlight_start': issue.highlight_start,
                'highlight_end': issue.highlight_end
            })
        
        # Build paragraphs list with their issues
        paragraphs = []
        for para in paragraphs_list:
            # Only include paragraphs that have been analyzed (have applicable_rules set)
            if para.applicable_rules is not None:
                paragraphs.append({
                    'index': para.paragraph_index,
                    'content': para.content,
                    'applicable_rules': para.applicable_rules or [],
                    'issues': issues_by_paragraph.get(para.id, [])
                })
            
        return {
            'session_id': analysis.session_id,
            'status': analysis.analysis_status,
            'created_at': analysis.created_at.isoformat(),
            'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None,
            'total_paragraphs': analysis.total_paragraphs,
            'paragraphs_processed': analysis.paragraphs_processed,
            'progress_percentage': round((analysis.paragraphs_processed / analysis.total_paragraphs * 100) if analysis.total_paragraphs > 0 else 0, 1),
            'paragraphs': paragraphs,
            'title': analysis.title,
            'rule_set_id': analysis.rule_set_id
        }
        
    async def get_user_analysis_history(self, user_id: str, limit: int = 20, offset: int = 0) -> Dict:
        """Get list of analyses for a specific user"""
        from sqlalchemy import desc, func
        
        # Count total analyses for the user
        count_query = select(func.count(DocumentAnalysis.id)).where(
            DocumentAnalysis.analyzed_by == user_id
        )
        total_count = await self.db.scalar(count_query)
        
        # Get analyses with rule set info
        query = (
            select(DocumentAnalysis, RuleSet.name)
            .join(RuleSet, DocumentAnalysis.rule_set_id == RuleSet.id)
            .where(DocumentAnalysis.analyzed_by == user_id)
            .order_by(desc(DocumentAnalysis.last_accessed_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(query)
        analyses = []
        
        for analysis, rule_set_name in result:
            # Count total issues for this analysis
            issues_count_query = select(func.count(ComplianceIssue.id)).where(
                ComplianceIssue.document_id == analysis.id
            )
            issues_count = await self.db.scalar(issues_count_query)
            
            # Generate title if none exists
            title = analysis.title
            if not title:
                # Use first 50 chars of document as title
                doc_preview = analysis.document_text[:50].strip()
                if len(analysis.document_text) > 50:
                    doc_preview += "..."
                title = doc_preview
            
            analyses.append({
                'session_id': analysis.session_id,
                'title': title,
                'rule_set_name': rule_set_name,
                'status': analysis.analysis_status,
                'total_paragraphs': analysis.total_paragraphs,
                'issues_count': issues_count,
                'created_at': analysis.created_at.isoformat(),
                'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None,
                'last_accessed_at': analysis.last_accessed_at.isoformat()
            })
        
        return {
            'analyses': analyses,
            'total': total_count,
            'limit': limit,
            'offset': offset
        }
        
    async def delete_analysis(self, session_id: str, user_id: str) -> bool:
        """Delete an analysis if user owns it"""
        result = await self.db.execute(
            select(DocumentAnalysis).where(
                DocumentAnalysis.session_id == session_id,
                DocumentAnalysis.analyzed_by == user_id
            )
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            return False
            
        await self.db.delete(analysis)
        await self.db.commit()
        return True
        
    async def update_analysis_title(self, session_id: str, user_id: str, title: str) -> bool:
        """Update analysis title if user owns it"""
        result = await self.db.execute(
            update(DocumentAnalysis)
            .where(
                DocumentAnalysis.session_id == session_id,
                DocumentAnalysis.analyzed_by == user_id
            )
            .values(title=title, last_accessed_at=datetime.utcnow())
        )
        
        await self.db.commit()
        return result.rowcount > 0
    
    async def stop_analysis(self, session_id: str, user_id: str) -> bool:
        """Stop an ongoing analysis"""
        result = await self.db.execute(
            select(DocumentAnalysis).where(
                DocumentAnalysis.session_id == session_id,
                DocumentAnalysis.analyzed_by == user_id,
                DocumentAnalysis.analysis_status == 'processing'
            )
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            return False
        
        # Update status to 'stopped'
        await self.db.execute(
            update(DocumentAnalysis)
            .where(DocumentAnalysis.id == analysis.id)
            .values(
                analysis_status='stopped',
                completed_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        
        # Note: The background task will check for this status change and stop processing
        return True