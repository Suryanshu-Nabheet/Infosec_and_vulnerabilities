#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User Scraper Module for Course Platform Scraper

This module handles the extraction of user data from the course platform,
including user names, emails, payment status, and other available details.
"""

import os
import time
import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

# Import settings from config
from config import settings
from src.auth.authenticator import Authenticator

# Set up logger
logger = logging.getLogger("course_scraper.user_scraper")


class UserScrapingError(Exception):
    """Exception raised for user data scraping related errors."""
    pass


class UserScraper:
    """
    User data scraper for the course platform.
    
    This class extracts information about users from the course platform,
    including user names, emails, payment status, join dates, and other
    available details.
    """
    
    def __init__(self, authenticator: Authenticator):
        """
        Initialize the user scraper with an authenticator.
        
        Args:
            authenticator: Authenticated authenticator object with active session
        
        Raises:
            UserScrapingError: If the authenticator is not authenticated
        """
        if not authenticator.authenticated:
            raise UserScrapingError("Authenticator must be authenticated before initializing UserScraper")
            
        self.authenticator = authenticator
        self.session = authenticator.session
        self.driver = authenticator.driver
        logger.info("UserScraper initialized with authenticated session")
    
    def scrape(self, use_selenium: bool = False) -> List[Dict[str, Any]]:
        """
        Scrape user data from the course platform.
        
        Args:
            use_selenium: Whether to use Selenium for scraping (for dynamic content)
            
        Returns:
            List[Dict[str, Any]]: List of user data dictionaries
            
        Raises:
            UserScrapingError: If scraping fails
        """
        logger.info("Starting user data scraping")
        
        try:
            if use_selenium and self.driver:
                return self._scrape_with_selenium()
            else:
                return self._scrape_with_requests()
        except Exception as e:
            logger.error(f"Failed to scrape user data: {e}")
            raise UserScrapingError(f"User data scraping failed: {e}") from e
    
    def _scrape_with_requests(self) -> List[Dict[str, Any]]:
        """
        Scrape user data using the requests library.
        
        Returns:
            List[Dict[str, Any]]: List of user data dictionaries
            
        Raises:
            UserScrapingError: If scraping fails
        """
        logger.info(f"Scraping user data with requests from: {settings.COURSE_URL}")
        user_data = []
        current_page = 1
        has_next_page = True
        
        while has_next_page:
            try:
                # Construct the URL for the current page
                page_url = f"{settings.COURSE_URL}?page={current_page}"
                
                # Implement retry mechanism
                content = self._fetch_with_retry(page_url)
                
                # Save raw HTML for debugging
                page_filename = f"users_page_{current_page}.html"
                self._save_raw_html(content, page_filename)
                
                # Parse and extract user data
                page_user_data, has_next_page = self._parse_user_data(content, current_page)
                user_data.extend(page_user_data)
                
                logger.info(f"Scraped {len(page_user_data)} users from page {current_page}")
                
                # Move to the next page if it exists
                if has_next_page:
                    current_page += 1
                    # Respect rate limiting
                    time.sleep(settings.REQUEST_DELAY)
                    
            except Exception as e:
                logger.error(f"Error scraping page {current_page}: {e}")
                raise UserScrapingError(f"Failed to scrape page {current_page}: {e}")
        
        # Post-process the collected data
        processed_data = self._process_user_data(user_data)
        
        logger.info(f"Successfully scraped data for {len(processed_data)} users")
        return processed_data
    
    def _scrape_with_selenium(self) -> List[Dict[str, Any]]:
        """
        Scrape user data using Selenium for dynamic content.
        
        Returns:
            List[Dict[str, Any]]: List of user data dictionaries
            
        Raises:
            UserScrapingError: If scraping fails
        """
        if not self.driver:
            raise UserScrapingError("Selenium WebDriver not available")
            
        logger.info(f"Scraping user data with Selenium from: {settings.COURSE_URL}")
        user_data = []
        current_page = 1
        has_next_page = True
        
        try:
            # Navigate to the course page
            self.driver.get(settings.COURSE_URL)
            
            while has_next_page:
                try:
                    # Wait for user data to load
                    WebDriverWait(self.driver, settings.SELENIUM_TIMEOUT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, settings.USER_LIST_SELECTOR))
                    )
                    
                    # Save raw HTML for debugging
                    content = self.driver.page_source
                    page_filename = f"users_page_{current_page}_selenium.html"
                    self._save_raw_html(content, page_filename)
                    
                    # Parse and extract user data
                    page_user_data, has_next_page = self._parse_user_data(content, current_page)
                    user_data.extend(page_user_data)
                    
                    logger.info(f"Scraped {len(page_user_data)} users from page {current_page} with Selenium")
                    
                    # Check if there's a next page button and click it if available
                    if has_next_page:
                        # Look for typical pagination elements - adjust as needed
                        next_button = self.driver.find_element(By.CSS_SELECTOR, 
                                                              "a.next-page, a.pagination-next, li.next a")
                        if next_button and next_button.is_displayed() and next_button.is_enabled():
                            next_button.click()
                            current_page += 1
                            # Wait for the page to load
                            time.sleep(settings.REQUEST_DELAY)
                        else:
                            has_next_page = False
                    
                except NoSuchElementException:
                    # No next page button found
                    has_next_page = False
                except TimeoutException:
                    logger.warning(f"Timed out waiting for user data on page {current_page}")
                    has_next_page = False
                except Exception as e:
                    logger.error(f"Error scraping page {current_page} with Selenium: {e}")
                    raise UserScrapingError(f"Failed to scrape page {current_page} with Selenium: {e}")
            
            # Post-process the collected data
            processed_data = self._process_user_data(user_data)
            
            logger.info(f"Successfully scraped data for {len(processed_data)} users with Selenium")
            return processed_data
            
        except Exception as e:
            logger.error(f"Selenium scraping error: {e}")
            raise UserScrapingError(f"Selenium user data scraping failed: {e}")
    
    def _fetch_with_retry(self, url: str, max_retries: int = None) -> str:
        """
        Fetch URL content with retry mechanism.
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts (defaults to settings.MAX_RETRIES)
            
        Returns:
            str: HTML content of the page
            
        Raises:
            UserScrapingError: If all retry attempts fail
        """
        if max_retries is None:
            max_retries = settings.MAX_RETRIES
            
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                logger.debug(f"Fetching URL: {url} (Attempt {retry_count + 1}/{max_retries})")
                
                response = self.session.get(
                    url,
                    timeout=settings.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                
                return response.text
                
            except requests.RequestException as e:
                retry_count += 1
                last_error = e
                wait_time = 2 ** retry_count  # Exponential backoff
                
                logger.warning(f"Request failed: {e}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        error_msg = f"Failed to fetch {url} after {max_retries} attempts: {last_error}"
        logger.error(error_msg)
        raise UserScrapingError(error_msg)
    
    def _save_raw_html(self, content: str, filename: str) -> None:
        """
        Save raw HTML content to file for debugging.
        
        Args:
            content: HTML content to save
            filename: Filename to save the content as
        """
        try:
            filepath = os.path.join(settings.RAW_HTML_DIR, filename)
            logger.debug(f"Saving raw HTML to: {filepath}")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            logger.warning(f"Failed to save raw HTML: {e}")
    
    def _parse_user_data(self, html_content: str, page_number: int) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Parse HTML content to extract user data.
        
        Args:
            html_content: HTML content to parse
            page_number: Current page number
            
        Returns:
            Tuple[List[Dict[str, Any]], bool]: Tuple of (user data list, has next page flag)
        """
        logger.debug(f"Parsing user data from page {page_number}")
        soup = BeautifulSoup(html_content, 'html.parser')
        user_data = []
        
        # Find all user elements on the page using the selector from settings
        user_elements = soup.select(settings.USER_LIST_SELECTOR)
        
        if not user_elements:
            logger.warning(f"No user elements found on page {page_number} using selector: {settings.USER_LIST_SELECTOR}")
        
        # Process each user element
        for i, user_element in enumerate(user_elements):
            try:
                user = {
                    'id': str(uuid.uuid4()),  # Generate a unique ID for each user
                    'scrape_date': datetime.now().isoformat()
                }
                
                # Extract user name
                name_elem = user_element.select_one(settings.USER_NAME_SELECTOR)
                if name_elem:
                    user['name'] = name_elem.get_text(strip=True)
                
                # Extract user email
                email_elem = user_element.select_one(settings.USER_EMAIL_SELECTOR)
                if email_elem:
                    user['email'] = email_elem.get_text(strip=True)
                
                # Extract payment status
                payment_elem = user_element.select_one(settings.USER_PAYMENT_STATUS_SELECTOR)
                if payment_elem:
                    payment_text = payment_elem.get_text(strip=True).lower()
                    user['paid'] = 'paid' in payment_text or 'success' in payment_text
                
                # Extract join date if available
                join_date_elem = user_element.select_one(settings.USER_JOIN_DATE_SELECTOR)
                if join_date_elem:
                    user['join_date'] = join_date_elem.get_text(strip=True)
                
                # Add any other available and relevant user information
                # (This part would be customized based on the actual HTML structure)
                
                user_data.append(user)
                
            except Exception as e:
                logger.warning(f"Error parsing user element {i+1} on page {page_number}: {e}")
        
        # Check if there's a next page by looking for pagination elements
        has_next_page = self._check_for_next_page(soup)
        
        return user_data, has_next_page
    
    def _check_for_next_page(self, soup: BeautifulSoup) -> bool:
        """
        Check if there's a next page in the pagination.
        
        Args:
            soup: BeautifulSoup object of the current page
            
        Returns:
            bool: True if there's a next page, False otherwise
        """
        # Look for common pagination elements
        # This needs to be customized based on the actual HTML structure
        next_button = soup.select_one("a.next-page, a.pagination-next, li.next:not(.disabled) a")
        
        # Check for "page X of Y" text
        page_info = soup.select_one(".pagination-info")
        if page_info:
            text = page_info.get_text(strip=True)
            if "of" in text.lower():
                parts = text.split("of")
                try:
                    current = int(parts[0].strip().split()[-1])
                    total = int(parts[1].strip().split()[0])
                    return current < total
                except (ValueError, IndexError):
                    pass
        
        return next_button is not None
    
    def _process_user_data(self, user_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and clean the extracted user data.
        
        Args:
            user_data: Raw extracted user data
            
        Returns:
            List[Dict[str, Any]]: Processed user data
        """
        logger.debug(f"Processing {len(user_data)} user records")
        processed_data = []
        
        for user in user_data:
            try:
                # Create a copy of the user dictionary
                processed_user = user.copy()
                
                # Clean and standardize data
                if 'name' in processed_user:
                    processed_user['name'] = processed_user['name'].strip().title()
                
                if 'email' in processed_user:
                    processed_user['email'] = processed_user['email'].strip().lower()
                
                # Standardize the 'paid' field to a boolean
                # Standardize the 'paid' field to a boolean
                if 'paid' in processed_user:
                    if isinstance(processed_user['paid'], str):
                        processed_user['paid'] = processed_user['paid'].lower() in ('true', 'yes', 'paid', 'success', '1')
                
                # Process join date to standard format if available
                if 'join_date' in processed_user and processed_user['join_date']:
                    try:
                        # Try various date formats
                        date_formats = [
                            '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', 
                            '%b %d, %Y', '%d %b %Y', '%B %d, %Y',
                            '%Y-%m-%d %H:%M:%S'
                        ]
                        
                        join_date = None
                        for date_format in date_formats:
                            try:
                                join_date = datetime.strptime(processed_user['join_date'], date_format)
                                break
                            except ValueError:
                                continue
                        
                        if join_date:
                            processed_user['join_date'] = join_date.isoformat()
                        else:
                            logger.warning(f"Could not parse join date: {processed_user['join_date']}")
                    except Exception as e:
                        logger.warning(f"Error processing join date: {e}")
                
                # Validate and clean email format
                if 'email' in processed_user and processed_user['email']:
                    if '@' not in processed_user['email'] or '.' not in processed_user['email']:
                        logger.warning(f"Invalid email format: {processed_user['email']}")
                        processed_user['email_valid'] = False
                    else:
                        processed_user['email_valid'] = True
                
                # Add additional derived fields
                processed_user['processed_timestamp'] = datetime.now().isoformat()
                
                # Validate the record
                valid_record = self._validate_user_record(processed_user)
                
                if valid_record:
                    processed_data.append(processed_user)
                else:
                    logger.warning(f"Skipping invalid user record: {processed_user.get('id', 'unknown')}")
                
            except Exception as e:
                logger.error(f"Error processing user data: {e}")
        
        return processed_data
    
    def _validate_user_record(self, user: Dict[str, Any]) -> bool:
        """
        Validate a user record to ensure it contains required fields.
        
        Args:
            user: User data dictionary to validate
            
        Returns:
            bool: True if the record is valid, False otherwise
        """
        # Check if record has minimum required fields
        required_fields = ['id', 'scrape_date']
        
        # Ensure that at least one identifying field exists
        identifying_fields = ['name', 'email']
        has_identifier = any(field in user and user[field] for field in identifying_fields)
        
        has_required = all(field in user for field in required_fields)
        
        return has_required and has_identifier
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Save user data to CSV file.
        
        Args:
            data: List of user data dictionaries
            filename: Optional filename (defaults to users_{timestamp}.csv)
            
        Returns:
            str: Path to the saved CSV file
            
        Raises:
            UserScrapingError: If saving fails
        """
        import csv
        from datetime import datetime
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"users_{timestamp}.csv"
        
        filepath = os.path.join(settings.PROCESSED_DATA_DIR, filename)
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Identify all possible field names from all records
            fieldnames = set()
            for user in data:
                fieldnames.update(user.keys())
            
            fieldnames = sorted(list(fieldnames))
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
                
            logger.info(f"Saved {len(data)} user records to {filepath}")
            return filepath
            
        except Exception as e:
            error_msg = f"Failed to save user data to CSV: {e}"
            logger.error(error_msg)
            raise UserScrapingError(error_msg)
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Save user data to JSON file.
        
        Args:
            data: List of user data dictionaries
            filename: Optional filename (defaults to users_{timestamp}.json)
            
        Returns:
            str: Path to the saved JSON file
            
        Raises:
            UserScrapingError: If saving fails
        """
        import json
        from datetime import datetime
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"users_{timestamp}.json"
        
        filepath = os.path.join(settings.PROCESSED_DATA_DIR, filename)
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Custom JSON encoder to handle datetime objects
            class DateTimeEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    return super(DateTimeEncoder, self).default(obj)
            
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, cls=DateTimeEncoder, indent=4)
                
            logger.info(f"Saved {len(data)} user records to {filepath}")
            return filepath
            
        except Exception as e:
            error_msg = f"Failed to save user data to JSON: {e}"
            logger.error(error_msg)
            raise UserScrapingError(error_msg)
