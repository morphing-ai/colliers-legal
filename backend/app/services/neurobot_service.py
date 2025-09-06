"""
Neurobot Service for Morphing Digital Paralegal
Dynamic code execution for contract analysis
"""
import asyncio
import json
import time
import traceback
from io import StringIO
from contextlib import redirect_stdout
from typing import Dict, List, Any, Optional, Callable
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.database import get_db
from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class NeurobotService:
    """Service for managing and executing Neurobots."""
    
    def __init__(self):
        self._neurobots_cache: Dict[str, Callable] = {}
        self._last_cache_update = 0
        self._cache_ttl = 300  # 5 minutes
        self.llm_service = LLMService()
        self.embedding_service = EmbeddingService()
        
    async def load_neurobots(self, db: AsyncSession, force_reload: bool = False) -> Dict[str, Callable]:
        """Load all active Neurobots from database into memory."""
        current_time = time.time()
        
        # Check if cache is still valid
        if not force_reload and self._neurobots_cache and (current_time - self._last_cache_update) < self._cache_ttl:
            return self._neurobots_cache
            
        logger.info("Loading Neurobots from database...")
        
        try:
            # Get all active neurobots
            query = text("SELECT * FROM neurobots WHERE is_active = true")
            result = await db.execute(query)
            neurobots = result.fetchall()
            
            # Create a module-like namespace
            module_code = """
# Auto-generated Neurobot module for Morphing Digital Paralegal
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# Available services will be injected at runtime
"""
            
            # Add each neurobot's code
            for bot in neurobots:
                module_code += f"\n\n# Neurobot: {bot['function_name']}\n"
                module_code += f"# Author: {bot['created_by']}\n"
                module_code += f"# Description: {bot['description']}\n"
                module_code += bot['code'] + "\n"
            
            # Create namespace and execute code
            namespace = {
                '__name__': 'neurobots',
                'asyncio': asyncio,
                'json': json,
                'Dict': Dict,
                'List': List,
                'Any': Any,
                'Optional': Optional,
                'datetime': datetime
            }
            
            # Execute the module code
            exec(module_code, namespace)
            
            # Extract functions
            self._neurobots_cache = {}
            for bot in neurobots:
                func_name = bot['function_name']
                if func_name in namespace and callable(namespace[func_name]):
                    self._neurobots_cache[func_name] = namespace[func_name]
                    logger.info(f"Loaded Neurobot: {func_name} by {bot['created_by']}")
                else:
                    logger.error(f"Failed to load Neurobot: {func_name}")
            
            self._last_cache_update = current_time
            logger.info(f"Loaded {len(self._neurobots_cache)} Neurobots")
            
            return self._neurobots_cache
            
        except Exception as e:
            logger.error(f"Error loading Neurobots: {str(e)}")
            logger.error(traceback.format_exc())
            return {}
    
    def _create_service_context(self, contract_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a context with available services for Neurobot execution."""
        services = {
            'llm': self.llm_service,
            'embeddings': self.embedding_service,
            'neurobots': self._neurobots_cache,  # Allow neurobots to call each other
            'get_similar_clauses': self.get_similar_clauses,
            'learn_pattern': self.learn_new_pattern
        }
        
        context = contract_context or {}
        context['services'] = services
        
        return context
    
    async def execute_neurobot(
        self,
        db: AsyncSession,
        function_name: str,
        params: Dict[str, Any] = None,
        contract_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a Neurobot function with given parameters."""
        start_time = time.time()
        
        try:
            # Load neurobots if needed
            await self.load_neurobots(db)
            
            # Check if neurobot exists
            if function_name not in self._neurobots_cache:
                return {
                    'success': False,
                    'error': f"Neurobot '{function_name}' not found"
                }
            
            # Create execution context
            context = self._create_service_context(contract_context)
            
            # Execute the neurobot
            logger.info(f"Executing Neurobot: {function_name}")
            neurobot_func = self._neurobots_cache[function_name]
            
            # Call the neurobot function
            if asyncio.iscoroutinefunction(neurobot_func):
                result = await neurobot_func(params, context)
            else:
                result = neurobot_func(params, context)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Log execution
            await self._log_execution(
                db=db,
                function_name=function_name,
                params=params,
                result=result,
                success=True,
                execution_time_ms=execution_time
            )
            
            # Update usage stats
            await self._update_usage_stats(db, function_name, execution_time)
            
            return {
                'success': True,
                'result': result,
                'execution_time_ms': execution_time
            }
            
        except Exception as e:
            logger.error(f"Error executing Neurobot {function_name}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Log failed execution
            await self._log_execution(
                db=db,
                function_name=function_name,
                params=params,
                result=None,
                success=False,
                error_message=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
            
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    async def create_neurobot(
        self,
        db: AsyncSession,
        function_name: str,
        description: str,
        code: str,
        neurobot_type: str,
        created_by: str,
        example_usage: Optional[str] = None,
        expected_parameters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a new Neurobot and store in database."""
        try:
            # Validate the code by attempting to compile it
            compile(code, f'<neurobot:{function_name}>', 'exec')
            
            # Insert into database
            query = insert('neurobots').values(
                function_name=function_name,
                description=description,
                code=code,
                neurobot_type=neurobot_type,
                created_by=created_by,
                example_usage=example_usage,
                expected_parameters=json.dumps(expected_parameters) if expected_parameters else None,
                is_active=True,
                run_count=0,
                feedback_plus=0,
                feedback_minus=0
            )
            
            await db.execute(query)
            await db.commit()
            
            # Force reload of neurobots
            await self.load_neurobots(db, force_reload=True)
            
            logger.info(f"Created new Neurobot: {function_name} by {created_by}")
            
            return {
                'success': True,
                'message': f"Neurobot '{function_name}' created successfully"
            }
            
        except SyntaxError as e:
            return {
                'success': False,
                'error': f"Syntax error in Neurobot code: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error creating Neurobot: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update_neurobot(
        self,
        db: AsyncSession,
        function_name: str,
        code: str,
        updated_by: str,
        change_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update existing Neurobot code with version tracking."""
        try:
            # Validate the new code
            compile(code, f'<neurobot:{function_name}>', 'exec')
            
            # Get current version
            query = select('*').select_from('neurobots').where(f"function_name = '{function_name}'")
            result = await db.execute(query)
            current = result.fetchone()
            
            if not current:
                return {
                    'success': False,
                    'error': f"Neurobot '{function_name}' not found"
                }
            
            # Save current version to history
            version_query = insert('neurobot_versions').values(
                neurobot_id=current['id'],
                version_number=current.get('run_count', 0) + 1,
                code_snapshot=current['code'],
                changed_by=updated_by,
                change_notes=change_notes
            )
            await db.execute(version_query)
            
            # Update the neurobot
            update_query = update('neurobots').where(
                f"function_name = '{function_name}'"
            ).values(
                code=code,
                updated_at=datetime.utcnow()
            )
            await db.execute(update_query)
            await db.commit()
            
            # Force reload
            await self.load_neurobots(db, force_reload=True)
            
            logger.info(f"Updated Neurobot: {function_name} by {updated_by}")
            
            return {
                'success': True,
                'message': f"Neurobot '{function_name}' updated successfully"
            }
            
        except SyntaxError as e:
            return {
                'success': False,
                'error': f"Syntax error in updated code: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error updating Neurobot: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_similar_clauses(
        self,
        db: AsyncSession,
        clause_text: str,
        threshold: float = 0.8,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find similar clauses using vector similarity search."""
        # Get embedding for the clause
        embedding = await self.embedding_service.get_embedding(clause_text)
        
        # Vector similarity search
        query = f"""
            SELECT 
                clause_text,
                clause_type,
                risk_score,
                paralegal_notes,
                1 - (embedding_vector <=> ARRAY{embedding}::vector) as similarity
            FROM clause_embeddings
            WHERE 1 - (embedding_vector <=> ARRAY{embedding}::vector) > {threshold}
            ORDER BY similarity DESC
            LIMIT {limit}
        """
        
        result = await db.execute(query)
        return [dict(row) for row in result.fetchall()]
    
    async def learn_new_pattern(
        self,
        db: AsyncSession,
        clause_text: str,
        pattern_name: str,
        risk_level: str,
        description: str,
        created_by: str
    ) -> Dict[str, Any]:
        """Learn a new pattern from a clause."""
        try:
            # Generate embedding
            embedding = await self.embedding_service.get_embedding(clause_text)
            
            # Store the pattern
            query = insert('clause_patterns').values(
                pattern_name=pattern_name,
                pattern_description=description,
                centroid_embedding=embedding,
                risk_level=risk_level,
                example_clauses=json.dumps([clause_text]),
                frequency_seen=1,
                created_by=created_by
            )
            
            await db.execute(query)
            
            # Also store in clause_embeddings
            embed_query = insert('clause_embeddings').values(
                clause_text=clause_text,
                clause_type=pattern_name,
                embedding_vector=embedding,
                risk_score=1.0 if risk_level == 'high' else 0.5 if risk_level == 'medium' else 0.2,
                created_by=created_by
            )
            
            await db.execute(embed_query)
            await db.commit()
            
            return {
                'success': True,
                'message': f"Learned new pattern: {pattern_name}"
            }
            
        except Exception as e:
            logger.error(f"Error learning pattern: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _log_execution(
        self,
        db: AsyncSession,
        function_name: str,
        params: Dict,
        result: Any,
        success: bool,
        execution_time_ms: int,
        error_message: Optional[str] = None
    ):
        """Log Neurobot execution for analytics."""
        try:
            # Get neurobot ID
            query = select('id').select_from('neurobots').where(f"function_name = '{function_name}'")
            bot_result = await db.execute(query)
            bot = bot_result.fetchone()
            
            if bot:
                log_query = insert('neurobot_execution_logs').values(
                    neurobot_id=bot['id'],
                    input_params=json.dumps(params) if params else None,
                    output_result=json.dumps(result) if result else None,
                    success=success,
                    error_message=error_message,
                    execution_time_ms=execution_time_ms
                )
                await db.execute(log_query)
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error logging execution: {str(e)}")
    
    async def _update_usage_stats(
        self,
        db: AsyncSession,
        function_name: str,
        execution_time_ms: int
    ):
        """Update usage statistics for a Neurobot."""
        try:
            # Get current stats
            query = select('run_count', 'avg_execution_time').select_from('neurobots').where(
                f"function_name = '{function_name}'"
            )
            result = await db.execute(query)
            current = result.fetchone()
            
            if current:
                new_count = current['run_count'] + 1
                new_avg = ((current['avg_execution_time'] * current['run_count']) + execution_time_ms) / new_count
                
                update_query = update('neurobots').where(
                    f"function_name = '{function_name}'"
                ).values(
                    run_count=new_count,
                    avg_execution_time=new_avg,
                    last_used_at=datetime.utcnow()
                )
                await db.execute(update_query)
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error updating usage stats: {str(e)}")


# Global instance
neurobot_service = NeurobotService()