# backend/app/db/models.py
from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, Text, ForeignKey, JSON, Index, Float, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TSVECTOR
from datetime import datetime

from app.db.database import Base

class RuleSet(Base):
    """Collection of rules that can be used for compliance analysis"""
    __tablename__ = "rule_sets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_by = Column(String)  # Clerk user ID
    is_active = Column(Boolean, default=True, index=True)
    preprocessing_prompt = Column(Text, nullable=True)  # Optional GPT-4o prompt for rule preprocessing
    rule_set_metadata = Column(JSON, nullable=True)  # Additional metadata
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    rules = relationship("Rule", back_populates="rule_set", cascade="all, delete-orphan")
    analyses = relationship("DocumentAnalysis", back_populates="rule_set", cascade="all, delete-orphan")

class Rule(Base):
    """Individual rules within a rule set"""
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_set_id = Column(Integer, ForeignKey("rule_sets.id"), index=True)
    rule_number = Column(String, index=True)
    rule_title = Column(String)
    effective_start_date = Column(Date, nullable=True, index=True)
    effective_end_date = Column(Date, nullable=True, index=True)
    rulebook_hierarchy = Column(String, nullable=True)
    rule_text = Column(Text)  # Plain text version of the rule
    original_rule_text = Column(Text, nullable=True)  # Before preprocessing
    
    # Optimized fields for search and classification
    summary = Column(Text, nullable=True)  # 2-3 sentence summary for LLM classification
    category = Column(String, index=True, nullable=True)  # supervision, trading, aml, etc.
    keywords = Column(JSON, nullable=True)  # List of keywords
    is_current = Column(Boolean, default=True, index=True)
    rule_metadata = Column(JSON, nullable=True)  # Additional rule metadata
    
    # Full-text search
    search_vector = Column(TSVECTOR, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    rule_set = relationship("RuleSet", back_populates="rules")
    
    __table_args__ = (
        UniqueConstraint('rule_set_id', 'rule_number', name='uq_rule_set_rule_number'),
        Index('idx_rule_search', 'search_vector', postgresql_using='gin'),
    )

class DocumentAnalysis(Base):
    """Analysis session for a pasted document"""
    __tablename__ = "document_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)  # For tracking analysis sessions
    title = Column(String, nullable=True)  # User-friendly title for the analysis
    rule_set_id = Column(Integer, ForeignKey("rule_sets.id"), index=True)  # Which rule set was used
    document_text = Column(Text)  # The pasted document
    document_hash = Column(String, index=True)  # For deduplication
    
    # Analysis metadata
    total_paragraphs = Column(Integer, default=0)
    paragraphs_processed = Column(Integer, default=0)  # For progress tracking
    analyzed_by = Column(String, index=True)  # Clerk user ID (indexed for history queries)
    analysis_status = Column(String, default="pending")  # pending, processing, completed, failed
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    rule_set = relationship("RuleSet", back_populates="analyses")
    paragraphs = relationship("DocumentParagraph", back_populates="document", cascade="all, delete-orphan")
    issues = relationship("ComplianceIssue", back_populates="document", cascade="all, delete-orphan")

class DocumentParagraph(Base):
    """Individual paragraphs from the document"""
    __tablename__ = "document_paragraphs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("document_analyses.id"))
    paragraph_index = Column(Integer)
    content = Column(Text)
    
    # Classification results
    applicable_rules = Column(JSON)  # List of rule numbers identified by LLM
    classification_confidence = Column(Float)
    
    # Relationships
    document = relationship("DocumentAnalysis", back_populates="paragraphs")
    issues = relationship("ComplianceIssue", back_populates="paragraph")

class ComplianceIssue(Base):
    """Compliance issues found in the document"""
    __tablename__ = "compliance_issues"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("document_analyses.id"))
    paragraph_id = Column(Integer, ForeignKey("document_paragraphs.id"), nullable=True)
    
    rule_number = Column(String, index=True)
    rule_title = Column(String)
    rule_date = Column(String)  # Effective date of the rule
    severity = Column(String, index=True)  # critical, high, medium, low, success
    issue_type = Column(String)  # compliant, missing, inadequate, outdated, violation
    
    description = Column(Text)
    current_text = Column(Text, nullable=True)  # What the document says
    required_text = Column(Text, nullable=True)  # What it should say
    suggested_fix = Column(Text, nullable=True)
    
    # For display
    highlight_start = Column(Integer, nullable=True)  # Character position in paragraph
    highlight_end = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("DocumentAnalysis", back_populates="issues")
    paragraph = relationship("DocumentParagraph", back_populates="issues")

class AnalysisCache(Base):
    """Cache for analysis results"""
    __tablename__ = "analysis_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String, unique=True, index=True)
    cached_data = Column(JSON)
    expires_at = Column(DateTime, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserPreferences(Base):
    """User preferences and settings"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)  # Clerk user ID or email
    
    # Preferences
    last_selected_rule_set_id = Column(Integer, nullable=True)
    ui_preferences = Column(JSON, default={})  # For storing various UI settings
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())