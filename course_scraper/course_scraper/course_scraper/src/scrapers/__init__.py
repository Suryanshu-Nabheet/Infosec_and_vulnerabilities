"""
Scrapers package for Course Platform Scraper

This package contains modules for extracting different types of data
from the course platform.
"""

from .user_scraper import UserScraper, UserScrapingError
from .financial_scraper import FinancialScraper, FinancialScrapingError

__all__ = [
    'UserScraper', 
    'UserScrapingError',
    'FinancialScraper',
    'FinancialScrapingError'
]

