# Repository layer for data access
import time
from .user_repository import UserRepository
from .question_repository import QuestionRepository
from .answer_repository import AnswerRepository
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context

logger = get_logger(__name__)

# Create singleton instances
user_repository = UserRepository()

# Lazy initialization functions for repositories that need database sessions
def get_question_repository():
    log_function_entry(logger, "get_question_repository")
    start_time = time.time()
    try:
        from services.database.database import SessionLocal
        db = SessionLocal()
        duration = time.time() - start_time
        log_performance(logger, "get_question_repository", duration)
        log_function_exit(logger, "get_question_repository", duration=duration)

        return QuestionRepository(db)
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_question_repository", duration=duration)
        logger.error(f"❌ Error in get_question_repository: {e}")
        log_function_exit(logger, "get_question_repository", duration=duration)
        raise

def get_answer_repository():
    log_function_entry(logger, "get_answer_repository")
    start_time = time.time()
    try:
        from services.database.database import SessionLocal
        db = SessionLocal()
        duration = time.time() - start_time
        log_performance(logger, "get_answer_repository", duration)
        log_function_exit(logger, "get_answer_repository", duration=duration)
        return AnswerRepository(db)
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_answer_repository", duration=duration)
        logger.error(f"❌ Error in get_answer_repository: {e}")
        log_function_exit(logger, "get_answer_repository", duration=duration)
        raise

# For compatibility with existing code
def get_user_repository():
    log_function_entry(logger, "get_user_repository")
    start_time = time.time()
    try:
        duration = time.time() - start_time
        log_performance(logger, "get_user_repository", duration)
        log_function_exit(logger, "get_user_repository", duration=duration)
        return user_repository
    except Exception as e:
        duration = time.time() - start_time
        log_error_with_context(logger, e, "get_user_repository", duration=duration)
        logger.error(f"❌ Error in get_user_repository: {e}")
        log_function_exit(logger, "get_user_repository", duration=duration)
        raise

__all__ = [
    "UserRepository",
    "QuestionRepository", 
    "AnswerRepository",
    "user_repository",
    "get_user_repository",
    "get_question_repository",
    "get_answer_repository"
]
