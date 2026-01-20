"""Logging utilities for WoW Addon Profile Manager."""

import logging
import sys
from pathlib import Path
from typing import Optional

from colorama import Fore, Style, init


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support."""
    
    # Initialize colorama
    init(autoreset=True)
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        if hasattr(record, 'no_color') and record.no_color:
            return super().format(record)
        
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        
        return super().format(record)


class Logger:
    """Enhanced logger with console and file output."""
    
    def __init__(self, name: str = "addons_profile_manager") -> None:
        """Initialize logger."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Setup console and file handlers."""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(console_handler)
    
    def add_file_handler(self, file_path: Path, level: int = logging.DEBUG) -> None:
        """Add file handler."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(level)
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(file_handler)
    
    def set_level(self, level: str) -> None:
        """Set logging level."""
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Update console handler level
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(log_level)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback."""
        self.logger.exception(message, **kwargs)
    
    def success(self, message: str, **kwargs) -> None:
        """Log success message (info level with special handling)."""
        # Add success marker for potential custom handling
        kwargs.setdefault('extra', {})['success'] = True
        self.info(f"✓ {message}", **kwargs)
    
    def progress(self, message: str, current: int, total: int, **kwargs) -> None:
        """Log progress message."""
        percentage = (current / total) * 100 if total > 0 else 0
        progress_msg = f"{message} [{current}/{total}] ({percentage:.1f}%)"
        self.info(progress_msg, **kwargs)


# Global logger instance
_global_logger: Optional[Logger] = None


def get_logger(name: Optional[str] = None) -> Logger:
    """Get global logger instance."""
    global _global_logger
    
    if _global_logger is None:
        logger_name = name or "addons_profile_manager"
        _global_logger = Logger(logger_name)
    
    return _global_logger


def setup_logging(
    level: str = "INFO",
    file_path: Optional[Path] = None,
    console_output: bool = True,
    colored_output: bool = True
) -> Logger:
    """Setup logging configuration."""
    logger = get_logger()
    logger.set_level(level)
    
    if file_path:
        logger.add_file_handler(file_path)
    
    if not console_output:
        # Remove console handler
        for handler in logger.logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                logger.logger.removeHandler(handler)
    
    return logger