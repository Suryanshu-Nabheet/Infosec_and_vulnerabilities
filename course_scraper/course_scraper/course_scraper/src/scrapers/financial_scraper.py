#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Financial Data Scraper Module for Course Platform Scraper

This module handles the extraction of financial data from the course platform,
including GMV (Gross Merchandise Value), total profit, number of paid users,
and other financial metrics.
"""

import os
import time
import logging
import re
from typing import Dict, Any, Optional, Union
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Import settings from config
from config import settings
from src.auth.authenticator import Authenticator

# Set up logger
logger = logging.getLogger("course_scraper.financial_scraper")


class FinancialScrapingError(Exception):
    """Exception raised for financial data scraping related errors."""
    pass


class FinancialScraper:
    """
    Financial data scraper for the course platform.
    
    This class extracts financial metrics from the course platform,
    including GMV, total profit, number of paid users, and other
    financial data.
    """
    
    def __init__(self, authenticator: Authenticator):
        """
        Initialize the financial scraper with an authenticator.
        
        Args:
            authenticator: Authenticated authenticator object with active session
        
        Raises:
            FinancialScrapingError: If the authenticator is not authenticated
        """
        if not authenticator.authenticated:
            raise FinancialScrapingError("Authenticator must be authenticated before initializing FinancialScraper")
            
        self.authenticator = authenticator
        self.session = authenticator.session
        self.driver = authenticator.driver
        logger.info("FinancialScraper initialized with authenticated session")
    
    def scrape(self, use_selenium: bool = False) -> Dict[str, Any]:
        """
        Scrape financial data from the course platform.
        
        Args:
            use_selenium: Whether to use Selenium for scraping (for dynamic content)
            
        Returns:
            Dict[str, Any]: Dictionary of financial metrics
            
        Raises:
            FinancialScrapingError: If scraping fails
        """
        logger.info("Starting financial data scraping")
        
        try:
            if use_selenium and self.driver:
                financial_data = self._scrape_with_selenium()
            else:
                financial_data = self._scrape_with_requests()
                
            # Process and clean the data
            processed_data = self._process_financial_data(financial_data)
            
            logger.info("Financial data scraping completed successfully")
            return processed_data
            
        except Exception as e:
            logger.error(f"Failed to scrape financial data: {e}")
            raise FinancialScrapingError(f"Financial data scraping failed: {e}") from e
    
    def _scrape_with_requests(self) -> Dict[str, Any]:
        """
        Scrape financial data using the requests library.
        
        Returns:
            Dict[str, Any]: Dictionary of financial metrics
            
        Raises:
            FinancialScrapingError: If scraping fails
        """
        logger.info(f"Scraping financial data with requests from: {settings.ANALYTICS_URL}")
        
        try:
            # Implement retry mechanism
            content = self._fetch_with_retry(settings.ANALYTICS_URL)
            
            # Save raw HTML for debugging
            self._save_raw_html(content, "financial_data.html")
            
            # Parse and extract financial data
            financial_data = self._parse_financial_data(content)
            
            return financial_data
            
        except Exception as e:
            logger.error(f"Error scraping financial data with requests: {e}")
            raise FinancialScrapingError(f"Failed to scrape financial data with requests: {e}")
    
    def _scrape_with_selenium(self) -> Dict[str, Any]:
        """
        Scrape financial data using Selenium for dynamic content.
        
        Returns:
            Dict[str, Any]: Dictionary of financial metrics
            
        Raises:
            FinancialScrapingError: If scraping fails
        """
        if not self.driver:
            raise FinancialScrapingError("Selenium WebDriver not available")
            
        logger.info(f"Scraping financial data with Selenium from: {settings.ANALYTICS_URL}")
        
        try:
            # Navigate to the analytics page
            self.driver.get(settings.ANALYTICS_URL)
            
            # Wait for financial data to load
            WebDriverWait(self.driver, settings.SELENIUM_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                                              ".financial-metrics, .dashboard-stats, .analytics-container"))
            )
            
            # In case the page uses JavaScript to load data, give it some extra time
            time.sleep(2)
            
            # Save raw HTML for debugging
            content = self.driver.page_source
            self._save_raw_html(content, "financial_data_selenium.html")
            
            # Parse and extract financial data
            financial_data = self._parse_financial_data(content)
            
            return financial_data
            
        except TimeoutException:
            logger.error("Timed out waiting for financial data elements")
            raise FinancialScrapingError("Financial data elements not found within timeout period")
        except Exception as e:
            logger.error(f"Selenium scraping error: {e}")
            raise FinancialScrapingError(f"Selenium financial data scraping failed: {e}")
    
    def _fetch_with_retry(self, url: str, max_retries: int = None) -> str:
        """
        Fetch URL content with retry mechanism.
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts (defaults to settings.MAX_RETRIES)
            
        Returns:
            str: HTML content of the page
            
        Raises:
            FinancialScrapingError: If all retry attempts fail
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
        raise FinancialScrapingError(error_msg)
    
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
    
    def _parse_financial_data(self, html_content: str) -> Dict[str, Any]:
        """
        Parse HTML content to extract financial data.
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            Dict[str, Any]: Dictionary of financial metrics
        """
        logger.debug("Parsing financial data")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Initialize financial data with default values
        financial_data = {
            "total_users": 0,
            "paid_users": 0,
            "total_gmv": 0.0,
            "total_profit": 0.0,
            "avg_revenue_per_user": 0.0,
            "conversion_rate": 0.0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Extract total users
        self._extract_metric(soup, financial_data, "total_users", settings.TOTAL_USERS_SELECTOR)
        
        # Extract paid users
        self._extract_metric(soup, financial_data, "paid_users", settings.PAID_USERS_SELECTOR)
        
        # Extract GMV (Gross Merchandise Value)
        self._extract_metric(soup, financial_data, "total_gmv", settings.TOTAL_GMV_SELECTOR, convert_to_float=True)
        
        # Extract total profit
        self._extract_metric(soup, financial_data, "total_profit", settings.TOTAL_PROFIT_SELECTOR, convert_to_float=True)
        
        # Calculate derived metrics
        self._calculate_derived_metrics(financial_data)
        
        logger.info(f"Extracted financial data: {financial_data}")
        return financial_data
    
    def _extract_metric(self, soup: BeautifulSoup, data: Dict[str, Any], 
                        key: str, selector: str, convert_to_float: bool = False) -> None:
        """
        Extract a specific metric from the HTML using the provided selector.
        
        Args:
            soup: BeautifulSoup object of the page
            data: Dictionary to store the extracted metric
            key: Key for storing the metric in the data dictionary
            selector: CSS selector for the metric element
            convert_to_float: Whether to convert the metric to a float (for currency values)
        """
        try:
            element = soup.select_one(selector)
            if element:
                value = element.get_text(strip=True)
                
                if convert_to_float:
                    # Convert currency value to float
                    value = self._convert_currency_to_float(value)
                    data[key] = value
                else:
                    # Try to convert to int first (for counts)
                    try:
                        data[key] = int(value.replace(',', ''))
                    except ValueError:
                        # If not an integer, store as is
                        data[key] = value
                        
                logger.debug(f"Extracted {key}: {data[key]}")
            else:
                logger.warning(f"No element found for {key} using selector: {selector}")
                
        except Exception as e:
            logger.warning(f"Error extracting {key}: {e}")
    
    def _convert_currency_to_float(self, currency_string: str) -> float:
        """
        Convert a currency string to a float.
        
        Args:
            currency_string: String representing a currency value (e.g., "$1,234.56")
            
        Returns:
            float: The numeric value of the currency
        """
        try:
            # Remove currency symbols, commas, and whitespace
            cleaned = re.sub(r'[^\d.]', '', currency_string)
            return float(cleaned)
        except ValueError:
            logger.warning(f"Failed to convert currency string to float: {currency_string}")
            return 0.0
    
    def _calculate_derived_metrics(self, data: Dict[str, Any]) -> None:
        """
        Calculate derived financial metrics.
        
        Args:
            data: Dictionary of financial metrics
        """
        try:
            # Calculate average revenue per user
            if data["paid_users"] > 0:
                data["avg_revenue_per_user"] = round(data["total_gmv"] / data["paid_users"], 2)
            
            # Calculate conversion rate (paid users / total users)
            if data["total_users"] > 0:
                data["conversion_rate"] = round((data["paid_users"] / data["total_users"]) * 100, 2)
                
            logger.debug("Calculated derived metrics")
            
        except Exception as e:
            logger.warning(f"Error calculating derived metrics: {e}")
    
    def _process_financial_data(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and clean the extracted financial data.
        
        Args:
            financial_data: Raw extracted financial data
            
        Returns:
            Dict[str, Any]: Processed financial data
        """
        logger.debug("Processing financial data")
        processed_data = financial_data.copy()
        
        # Add processing timestamp
        processed_data["processed_at"] = datetime.now().isoformat()
        
        # Ensure all numeric fields are of the right type
        try:
            numeric_fields = ["total_users", "paid_users", "total_gmv", "total_profit", 
                             "avg_revenue_per_user", "conversion_rate"]
            
            for field in numeric_fields:
                if field in processed_data:
                    if field in ["total_users", "paid_users"]:
                        # Ensure these are integers
                        processed_data[field] = int(processed_data[field])
                    else:
                        # Ensure these are floats
                        processed_data[field] = float(processed_data[field])
                        
                        # Round to 2 decimal places for currency values
                        processed_data[field] = round(processed_data[field], 2)
                        
            logger.debug("Financial data processed successfully")
            
        except Exception as e:
            logger.warning(f"Error during financial data processing: {e}")
            
        return processed_data

