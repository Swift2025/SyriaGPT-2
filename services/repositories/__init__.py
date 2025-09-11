# Repository layer for data access
import time
from .user_repository import UserRepository
from config.logging_config import get_logger, log_function_entry, log_function_exit, log_performance, log_error_with_context

logger = get_logger(__name__)

# Create singleton instances
user_repository = UserRepository()


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
    "user_repository",
    "get_user_repository"
]
