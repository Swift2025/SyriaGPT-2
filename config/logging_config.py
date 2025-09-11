import logging
import logging.config
import os
from typing import Dict, Any

def setup_logging() -> None:
    """Setup structured logging configuration with verbose logging support"""
    
    # Default to DEBUG for verbose logging, but allow override via environment
    log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
    
    # Enable verbose logging for specific modules if needed
    verbose_modules = os.getenv("VERBOSE_MODULES", "").split(",") if os.getenv("VERBOSE_MODULES") else []
    
    # Enable ultra-verbose logging for all modules if specified
    ultra_verbose = os.getenv("ULTRA_VERBOSE", "false").lower() == "true"
    
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "verbose": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "ultra_verbose": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(threadName)s - %(processName)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "file": "%(filename)s", "line": "%(lineno)d", "function": "%(funcName)s", "thread": "%(threadName)s", "process": "%(processName)s", "message": "%(message)s"}',
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "performance": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - [PERF] - %(funcName)s() - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "ultra_verbose" if ultra_verbose else "verbose" if log_level == "DEBUG" else "default",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "ultra_verbose" if ultra_verbose else "verbose" if log_level == "DEBUG" else "default",
                "filename": "logs/syriagpt.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "debug_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "ultra_verbose" if ultra_verbose else "verbose",
                "filename": "logs/syriagpt_debug.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 3,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "ultra_verbose" if ultra_verbose else "verbose",
                "filename": "logs/syriagpt_errors.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 3,
            },
            "performance_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "performance",
                "filename": "logs/syriagpt_performance.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 2,
            },
            "json_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "json",
                "filename": "logs/syriagpt_json.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 2,
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file", "debug_file", "error_file", "performance_file", "json_file"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console", "file", "debug_file", "error_file", "performance_file", "json_file"],
                "level": log_level,
                "propagate": False,
            },
            "fastapi": {
                "handlers": ["console", "file", "debug_file", "error_file", "performance_file", "json_file"],
                "level": log_level,
                "propagate": False,
            },
            "sqlalchemy": {
                "handlers": ["console", "file", "debug_file", "error_file", "performance_file", "json_file"],
                "level": "DEBUG" if log_level == "DEBUG" else "WARNING",
                "propagate": False,
            },
            # Add verbose logging for specific modules
            "services": {
                "handlers": ["console", "file", "debug_file", "error_file", "performance_file", "json_file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "api": {
                "handlers": ["console", "file", "debug_file", "error_file", "performance_file", "json_file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "config": {
                "handlers": ["console", "file", "debug_file", "error_file", "performance_file", "json_file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "models": {
                "handlers": ["console", "file", "debug_file", "error_file", "performance_file", "json_file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "migrations": {
                "handlers": ["console", "file", "debug_file", "error_file", "performance_file", "json_file"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }
    
    # Add specific verbose logging for modules listed in VERBOSE_MODULES
    for module in verbose_modules:
        if module.strip():
            logging_config["loggers"][module.strip()] = {
                "handlers": ["console", "file", "debug_file", "error_file", "performance_file", "json_file"],
                "level": "DEBUG",
                "propagate": False,
            }
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    logging.config.dictConfig(logging_config)
    
    # Log the logging configuration setup
    root_logger = logging.getLogger()
    root_logger.info(f"[SETUP] Logging system initialized with level: {log_level}")
    if ultra_verbose:
        root_logger.info("[SETUP] Ultra-verbose logging enabled")
    if verbose_modules:
        root_logger.info(f"[SETUP] Verbose logging enabled for modules: {verbose_modules}")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    logger = logging.getLogger(name)
    logger.debug(f"[LOGGER] Logger '{name}' initialized")
    return logger

def set_verbose_logging(module_name: str = None) -> None:
    """Enable verbose logging for a specific module or globally"""
    if module_name:
        logger = logging.getLogger(module_name)
        logger.setLevel(logging.DEBUG)
        # Ensure all handlers are set to DEBUG level
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
        logger.info(f"[SETUP] Verbose logging enabled for module: {module_name}")
    else:
        # Set root logger to DEBUG
        logging.getLogger().setLevel(logging.DEBUG)
        for handler in logging.getLogger().handlers:
            handler.setLevel(logging.DEBUG)
        logging.getLogger().info("[SETUP] Global verbose logging enabled")

def log_function_entry(logger: logging.Logger, func_name: str = None, **kwargs):
    """Decorator helper to log function entry with parameters"""
    if not func_name:
        import inspect
        func_name = inspect.currentframe().f_back.f_code.co_name
    
    # Sanitize sensitive parameters
    sanitized_kwargs = {}
    sensitive_keys = ['password', 'token', 'secret', 'key', 'auth']
    
    for key, value in kwargs.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized_kwargs[key] = '[REDACTED]'
        else:
            # Truncate long values for readability
            if isinstance(value, str) and len(value) > 100:
                sanitized_kwargs[key] = f"{value[:100]}..."
            else:
                sanitized_kwargs[key] = value
    
    logger.debug(f"[ENTER] Entering function: {func_name} with params: {sanitized_kwargs}")

def log_function_exit(logger: logging.Logger, func_name: str = None, result=None, duration=None):
    """Decorator helper to log function exit with result"""
    if not func_name:
        import inspect
        func_name = inspect.currentframe().f_back.f_code.co_name
    
    duration_msg = f" (took {duration:.3f}s)" if duration else ""
    
    if result is not None:
        # Truncate long results for readability
        if isinstance(result, str) and len(result) > 200:
            result_str = f"{result[:200]}..."
        else:
            result_str = str(result)
        logger.debug(f"[EXIT] Exiting function: {func_name} with result: {result_str}{duration_msg}")
    else:
        logger.debug(f"[EXIT] Exiting function: {func_name}{duration_msg}")

def log_performance(logger: logging.Logger, operation: str, duration: float, **context):
    """Log performance metrics"""
    logger.info(f"[PERF] Performance: {operation} took {duration:.3f}s - Context: {context}")

def log_error_with_context(logger: logging.Logger, error: Exception, context: str = "", **kwargs):
    """Log errors with additional context"""
    logger.error(f"[ERROR] Error in {context}: {str(error)} - Context: {kwargs}")
    logger.debug(f"[ERROR] Error details: {type(error).__name__}: {str(error)}")
