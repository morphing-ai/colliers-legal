# backend/app/services/llm_service.py
import json
import logging
import os
import asyncio
import time
from typing import List, Dict, Optional
import httpx
from openai import AsyncAzureOpenAI

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Show info level logs for API calls

class LLMService:
    """Service for LLM-based classification and analysis using Azure OpenAI GPT-4o"""
    
    def __init__(self):
        # Use Azure OpenAI exclusively with GPT-4o
        self.client = AsyncAzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-03-01-preview"),
            timeout=httpx.Timeout(30.0, connect=10.0),  # 30 sec timeout, 10 sec connect
            max_retries=2
        )
        
        # Use GPT-4o for everything
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        self.provider = "azure_openai"
        
        # Also use Azure OpenAI for preprocessing (same GPT-4o model)
        self.preprocessing_client = self.client
        self.preprocessing_model = self.model
        
        logger.info(f"[LLM] Initialized with Azure OpenAI using {self.model}")
            
    async def classify_paragraph(self, paragraph_text: str, rule_catalog: List[Dict]) -> List[str]:
        """Use LLM to classify which FINRA rules apply to a paragraph"""
        
        logger.info(f"[LLM-CLASSIFY] Starting classification: paragraph={len(paragraph_text)} chars, catalog={len(rule_catalog)} rules")
        logger.info(f"[LLM-CLASSIFY] Using Azure OpenAI {self.model}")
        
        # Format rule catalog for LLM
        catalog_text = "\n".join([
            f"{r['number']} - {r['title']} - {r['summary'][:100] if r.get('summary') else 'No summary'}"
            for r in rule_catalog
        ])
        
        prompt = f"""You are a FINRA compliance expert. Analyze this WSP (Written Supervisory Procedures) paragraph and identify ALL applicable FINRA rules FROM THE PROVIDED LIST ONLY.

WSP Paragraph:
{paragraph_text}

Available FINRA Rules (USE ONLY THESE EXACT RULE NUMBERS):
{catalog_text}

Instructions:
1. Identify rules explicitly mentioned or referenced in the paragraph
2. Identify rules that SHOULD apply based on the topics and procedures discussed
3. Consider implicit requirements (e.g., if discussing customer accounts, include suitability rules)
4. Be comprehensive - include all potentially relevant rules
5. CRITICAL: Only return rule numbers that appear in the "Available FINRA Rules" list above
6. DO NOT make up rule numbers or use any numbers not in the provided list

Return ONLY a JSON array of rule numbers that apply to this paragraph.
The rule numbers must be EXACTLY as they appear in the Available FINRA Rules list above.

If no rules apply, return an empty array: []"""

        try:
            # Azure OpenAI with GPT-4o
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a FINRA compliance expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            # Note: Azure OpenAI GPT-4o supports JSON mode but not through response_format
            
            # Log and call API
            logger.info(f"[LLM-CLASSIFY] Calling Azure OpenAI API ({self.model})...")
            start_time = time.time()
            try:
                response = await self.client.chat.completions.create(**kwargs)
                elapsed = time.time() - start_time
                logger.info(f"[LLM-CLASSIFY] Got response in {elapsed:.2f}s")
                content = response.choices[0].message.content
                logger.debug(f"[LLM-CLASSIFY] Response length: {len(content) if content else 0} chars")
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"[LLM-CLASSIFY] API error after {elapsed:.2f}s: {e}")
                raise
                
            # Parse response
            if not content:
                logger.warning("[LLM-CLASSIFY] Empty response")
                return []
            result = json.loads(content)
            if isinstance(result, dict) and 'rules' in result:
                logger.info(f"[LLM-CLASSIFY] Found {len(result['rules'])} rules")
                return result['rules']
            elif isinstance(result, list):
                logger.info(f"[LLM-CLASSIFY] Found {len(result)} rules")
                return result
            else:
                logger.warning(f"[LLM-CLASSIFY] Unexpected format")
                return []
                
        except asyncio.CancelledError:
            logger.warning("Classification cancelled")
            raise  # Propagate cancellation
        except asyncio.TimeoutError:
            logger.error("LLM classification timed out")
            raise  # Propagate timeout
        except Exception as e:
            logger.error(f"Error in LLM classification: {e}")
            # Check if it's a rate limit error that should be propagated
            if '429' in str(e) or 'rate' in str(e).lower():
                raise  # Propagate rate limit errors
            return []
            
    async def analyze_compliance(self, paragraph_text: str, relevant_rules: List[Dict]) -> List[Dict]:
        """Perform deep compliance analysis on a paragraph"""
        
        if not relevant_rules:
            logger.info("[LLM-ANALYZE] No rules to analyze")
            return []
        
        logger.info(f"[LLM-ANALYZE] Starting analysis with {len(relevant_rules)} rules")
        
        # Format rules for analysis
        rules_text = "\n\n".join([
            f"Rule {r['rule_number']}: {r['rule_title']}\n"
            f"Effective Date: {r['effective_date']}\n"
            f"Requirements: {r['rule_text'][:500]}..."
            for r in relevant_rules
        ])
        
        prompt = f"""Perform a detailed FINRA compliance analysis of this WSP paragraph.

WSP Paragraph:
{paragraph_text}

Applicable FINRA Rules:
{rules_text}

For each rule, determine:
1. Is the rule properly addressed in the WSP paragraph?
2. What specific requirements are missing or inadequate?
3. What text should be added or modified?

Return a JSON array of issues found. Include BOTH compliant findings AND violations.

Format:
[
    {{
        "rule_number": "3010",
        "rule_title": "Supervision",  
        "rule_date": "2023-09-01",
        "severity": "high",  // critical, high, medium, low, success
        "issue_type": "missing",  // compliant, missing, inadequate, outdated, violation
        "description": "Clear explanation of the issue",
        "current_text": "Quote the problematic text if any",
        "required_text": "What the text should say",
        "suggested_fix": "Specific suggestion to fix the issue"
    }}
]

Severity levels:
- success: Fully compliant with the rule
- low: Minor improvement suggested
- medium: Important gap that should be addressed
- high: Significant compliance issue
- critical: Major violation or completely missing required element

Issue types:
- compliant: Meets all requirements
- missing: Required element not addressed
- inadequate: Addressed but insufficient
- outdated: References old version of rule
- violation: Directly violates the rule

Include BOTH compliant findings (severity: success) and issues."""

        try:
            # Azure OpenAI with GPT-4o
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a FINRA compliance expert auditor. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 2000
            }
            
            # Log and call API
            logger.info(f"[LLM-ANALYZE] Calling Azure OpenAI API ({self.model})...")
            start_time = time.time()
            try:
                response = await self.client.chat.completions.create(**kwargs)
                elapsed = time.time() - start_time
                logger.info(f"[LLM-ANALYZE] Got response in {elapsed:.2f}s")
                content = response.choices[0].message.content
                logger.debug(f"[LLM-ANALYZE] Response length: {len(content) if content else 0} chars")
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"[LLM-ANALYZE] API error after {elapsed:.2f}s: {e}")
                raise
                
            # Parse response
            if not content:
                logger.warning("[LLM-ANALYZE] Empty response")
                return []
            
            logger.debug(f"[LLM-ANALYZE] Parsing JSON response")
            result = json.loads(content)
            
            if isinstance(result, dict) and 'issues' in result:
                issues = result['issues']
                logger.info(f"[LLM-ANALYZE] Found {len(issues)} compliance issues")
                for issue in issues[:3]:  # Log first 3 issues
                    logger.debug(f"[LLM-ANALYZE] Issue: {issue.get('rule_number', 'N/A')} - {issue.get('severity', 'N/A')} - {issue.get('issue_type', 'N/A')}")
                return issues
            elif isinstance(result, list):
                logger.info(f"[LLM-ANALYZE] Found {len(result)} compliance issues")
                for issue in result[:3]:  # Log first 3 issues
                    logger.debug(f"[LLM-ANALYZE] Issue: {issue.get('rule_number', 'N/A')} - {issue.get('severity', 'N/A')} - {issue.get('issue_type', 'N/A')}")
                return result
            else:
                logger.warning(f"[LLM-ANALYZE] Unexpected format")
                return []
                
        except asyncio.CancelledError:
            logger.warning("Compliance analysis cancelled")
            raise  # Propagate cancellation
        except asyncio.TimeoutError:
            logger.error("LLM compliance analysis timed out")
            raise  # Propagate timeout
        except Exception as e:
            logger.error(f"Error in compliance analysis: {e}")
            # Check if it's a rate limit error that should be propagated
            if '429' in str(e) or 'rate' in str(e).lower():
                raise  # Propagate rate limit errors
            return []
    
    async def preprocess_rule(self, rule_text: str, preprocessing_prompt: str) -> str:
        """Use GPT-4o to preprocess/transform a rule based on user prompt"""
        
        if not preprocessing_prompt or not rule_text:
            return rule_text
            
        prompt = f"""Based on the following instruction, process this rule text:

Instruction: {preprocessing_prompt}

Rule Text:
{rule_text}

Return only the processed rule text."""
        
        try:
            response = await self.preprocessing_client.chat.completions.create(
                model=self.preprocessing_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that processes and transforms rule text based on instructions. Return only the processed rule text without any additional explanation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            return response.choices[0].message.content or rule_text
        except Exception as e:
            logger.error(f"Error preprocessing rule with GPT-4o: {e}")
            return rule_text
    
    async def preprocess_rule_json(self, rule_data: Dict, preprocessing_prompt: str) -> Dict:
        """Use GPT-4o to preprocess rule and return structured JSON"""
        
        if not preprocessing_prompt:
            return rule_data
            
        prompt = f"""Based on the following instruction, process this rule and return structured JSON:

Instruction: {preprocessing_prompt}

Current Rule Data:
{json.dumps(rule_data, indent=2)}

Return a JSON object with the same structure but transformed according to the instruction."""
        
        try:
            response = await self.preprocessing_client.chat.completions.create(
                model=self.preprocessing_model,
                messages=[
                    {"role": "system", "content": "You are a FINRA compliance expert. Return valid JSON with the requested structure."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            result = json.loads(response.choices[0].message.content)
            return result if isinstance(result, dict) else rule_data
            
        except Exception as e:
            logger.error(f"Error preprocessing rule JSON: {e}")
            return rule_data