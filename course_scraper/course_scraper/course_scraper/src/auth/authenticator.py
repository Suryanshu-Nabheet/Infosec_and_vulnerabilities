#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentication module for Course Platform Scraper

This module handles the authentication process for accessing the course platform,
supporting both requests-based and Selenium-based authentication methods.
"""

import time
import logging
from typing import Optional, Dict, Any, Union

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Import settings from config
from config import settings

# Set up logger
logger = logging.getLogger("course_scraper.auth")


class AuthenticationError(Exception):
    """Exception raised for authentication related errors."""
    pass


class Authenticator:
    """
    Authentication handler for the course platform.
    
    This class provides methods for authenticating with the course platform using
    either requests or Selenium based on the complexity of the login process.
    """
    
    def __init__(self, email: str, password: str):
        """
        Initialize the authenticator with login credentials.
        
        Args:
            email: Email address for login
            password: Password for login
        """
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.session.headers.update(settings.HTTP_HEADERS)
        self.driver = None
        self._authenticated = False
        logger.info("Authenticator initialized")
    
    @property
    def authenticated(self) -> bool:
        """
        Check if the authenticator is authenticated.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        return self._authenticated
    
    def authenticate(self, use_selenium: bool = False) -> bool:
        """
        Authenticate with the course platform.
        
        Args:
            use_selenium: Whether to use Selenium for authentication (for dynamic content)
            
        Returns:
            bool: True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        if self._authenticated:
            logger.debug("Already authenticated")
            return True
        
        logger.info(f"Attempting to authenticate with email: {self.email}")
        
        try:
            if use_selenium:
                result = self._authenticate_with_selenium()
            else:
                result = self._authenticate_with_requests()
                
            if result:
                self._authenticated = True
                logger.info("Authentication successful")
                return True
            else:
                raise AuthenticationError("Authentication failed")
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(f"Failed to authenticate: {e}") from e
    
    def _authenticate_with_requests(self) -> bool:
        """
        Authenticate using the requests library.
        
        Returns:
            bool: True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # First, get the login page to extract any CSRF token
            logger.debug(f"Accessing login page: {settings.LOGIN_URL}")
            response = self.session.get(
                settings.LOGIN_URL, 
                timeout=settings.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            # Extract CSRF token from the login page if present
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_token = None
            
            # Look for common CSRF token field names
            csrf_input = soup.find('input', {'name': 'csrf_token'}) or \
                         soup.find('input', {'name': '_csrf'}) or \
                         soup.find('input', {'name': 'csrfmiddlewaretoken'})
                         
            if csrf_input:
                csrf_token = csrf_input.get('value')
                logger.debug(f"CSRF token extracted: {csrf_token[:5]}...")
            
            # Prepare login data
            login_data = {
                'email': self.email,
                'password': self.password
            }
            
            # Add CSRF token if found
            if csrf_token:
                login_data['csrf_token'] = csrf_token
            
            # Add a delay to respect rate limiting
            time.sleep(settings.REQUEST_DELAY)
            
            # Submit login form
            logger.debug("Submitting login form")
            login_response = self.session.post(
                settings.LOGIN_URL,
                data=login_data,
                allow_redirects=True,
                timeout=settings.REQUEST_TIMEOUT
            )
            login_response.raise_for_status()
            
            # Save the raw HTML for debugging if needed
            with open(f"{settings.RAW_HTML_DIR}/login_response.html", 'w', encoding='utf-8') as f:
                f.write(login_response.text)
            
            # Check if login was successful
            success_indicators = ["logout", "dashboard", "profile", "account", "my courses"]
            login_html_lower = login_response.text.lower()
            
            # Look for any success indicators in the response
            login_success = any(indicator in login_html_lower for indicator in success_indicators)
            
            if login_success:
                logger.info("Authentication with requests successful")
                return True
            else:
                logger.warning("Authentication seems to have failed: no success indicators found in response")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Request error during authentication: {e}")
            raise AuthenticationError(f"Network error during authentication: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            raise AuthenticationError(f"Authentication failed: {e}")
    
    def _authenticate_with_selenium(self) -> bool:
        """
        Authenticate using Selenium for dynamic login forms.
        
        Returns:
            bool: True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            self._init_selenium()
            
            logger.debug(f"Navigating to login page: {settings.LOGIN_URL}")
            self.driver.get(settings.LOGIN_URL)
            
            # Wait for login form to load
            logger.debug("Waiting for login form to load")
            WebDriverWait(self.driver, settings.SELENIUM_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, settings.EMAIL_FIELD_SELECTOR))
            )
            
            # Fill in login form
            logger.debug("Filling in login form")
            email_input = self.driver.find_element(By.ID, settings.EMAIL_FIELD_SELECTOR)
            password_input = self.driver.find_element(By.ID, settings.PASSWORD_FIELD_SELECTOR)
            
            email_input.clear()
            email_input.send_keys(self.email)
            
            password_input.clear()
            password_input.send_keys(self.password)
            
            # Submit form
            logger.debug("Submitting login form")
            login_button = self.driver.find_element(By.XPATH, settings.LOGIN_BUTTON_SELECTOR)
            login_button.click()
            
            # Wait for login to complete - check for any indicators of successful login
            logger.debug("Waiting for login to complete")
            
            # Using a lambda to check multiple conditions for login success
            login_success = WebDriverWait(self.driver, settings.SELENIUM_TIMEOUT).until(
                lambda d: any(
                    indicator in d.current_url.lower() or indicator in d.page_source.lower()
                    for indicator in ["dashboard", "logout", "profile", "account"]
                )
            )
            
            if login_success:
                # Save the page source for debugging if needed
                with open(f"{settings.RAW_HTML_DIR}/login_response_selenium.html", 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                
                # Transfer cookies from Selenium to Requests session
                logger.debug("Transferring cookies from Selenium to Requests session")
                for cookie in self.driver.get_cookies():
                    self.session.cookies.set(cookie['name'], cookie['value'])
                
                logger.info("Authentication with Selenium successful")
                return True
            else:
                logger.warning("Authentication with Selenium seems to have failed")
                return False
                
        except TimeoutException:
            logger.error("Timed out waiting for login page elements")
            raise AuthenticationError("Login page elements not found within timeout period")
        except WebDriverException as e:
            logger.error(f"WebDriver error during authentication: {e}")
            raise AuthenticationError(f"WebDriver error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during Selenium authentication: {e}")
            raise AuthenticationError(f"Authentication with Selenium failed: {e}")
    
    def _init_selenium(self) -> None:
        """
        Initialize Selenium WebDriver.
        
        Raises:
            AuthenticationError: If Selenium initialization fails
        """
        if self.driver:
            return
            
        try:
            logger.debug("Initializing Selenium WebDriver")
            chrome_options = Options()
            
            if settings.HEADLESS:
                chrome_options.add_argument("--headless")
                
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"user-agent={settings.HTTP_HEADERS['User-Agent']}")
            chrome_options.add_argument(f"window-size={settings.SELENIUM_WINDOW_SIZE[0]},{settings.SELENIUM_WINDOW_SIZE[1]}")
            
            # Set up the driver with custom path if provided
            if settings.WEBDRIVER_PATH:
                from selenium.webdriver.chrome.service import Service
                service = Service(executable_path=settings.WEBDRIVER_PATH)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
                
            self.driver.set_page_load_timeout(settings.SELENIUM_TIMEOUT)
            logger.debug("Selenium WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Selenium WebDriver: {e}")
            raise AuthenticationError(f"Failed to initialize Selenium: {e}")
    
    def close(self) -> None:
        """Clean up resources."""
        if self.driver:
            logger.debug("Closing Selenium WebDriver")
            self.driver.quit()
            self.driver = None
            
        logger.debug("Closing requests session")
        self.session.close()
        logger.info("Authenticator resources cleaned up")

