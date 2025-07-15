#!/usr/bin/env python
"""Add path and depth columns to departments table."""

import os
import sys
from sqlalchemy import create_engine, text

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def add_columns():
    """Add path and depth columns to departments table."""
    engine = create_engine(str(settings.DATABASE_URL))
    
    with engine.connect() as conn:
        # Add columns if they don't exist
        conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name='departments' AND column_name='path') THEN
                    ALTER TABLE departments ADD COLUMN path VARCHAR(1000) NOT NULL DEFAULT '/';
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name='departments' AND column_name='depth') THEN
                    ALTER TABLE departments ADD COLUMN depth INTEGER NOT NULL DEFAULT 0;
                END IF;
            END $$;
        """))
        conn.commit()
        
    print("Successfully added path and depth columns to departments table")

if __name__ == "__main__":
    add_columns()