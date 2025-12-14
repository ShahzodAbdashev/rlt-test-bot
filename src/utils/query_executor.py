from typing import Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.engine.result import Row

from src.utils.llm import generate_sql_query, validate_sql_query
import logging

logger = logging.getLogger(__name__)

def execute_natural_language_query(db: Session, user_query: str) -> Any:
    try:
        sql_query = generate_sql_query(user_query)
        logger.info(f"Generated SQL query: \n{sql_query}")

        if not validate_sql_query(sql_query):
            raise ValueError("Generated query is not safe or incorrect")
        
        result = db.execute(text(sql_query))
        row = result.fetchone()
        
        if row is None:
            return 0
        
        value = row[0] if isinstance(row, (Row)) else row
        
        if isinstance(value, (int, float)):
            return int(value) if isinstance(value, float) and value.is_integer() else value
        
        try:
            return int(value)
        except (ValueError, TypeError):
            try:
                return float(value)
            except (ValueError, TypeError):
                return value
        
    except Exception as e:
        raise ValueError(f"Error executing query: {str(e)}")

