# backend/app/db/user_preferences.py
from sqlalchemy import Column, String, Integer, JSON, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)  # Clerk user ID or email
    
    # Preferences
    last_selected_rule_set_id = Column(Integer, nullable=True)
    ui_preferences = Column(JSON, default={})  # For storing various UI settings
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())