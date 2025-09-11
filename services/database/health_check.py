# Database health check utilities
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from config.logging_config import get_logger

logger = get_logger(__name__)

def check_database_health(db: Session) -> Dict[str, Any]:
    """Check database health and verify required tables exist"""
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        
        # Get inspector to check tables
        inspector = inspect(db.bind)
        existing_tables = inspector.get_table_names()
        
        # Required tables for the application
        required_tables = [
            'users',
            'chats', 
            'chat_messages',
            'chat_feedbacks',
            'chat_settings',
            'questions',
            'answers',
            'qa_pairs',
            'sessions'
        ]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        health_status = {
            "status": "healthy" if not missing_tables else "degraded",
            "connection": "connected",
            "existing_tables": existing_tables,
            "required_tables": required_tables,
            "missing_tables": missing_tables,
            "table_count": len(existing_tables),
            "required_count": len(required_tables),
            "missing_count": len(missing_tables)
        }
        
        if missing_tables:
            logger.warning(f"⚠️ Missing required tables: {missing_tables}")
            health_status["message"] = f"Missing {len(missing_tables)} required tables"
        else:
            logger.info("✅ All required database tables exist")
            health_status["message"] = "Database is healthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "connection": "failed",
            "error": str(e),
            "message": "Database health check failed"
        }

def verify_table_structure(db: Session, table_name: str) -> Dict[str, Any]:
    """Verify a specific table's structure"""
    try:
        inspector = inspect(db.bind)
        
        if not inspector.has_table(table_name):
            return {
                "exists": False,
                "error": f"Table '{table_name}' does not exist"
            }
        
        # Get table columns
        columns = inspector.get_columns(table_name)
        column_info = [
            {
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col["nullable"],
                "primary_key": col.get("primary_key", False)
            }
            for col in columns
        ]
        
        # Get table constraints
        constraints = inspector.get_unique_constraints(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        
        return {
            "exists": True,
            "columns": column_info,
            "constraints": constraints,
            "foreign_keys": foreign_keys,
            "column_count": len(columns)
        }
        
    except Exception as e:
        logger.error(f"❌ Error verifying table '{table_name}': {e}")
        return {
            "exists": False,
            "error": str(e)
        }

def get_database_info(db: Session) -> Dict[str, Any]:
    """Get comprehensive database information"""
    try:
        # Get database version
        version_result = db.execute(text("SELECT version()"))
        version = version_result.scalar()
        
        # Get database size
        size_result = db.execute(text("""
            SELECT pg_size_pretty(pg_database_size(current_database())) as size
        """))
        size = size_result.scalar()
        
        # Get table sizes
        table_sizes_result = db.execute(text("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """))
        table_sizes = [dict(row) for row in table_sizes_result]
        
        return {
            "version": version,
            "database_size": size,
            "table_sizes": table_sizes,
            "total_tables": len(table_sizes)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting database info: {e}")
        return {
            "error": str(e)
        }
