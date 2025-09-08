"""
Logging configuration for SyriaGPT application.
Provides structured logging with multiple handlers and formatters.
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Dict, Any
import structlog
from colorama import init as colorama_init

# Initialize colorama for colored console output
colorama_init(autoreset=True)


def setup_logging(config) -> logging.Logger:
    """Setup comprehensive logging configuration.
    
    Args:
        config: Configuration loader instance
        
    Returns:
        Configured logger instance
    """
    logging_config = config.get_logging_config()
    
    # Create logs directory if it doesn't exist
    log_file_path = Path(logging_config["file_path"])
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, logging_config["level"].upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, logging_config["level"].upper()))
    
    # Create colored formatter for console
    console_formatter = ColoredFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=logging_config["file_path"],
        maxBytes=logging_config["max_size"],
        backupCount=logging_config["backup_count"],
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # JSON formatter for file
    file_formatter = JSONFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler for errors and above
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_file_path.parent / "errors.log",
        maxBytes=logging_config["max_size"],
        backupCount=logging_config["backup_count"],
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Access log handler for HTTP requests
    access_handler = logging.handlers.RotatingFileHandler(
        filename=log_file_path.parent / "access.log",
        maxBytes=logging_config["max_size"],
        backupCount=logging_config["backup_count"],
        encoding='utf-8'
    )
    access_handler.setLevel(logging.INFO)
    access_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    access_handler.setFormatter(access_formatter)
    
    # Create access logger
    access_logger = logging.getLogger("access")
    access_logger.addHandler(access_handler)
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False
    
    # Configure specific loggers
    _configure_specific_loggers(logging_config)
    
    # Create main application logger
    app_logger = logging.getLogger("syriagpt")
    app_logger.info("🚀 SyriaGPT logging system initialized")
    
    return app_logger


def _configure_specific_loggers(config: Dict[str, Any]):
    """Configure specific loggers for different modules."""
    
    # Database logger
    db_logger = logging.getLogger("sqlalchemy.engine")
    if config["ultra_verbose"]:
        db_logger.setLevel(logging.INFO)
    else:
        db_logger.setLevel(logging.WARNING)
    
    # AI services logger
    ai_logger = logging.getLogger("services.ai")
    ai_logger.setLevel(logging.DEBUG if "ai" in config["verbose_modules"] else logging.INFO)
    
    # Authentication logger
    auth_logger = logging.getLogger("services.auth")
    auth_logger.setLevel(logging.DEBUG if "auth" in config["verbose_modules"] else logging.INFO)
    
    # Email logger
    email_logger = logging.getLogger("services.email")
    email_logger.setLevel(logging.DEBUG if "email" in config["verbose_modules"] else logging.INFO)
    
    # Qdrant logger
    qdrant_logger = logging.getLogger("qdrant")
    qdrant_logger.setLevel(logging.WARNING)
    
    # Uvicorn logger
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(logging.INFO)
    
    # FastAPI logger
    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.setLevel(logging.INFO)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        """Format log record with colors."""
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        # Add emoji based on level
        emoji_map = {
            'DEBUG': '🔍',
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '💥'
        }
        
        if record.levelname.replace(self.COLORS.get(record.levelname, ''), '').replace(self.COLORS['RESET'], '') in emoji_map:
            emoji = emoji_map[record.levelname.replace(self.COLORS.get(record.levelname, ''), '').replace(self.COLORS['RESET'], '')]
            record.msg = f"{emoji} {record.msg}"
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        import json
        return json.dumps(log_entry, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_function_call(func):
    """Decorator to log function calls."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {e}")
            raise
    return wrapper


def log_async_function_call(func):
    """Decorator to log async function calls."""
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling async {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Async {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Async {func.__name__} failed with error: {e}")
            raise
    return wrapper
