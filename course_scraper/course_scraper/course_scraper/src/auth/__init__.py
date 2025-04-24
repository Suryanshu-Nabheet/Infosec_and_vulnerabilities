"""
Authentication package for Course Platform Scraper

This package contains modules for handling authentication with the course platform.
"""

from .authenticator import Authenticator, AuthenticationError

__all__ = ['Authenticator', 'AuthenticationError']

