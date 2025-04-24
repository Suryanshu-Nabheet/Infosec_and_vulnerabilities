#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Models Module for Course Platform Scraper

This module defines the data models used for storing and validating
scraped data from the course platform.
"""

import re
import json
import uuid
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, ClassVar, Type, Set, Union, TypeVar
from datetime import datetime

# Set up logger
logger = logging.getLogger("course_scraper.models")

# Type variable for BaseModel subclasses
T = TypeVar('T', bound='BaseModel')


class ValidationError(Exception):
    """Exception raised for data validation errors."""
    pass


class BaseModel(ABC):
    """
    Base model class for all data models.
    
    This abstract class provides common functionality for data models,
    including serialization, validation, and conversion methods.
    """
    
    # Fields that all models should have
    id: str
    created_at: str
    
    # Class variables to define model structure
    required_fields: ClassVar[Set[str]] = {'id', 'created_at'}
    optional_fields: ClassVar[Set[str]] = set()
    field_types: ClassVar[Dict[str, Type]] = {
        'id': str,
        'created_at': str
    }
    
    def __init__(self, **kwargs):
        """
        Initialize the model with provided values.
        
        Args:
            **kwargs: Key-value pairs to initialize the model fields
            
        Raises:
            ValidationError: If required fields are missing or field values are invalid
        """
        # Generate ID and timestamp if not provided
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.now().isoformat()
            
        # Validate the provided values
        self.validate(kwargs)
        
        # Set attributes
        for field, value in kwargs.items():
            setattr(self, field, value)
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> None:
        """
        Validate data against the model's field definitions.
        
        Args:
            data: Dictionary of field values to validate
            
        Raises:
            ValidationError: If validation fails
        """
        # Check for required fields
        for field in cls.required_fields:
            if field not in data:
                raise ValidationError(f"Required field '{field}' is missing")
        
        # Check field types
        for field, value in data.items():
            if field in cls.field_types and value is not None:
                expected_type = cls.field_types[field]
                
                # Special handling for fields that can be strings or converted to strings
                if expected_type == str and not isinstance(value, str):
                    try:
                        # Attempt to convert to string
                        data[field] = str(value)
                    except (ValueError, TypeError):
                        raise ValidationError(f"Field '{field}' should be a string or convertible to string")
                
                # Check types for other fields
                elif not isinstance(value, expected_type):
                    raise ValidationError(
                        f"Field '{field}' should be of type {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {
            field: getattr(self, field) 
            for field in list(self.required_fields) + list(self.optional_fields)
            if hasattr(self, field)
        }
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert the model to a JSON string.
        
        Args:
            indent: Number of spaces for indentation in JSON
            
        Returns:
            str: JSON string representation of the model
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create a model instance from a dictionary.
        
        Args:
            data: Dictionary containing field values
            
        Returns:
            T: Model instance
            
        Raises:
            ValidationError: If data validation fails
        """
        # Create a new instance of the specific model class
        return cls(**data)
    
    @classmethod
    def from_list(cls: Type[T], data_list: List[Dict[str, Any]]) -> List[T]:
        """
        Create model instances from a list of dictionaries.
        
        Args:
            data_list: List of dictionaries containing field values
            
        Returns:
            List[T]: List of model instances
        """
        models = []
        for i, data in enumerate(data_list):
            try:
                models.append(cls.from_dict(data))
            except ValidationError as e:
                logger.warning(f"Skipping item {i} due to validation error: {e}")
        return models
    
    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """
        Create a model instance from a JSON string.
        
        Args:
            json_str: JSON string containing field values
            
        Returns:
            T: Model instance
            
        Raises:
            ValidationError: If data validation fails
            json.JSONDecodeError: If JSON decoding fails
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


class User(BaseModel):
    """
    User model for storing user information.
    
    Attributes:
        id: Unique identifier for the user
        created_at: Timestamp when the record was created
        name: User's name
        email: User's email address
        paid: Whether the user has paid for the course
        join_date: Date when the user joined the platform
    """
    
    name: Optional[str]
    email: Optional[str]
    paid: bool
    join_date: Optional[str]
    scrape_date: str
    
    # Override class variables to define model structure
    required_fields: ClassVar[Set[str]] = {'id', 'created_at', 'scrape_date', 'paid'}
    optional_fields: ClassVar[Set[str]] = {'name', 'email', 'join_date'}
    field_types: ClassVar[Dict[str, Type]] = {
        'id': str,
        'created_at': str,
        'name': str,
        'email': str,
        'paid': bool,
        'join_date': str,
        'scrape_date': str
    }
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> None:
        """
        Validate user data.
        
        Args:
            data: Dictionary of user field values to validate
            
        Raises:
            ValidationError: If validation fails
        """
        # First, use the base validation
        super().validate(data)
        
        # Additional validation for user-specific fields
        
        # Email validation (if provided)
        if 'email' in data and data['email']:
            email = data['email']
            # Simple regex for email validation
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                raise ValidationError(f"Invalid email format: {email}")
        
        # Convert paid field to boolean if it's a string
        if 'paid' in data and isinstance(data['paid'], str):
            paid_text = data['paid'].lower()
            data['paid'] = (paid_text == 'true' or paid_text == 'yes' or paid_text == '1')


class FinancialMetrics(BaseModel):
    """
    Financial metrics model for storing financial data.
    
    Attributes:
        id: Unique identifier for the financial metrics record
        created_at: Timestamp when the record was created
        total_users: Total number of users on the platform
        paid_users: Number of paid users
        total_gmv: Total Gross Merchandise Value
        total_profit: Total profit
        avg_revenue_per_user: Average revenue per user
        conversion_rate: Conversion rate (percentage of paid users)
        timestamp: Timestamp when the financial data was scraped
    """
    
    total_users: int
    paid_users: int
    total_gmv: float
    total_profit: float
    avg_revenue_per_user: float
    conversion_rate: float
    timestamp: str
    processed_at: Optional[str]
    
    # Override class variables to define model structure
    required_fields: ClassVar[Set[str]] = {
        'id', 'created_at', 'total_users', 'paid_users', 
        'total_gmv', 'total_profit', 'timestamp'
    }
    optional_fields: ClassVar[Set[str]] = {
        'avg_revenue_per_user', 'conversion_rate', 'processed_at'
    }
    field_types: ClassVar[Dict[str, Type]] = {
        'id': str,
        'created_at': str,
        'total_users': int,
        'paid_users': int,
        'total_gmv': float,
        'total_profit': float,
        'avg_revenue_per_user': float,
        'conversion_rate': float,
        'timestamp': str,
        'processed_at': str
    }
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> None:
        """
        Validate financial metrics data.
        
        Args:
            data: Dictionary of financial field values to validate
            
        Raises:
            ValidationError: If validation fails
        """
        # First, perform type conversion for numeric fields
        if 'total_users' in data and not isinstance(data['total_users'], int):
            try:
                data['total_users'] = int(data['total_users'])
            except (ValueError, TypeError):
                raise ValidationError("total_users must be convertible to an integer")
                
        if 'paid_users' in data and not isinstance(data['paid_users'], int):
            try:
                data['paid_users'] = int(data['paid_users'])
            except (ValueError, TypeError):
                raise ValidationError("paid_users must be convertible to an integer")
        
        for field in ['total_gmv', 'total_profit', 'avg_revenue_per_user', 'conversion_rate']:
            if field in data and not isinstance(data[field], float):
                try:
                    data[field] = float(data[field])
                except (ValueError, TypeError):
                    raise ValidationError(f"{field} must be convertible to a float")
        
        # Use the base validation
        super().validate(data)
        
        # Additional validation for financial-specific fields
        if 'total_users' in data and data['total_users'] < 0:
            raise ValidationError("total_users cannot be negative")
            
        if 'paid_users' in data and data['paid_users'] < 0:
            raise ValidationError("paid_users cannot be negative")
            
        if 'total_gmv' in data and data['total_gmv'] < 0:
            raise ValidationError("total_gmv cannot be negative")
            
        if 'total_profit' in data:
            # Profit can be negative (losses), so no need to check
            pass
            
        if 'conversion_rate' in data:
            rate = data['conversion_rate']
            if rate < 0 or rate > 100:
                raise ValidationError("conversion_rate must be between 0 and 100")
    
    def calculate_derived_metrics(self) -> None:
        """
        Calculate derived financial metrics.
        
        This method calculates metrics that can be derived from the base metrics,
        such as average revenue per user and conversion rate.
        """
        # Calculate average revenue per user
        if hasattr(self, 'total_gmv') and hasattr(self, 'paid_users') and self.paid_users > 0:
            self.avg_revenue_per_user = round(self.total_gmv / self.paid_users, 2)
        else:
            self.avg_revenue_per_user = 0.0
        
        # Calculate conversion rate
        if hasattr(self, 'total_users') and hasattr(self, 'paid_users') and self.total_users > 0:
            self.conversion_rate = round((self.paid_users / self.total_users) * 100, 2)
        else:
            self.conversion_rate = 0.0

