#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Storage Module for Course Platform Scraper

This module provides functions for saving data to various formats,
including CSV and JSON, with error handling and data validation.
"""

import os
import csv
import json
import shutil
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import settings from config
from config import settings

# Set up logger
logger = logging.getLogger("course_scraper.data_storage")


class DataStorageError(Exception):
    """Exception raised for data storage related errors."""
    pass


def save_to_csv(
    data: List[Dict[str, Any]],
    filepath: str,
    create_backup: bool = True,
    validate: bool = True
) -> str:
    """
    Save data to a CSV file.
    
    Args:
        data: List of dictionaries to save
        filepath: Path to the CSV file
        create_backup: Whether to create a backup of existing file
        validate: Whether to validate the data before saving
        
    Returns:
        str: Path to the saved file
        
    Raises:
        DataStorageError: If saving fails
    """
    if not data:
        logger.warning("No data to save to CSV")
        return filepath
        
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Validate data if requested
        if validate:
            _validate_csv_data(data)
        
        # Create backup if requested and file exists
        if create_backup and os.path.exists(filepath):
            backup_path = _create_backup(filepath)
            logger.info(f"Created backup: {backup_path}")
        
        # Get all field names from the data
        fieldnames = set()
        for item in data:
            fieldnames.update(item.keys())
            
        # Sort fieldnames for consistent column order
        fieldnames = sorted(fieldnames)
        
        # Write data to CSV
        logger.info(f"Saving {len(data)} records to CSV: {filepath}")
        with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            
        logger.info(f"Successfully saved data to CSV: {filepath}")
        return filepath
        
    except Exception as e:
        error_msg = f"Failed to save data to CSV: {e}"
        logger.error(error_msg)
        raise DataStorageError(error_msg)


def save_to_json(
    data: Any,
    filepath: str,
    create_backup: bool = True,
    indent: int = 4,
    validate: bool = True
) -> str:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save (should be JSON serializable)
        filepath: Path to the JSON file
        create_backup: Whether to create a backup of existing file
        indent: Number of spaces for indentation in JSON file
        validate: Whether to validate the data before saving
        
    Returns:
        str: Path to the saved file
        
    Raises:
        DataStorageError: If saving fails
    """
    if data is None:
        logger.warning("No data to save to JSON")
        return filepath
        
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Validate data if requested
        if validate:
            _validate_json_data(data)
        
        # Create backup if requested and file exists
        if create_backup and os.path.exists(filepath):
            backup_path = _create_backup(filepath)
            logger.info(f"Created backup: {backup_path}")
        
        # Write data to JSON
        logger.info(f"Saving data to JSON: {filepath}")
        with open(filepath, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=indent, ensure_ascii=False)
            
        logger.info(f"Successfully saved data to JSON: {filepath}")
        return filepath
        
    except Exception as e:
        error_msg = f"Failed to save data to JSON: {e}"
        logger.error(error_msg)
        raise DataStorageError(error_msg)


def load_from_csv(filepath: str) -> List[Dict[str, Any]]:
    """
    Load data from a CSV file.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        List[Dict[str, Any]]: List of dictionaries containing the CSV data
        
    Raises:
        DataStorageError: If loading fails
    """
    try:
        if not os.path.exists(filepath):
            logger.warning(f"CSV file not found: {filepath}")
            return []
            
        logger.info(f"Loading data from CSV: {filepath}")
        data = []
        
        with open(filepath, 'r', newline='', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            data = [row for row in reader]
            
        logger.info(f"Successfully loaded {len(data)} records from CSV: {filepath}")
        return data
        
    except Exception as e:
        error_msg = f"Failed to load data from CSV: {e}"
        logger.error(error_msg)
        raise DataStorageError(error_msg)


def load_from_json(filepath: str) -> Any:
    """
    Load data from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Any: Data loaded from the JSON file
        
    Raises:
        DataStorageError: If loading fails
    """
    try:
        if not os.path.exists(filepath):
            logger.warning(f"JSON file not found: {filepath}")
            return None
            
        logger.info(f"Loading data from JSON: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            
        logger.info(f"Successfully loaded data from JSON: {filepath}")
        return data
        
    except Exception as e:
        error_msg = f"Failed to load data from JSON: {e}"
        logger.error(error_msg)
        raise DataStorageError(error_msg)


def _create_backup(filepath: str) -> str:
    """
    Create a backup of a file.
    
    Args:
        filepath: Path to the file to backup
        
    Returns:
        str: Path to the backup file
        
    Raises:
        DataStorageError: If backup creation fails
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{filepath}.{timestamp}.bak"
        
        shutil.copy2(filepath, backup_path)
        return backup_path
        
    except Exception as e:
        error_msg = f"Failed to create backup of {filepath}: {e}"
        logger.error(error_msg)
        raise DataStorageError(error_msg)


def _validate_csv_data(data: List[Dict[str, Any]]) -> None:
    """
    Validate data for CSV storage.
    
    Args:
        data: List of dictionaries to validate
        
    Raises:
        DataStorageError: If validation fails
    """
    if not isinstance(data, list):
        raise DataStorageError(f"CSV data must be a list, got {type(data).__name__}")
        
    if not all(isinstance(item, dict) for item in data):
        raise DataStorageError("All items in CSV data must be dictionaries")


def _validate_json_data(data: Any) -> None:
    """
    Validate data for JSON storage.
    
    Args:
        data: Data to validate
        
    Raises:
        DataStorageError: If validation fails
    """
    try:
        # Check if data is JSON serializable by trying to encode it
        json.dumps(data)
    except (TypeError, OverflowError) as e:
        raise DataStorageError(f"Data is not JSON serializable: {e}")


def save_raw_html(html_content: str, filename: str) -> str:
    """
    Save raw HTML content to a file.
    
    Args:
        html_content: HTML content to save
        filename: Filename to save the content as
        
    Returns:
        str: Path to the saved file
        
    Raises:
        DataStorageError: If saving fails
    """
    try:
        filepath = os.path.join(settings.RAW_HTML_DIR, filename)
        logger.debug(f"Saving raw HTML to: {filepath}")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return filepath
        
    except Exception as e:
        error_msg = f"Failed to save raw HTML: {e}"
        logger.warning(error_msg)
        raise DataStorageError(error_msg)

