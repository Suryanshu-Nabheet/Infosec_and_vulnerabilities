"""
Models package for Course Platform Scraper

This package contains data models for representing
scraped data from the course platform.
"""

from .data_models import BaseModel, User, FinancialMetrics, ValidationError

__all__ = ['BaseModel', 'User', 'FinancialMetrics', 'ValidationError']

