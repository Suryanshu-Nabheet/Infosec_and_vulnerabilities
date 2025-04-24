#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Module for Course Platform Scraper

This module contains all configuration settings and constants for the web scraper,
including URLs, request parameters, and file paths.
"""

import os
import sys
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# URLs
BASE_URL = "https://harkirat.classx.co.in"
LOGIN_URL = f"{BASE_URL}/login"
COURSE_URL = f"{BASE_URL}/new-courses/8-live-0-100-complete"
DASHBOARD_URL = f"{BASE_URL}/dashboard"
ANALYTICS_URL = f"{BASE_URL}/dashboard/analytics"
USER_URL = f"{BASE_URL}/dashboard/users"
PAYMENT_URL = f"{BASE_URL}/dashboard/payments"
API_BASE_URL = f"{BASE_URL}/api"
COURSE_LIST_API = f"{API_BASE_URL}/courses"
USER_LIST_API = f"{API_BASE_URL}/users"
PAYMENT_LIST_API = f"{API_BASE_URL}/payments"

# HTTP Headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache"
}

# User-Agent Rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Edge/120.0.0.0",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1",
]

def get_random_user_agent() -> str:
    """Returns a random user agent from the list"""
    return random.choice(USER_AGENTS)

def get_headers(use_random_agent: bool = True) -> Dict[str, str]:
    """Returns HTTP headers, optionally with a random user agent"""
    headers = DEFAULT_HEADERS.copy()
    if use_random_agent:
        headers["User-Agent"] = get_random_user_agent()
    return headers

# Selenium Settings
SELENIUM_TIMEOUT = 30  # seconds
WEBDRIVER_PATH = None  # Set this if you need a specific driver path
HEADLESS = True
SELENIUM_WINDOW_SIZE = (1920, 1080)
SELENIUM_PAGE_LOAD_TIMEOUT = 60  # seconds
SELENIUM_SCRIPT_TIMEOUT = 30  # seconds
SELENIUM_IMPLICIT_WAIT = 10  # seconds
USE_UNDETECTED_CHROMEDRIVER = False  # Set to True to use undetected_chromedriver to bypass detection
SELENIUM_ARGUMENTS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-extensions",
    "--no-sandbox",
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--disable-notifications",
]

# Request Settings
REQUEST_TIMEOUT = 30  # seconds
REQUEST_DELAY = 3  # seconds between requests for rate limiting
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 0.5  # exponential backoff factor
RETRY_STATUS_FORCELIST = [429, 500, 502, 503, 504]  # HTTP status codes to retry
RETRY_METHODS = ["GET", "POST"]  # HTTP methods to retry

# Rate Limiting
MIN_REQUEST_DELAY = 2  # minimum seconds between requests
MAX_REQUEST_DELAY = 5  # maximum seconds between requests
RATE_LIMIT_ENABLED = True  # enable rate limiting
RATE_LIMIT_REQUESTS = 10  # number of requests
RATE_LIMIT_PERIOD = 60  # in this many seconds
RANDOMIZE_DELAY = True  # randomize delay between requests

def get_random_delay() -> float:
    """Returns a random delay between MIN_REQUEST_DELAY and MAX_REQUEST_DELAY"""
    if RANDOMIZE_DELAY:
        return round(random.uniform(MIN_REQUEST_DELAY, MAX_REQUEST_DELAY), 2)
    return REQUEST_DELAY

# Directory Structure
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
COOKIES_DIR = os.path.join(DATA_DIR, "cookies")
SCREENSHOTS_DIR = os.path.join(DATA_DIR, "screenshots")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")

# Output File Paths
USER_DATA_CSV = os.path.join(PROCESSED_DATA_DIR, "user_data.csv")
FINANCIAL_DATA_JSON = os.path.join(PROCESSED_DATA_DIR, "financial_data.json")
COURSE_DATA_JSON = os.path.join(PROCESSED_DATA_DIR, "course_data.json")
RAW_HTML_DIR = os.path.join(RAW_DATA_DIR, "html")
COOKIES_FILE = os.path.join(COOKIES_DIR, "session_cookies.json")
LOG_FILE = os.path.join(LOGS_DIR, "scraper.log")
ERROR_SCREENSHOTS_DIR = os.path.join(SCREENSHOTS_DIR, "errors")

# Data Export Settings
CSV_DELIMITER = ','
CSV_QUOTECHAR = '"'
CSV_QUOTING = 1  # csv.QUOTE_ALL
JSON_INDENT = 4
EXPORT_ENCODING = 'utf-8'
DEFAULT_DATA_FORMAT = 'json'  # 'json' or 'csv'

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_BACKUP_COUNT = 5
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
CONSOLE_LOG_LEVEL = "INFO"
FILE_LOG_LEVEL = "DEBUG"
LOG_TO_CONSOLE = True
LOG_TO_FILE = True

# Error handling
TAKE_SCREENSHOT_ON_ERROR = True
SAVE_HTML_ON_ERROR = True

# Make sure directories exist
all_directories = [
    DATA_DIR, LOGS_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, 
    RAW_HTML_DIR, CACHE_DIR, COOKIES_DIR, SCREENSHOTS_DIR, 
    REPORTS_DIR, ERROR_SCREENSHOTS_DIR
]

for directory in all_directories:
    os.makedirs(directory, exist_ok=True)

# Authentication Settings
AUTH_METHOD = "form"  # "form" or "api"
SESSION_TIMEOUT = 3600  # seconds (1 hour)
STORE_COOKIES = True
COOKIES_EXPIRY_DAYS = 7
AUTO_RELOGIN = True
MAX_LOGIN_ATTEMPTS = 3
LOGIN_REQUIRED = True
TOKEN_REFRESH_MARGIN = 300  # seconds before expiry to refresh token

# Login Form Selectors
EMAIL_FIELD_SELECTOR = "email"  # ID or name of the email input field
PASSWORD_FIELD_SELECTOR = "password"  # ID or name of the password input field
LOGIN_BUTTON_SELECTOR = "//button[contains(text(), 'Login') or contains(text(), 'Sign in')]"  # X

