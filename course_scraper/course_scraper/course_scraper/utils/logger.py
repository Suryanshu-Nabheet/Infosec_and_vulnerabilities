#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging Configuration Module for Course Platform Scraper

This module configures logging for the entire application, setting up
file and console handlers, and providing utility functions for getting loggers.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

# Import settings from config
from config import settings

# Constants for log levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}


def configure_logging(
    log_file: Optional[str] = None,
    log_level: Optional[str] = None,
    log_format: Optional[str] = None
) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_file: Path to the log file (defaults to settings.LOG_FILE)
        log_level: Logging level (defaults to settings.LOG_LEVEL)
        log_format: Log format string (defaults to settings.LOG_FORMAT)
    """
    # Use defaults from settings if not provided
    log_file = log_file or settings.LOG_FILE
    log_level = log_level or settings.LOG_LEVEL
    log_format = log_format or settings.LOG_FORMAT
    
    # Convert log level string to logging constant
    level = LOG_LEVELS.get(log_level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    formatter = logging.Formatter(log_format)
    
    # Create and configure file handler
    try:
        # Ensure the logs directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Use a rotating file handler to avoid huge log files
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
    except Exception as e:
        print(f"Error setting up file logging: {e}")
        # Continue with console logging
    
    # Create and configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Log the configuration
    root_logger.info(f"Logging configured with level: {log_level}")
    root_logger.info(f"Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


# Configure logging when the module is imported
configure_logging()


# Add a convenience function for changing the log level at runtime
def set_log_level(level: str) -> None:
    """
    Set the log level for all handlers.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    if level.upper() not in LOG_LEVELS:
        raise ValueError(f"Invalid log level: {level}. Must be one of {list(LOG_LEVELS.keys())}")
        
    log_level = LOG_LEVELS[level.upper()]
    
    # Set level for the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Set level for all handlers
    for handler in root_logger.handlers:
        handler.setLevel(log_level)
        
    root_logger.info(f"Log level changed to: {level}")

