#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Course Platform Scraper

This module contains tests for the various components of the course scraper:
- Authentication
- User scraping
- Financial scraping
- Error handling
"""

import os
import sys
import json
import pytest
import tempfile
import datetime
from unittest import mock
from typing import Dict, List, Any

# Add the project root to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'course_scraper', 'course_scraper'))

# Import modules to test
from config import settings
from src.auth.authenticator import Authenticator
from src.scrapers.user_scraper import UserScraper, UserScrapingError
from src.scrapers.financial_scraper import FinancialScraper, FinancialScrapingError


# Sample HTML responses for mocking
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
    <form action="/login" method="post">
        <input type="email" name="email" id="email" placeholder="Email">
        <input type="password" name="password" id="password" placeholder="Password">
        <button type="submit">Login</button>
    </form>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head><title>Dashboard</title></head>
<body>
    <h1>Welcome to your Dashboard</h1>
    <div class="user-info">
        <span class="username">Test User</span>
        <span class="email">test@example.com</span>
    </div>
</body>
</html>
"""

USER_LIST_HTML = """
<!DOCTYPE html>
<html>
<head><title>User List</title></head>
<body>
    <h1>Users</h1>
    <div class="user-list">
        <div class="user-item">
            <div class="user-name">John Doe</div>
            <div class="user-email">john@example.com</div>
            <div class="payment-status">Paid</div>
            <div class="join-date">2023-05-15</div>
        </div>
        <div class="user-item">
            <div class="user-name">Jane Smith</div>
            <div class="user-email">jane@example.com</div>
            <div class="payment-status">Pending</div>
            <div class="join-date">2023-06-20</div>
        </div>
    </div>
</body>
</html>
"""

FINANCIAL_DATA_HTML = """
<!DOCTYPE html>
<html>
<head><title>Financial Data</title></head>
<body>
    <h1>Financial Overview</h1>
    <div class="financial-metrics">
        <div class="total-users-value">500</div>
        <div class="paid-users-value">350</div>
        <div class="total-gmv-value">$50,000</div>
        <div class="total-profit-value">$35,000</div>
    </div>
</body>
</html>
"""


# Fixtures
@pytest.fixture
def mock_response():
    """Fixture for creating a mock HTTP response."""
    class MockResponse:
        def __init__(self, text, status_code=200, url=None, cookies=None):
            self.text = text
            self.content = text.encode('utf-8')
            self.status_code = status_code
            self.url = url or "https://harkirat.classx.co.in"
            self.cookies = cookies or {}
            
        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP Error: {self.status_code}")
            
        def json(self):
            return json.loads(self.text)
    
    return MockResponse


@pytest.fixture
def mock_requests(monkeypatch, mock_response):
    """Fixture to mock requests library."""
    def _mock_get(url, **kwargs):
        if 'login' in url:
            return mock_response(LOGIN_HTML)
        elif 'dashboard' in url:
            return mock_response(DASHBOARD_HTML)
        elif 'users' in url:
            return mock_response(USER_LIST_HTML)
        elif 'analytics' in url:
            return mock_response(FINANCIAL_DATA_HTML)
        else:
            return mock_response("", 404)
    
    def _mock_post(url, **kwargs):
        if 'login' in url:
            # Simulate successful login with cookies
            return mock_response(
                DASHBOARD_HTML, 
                cookies={'session': 'test_session_cookie'}
            )
        else:
            return mock_response("", 404)
    
    monkeypatch.setattr('requests.get', _mock_get)
    monkeypatch.setattr('requests.post', _mock_post)
    monkeypatch.setattr('requests.Session.get', _mock_get)
    monkeypatch.setattr('requests.Session.post', _mock_post)


@pytest.fixture
def temp_dir():
    """Fixture to create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Update settings to use the temporary directory
        original_data_dir = settings.DATA_DIR
        original_logs_dir = settings.LOGS_DIR
        original_raw_data_dir = settings.RAW_DATA_DIR
        original_processed_data_dir = settings.PROCESSED_DATA_DIR
        
        settings.DATA_DIR = os.path.join(tmpdirname, 'data')
        settings.LOGS_DIR = os.path.join(tmpdirname, 'logs')
        settings.RAW_DATA_DIR = os.path.join(tmpdirname, 'data', 'raw')
        settings.PROCESSED_DATA_DIR = os.path.join(tmpdirname, 'data', 'processed')
        settings.RAW_HTML_DIR = os.path.join(tmpdirname, 'data', 'raw', 'html')
        
        # Create directories
        os.makedirs(settings.RAW_HTML_DIR, exist_ok=True)
        os.makedirs(settings.PROCESSED_DATA_DIR, exist_ok=True)
        os.makedirs(settings.LOGS_DIR, exist_ok=True)
        
        yield tmpdirname
        
        # Restore original settings
        settings.DATA_DIR = original_data_dir
        settings.LOGS_DIR = original_logs_dir
        settings.RAW_DATA_DIR = original_raw_data_dir
        settings.PROCESSED_DATA_DIR = original_processed_data_dir


@pytest.fixture
def mock_selenium(monkeypatch):
    """Fixture to mock Selenium WebDriver."""
    # Create mock driver
    mock_driver = mock.MagicMock()
    mock_driver.get.return_value = None
    mock_driver.page_source = USER_LIST_HTML
    mock_driver.current_url = "https://harkirat.classx.co.in/dashboard"
    
    # Mock find_element
    mock_element = mock.MagicMock()
    mock_element.send_keys.return_value = None
    mock_element.click.return_value = None
    mock_element.text = "Test User"
    mock_element.is_displayed.return_value = True
    mock_element.is_enabled.return_value = True
    
    mock_driver.find_element.return_value = mock_element
    
    # Patch WebDriver
    monkeypatch.setattr('selenium.webdriver.Chrome', lambda **kwargs: mock_driver)
    monkeypatch.setattr('selenium.webdriver.Firefox', lambda **kwargs: mock_driver)
    
    return mock_driver


@pytest.fixture
def mock_authenticator(mock_requests):
    """Fixture to provide a pre-authenticated authenticator."""
    authenticator = Authenticator(use_selenium=False)
    authenticator.session.cookies.update({'session': 'test_session_cookie'})
    authenticator.authenticated = True
    return authenticator


# Tests for Authentication
class TestAuthentication:
    """Tests for the authentication mechanism."""
    
    def test_init_authenticator(self):
        """Test initializing the authenticator."""
        authenticator = Authenticator(use_selenium=False)
        assert authenticator is not None
        assert authenticator.authenticated is False
        assert authenticator.session is not None
    
    def test_login_with_requests(self, mock_requests):
        """Test login using requests."""
        authenticator = Authenticator(use_selenium=False)
        authenticator.login("test@example.com", "password")
        
        assert authenticator.authenticated is True
        assert 'session' in authenticator.session.cookies
    
    def test_login_with_selenium(self, mock_selenium):
        """Test login using Selenium."""
        authenticator = Authenticator(use_selenium=True)
        authenticator.login("test@example.com", "password")
        
        assert authenticator.authenticated is True
        assert authenticator.driver is not None
        assert authenticator.driver.get.called
    
    def test_validate_session(self, mock_authenticator, mock_requests):
        """Test validating an existing session."""
        assert mock_authenticator.validate_session() is True
    
    def test_invalid_session(self, mock_requests):
        """Test handling an invalid session."""
        authenticator = Authenticator(use_selenium=False)
        assert authenticator.validate_session() is False
    
    def test_save_and_load_cookies(self, mock_authenticator, temp_dir):
        """Test saving and loading cookies."""
        cookies_file = os.path.join(temp_dir, 'cookies.json')
        
        # Save cookies
        mock_authenticator.save_cookies(cookies_file)
        assert os.path.exists(cookies_file)
        
        # Create a new authenticator and load cookies
        new_authenticator = Authenticator(use_selenium=False)
        new_authenticator.load_cookies(cookies_file)
        
        assert 'session' in new_authenticator.session.cookies
        assert new_authenticator.session.cookies['session'] == 'test_session_cookie'


# Tests for User Scraper
class TestUserScraper:
    """Tests for the user scraper."""
    
    def test_init_user_scraper(self, mock_authenticator):
        """Test initializing the user scraper."""
        user_scraper = UserScraper(mock_authenticator)
        assert user_scraper is not None
        assert user_scraper.authenticator is mock_authenticator
    
    def test_init_without_auth(self):
        """Test initializing without authentication."""
        authenticator = Authenticator(use_selenium=False)
        
        with pytest.raises(UserScrapingError):
            UserScraper(authenticator)
    
    def test_fetch_with_retry(self, mock_authenticator, mock_requests):
        """Test fetching with retry mechanism."""
        user_scraper = UserScraper(mock_authenticator)
        content = user_scraper._fetch_with_retry(settings.USER_URL)
        
        assert content is not None
        assert "Users" in content
    
    def test_parse_user_data(self, mock_authenticator, mock_requests):
        """Test parsing user data from HTML."""
        user_scraper = UserScraper(mock_authenticator)
        users, has_next = user_scraper._parse_user_data(USER_LIST_HTML, 1)
        
        assert len(users) == 2
        assert users[0]['name'] == 'John Doe'
        assert users[0]['email'] == 'john@example.com'
        assert users[0]['paid'] == True
    
    def test_process_user_data(self, mock_authenticator):
        """Test processing raw user data."""
        user_scraper = UserScraper(mock_authenticator)
        raw_data = [
            {
                'id': '123',
                'name': ' john doe ',
                'email': ' JOHN@example.com ',
                'paid': 'Yes',
                'join_date': '2023-05-15',
                'scrape_date': datetime.datetime.now().isoformat()
            },
            {
                'id': '456',
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'paid': 'No',
                'join_date': '06/20/2023',
                'scrape_date': datetime.datetime.now().isoformat()
            }
        ]
        
        processed_data = user_scraper._process_user_data(raw_data)
        
        assert len(processed_data) == 2
        assert processed_data[0]['name'] == 'John Doe'
        assert processed_data[0]['email'] == 'john@example.com'
        assert processed_data[0]['paid'] is True
        assert processed_data[0]['email_valid'] is True
    
    def test_save_to_csv(self, mock_authenticator, temp_dir):
        """Test saving data to CSV."""
        user_scraper = UserScraper(mock_authenticator)
        test_data = [
            {'id': '123', 'name': 'John Doe', 'email': 'john@example.com'},
            {'id': '456', 'name': 'Jane Smith', 'email': 'jane@example.com'}
        ]
        
        csv_path = user_scraper.save_to_csv(test_data, 'test_users.csv')
        
        assert os.path.exists(csv_path)
        
        # Read the CSV and verify content
        import csv
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            
            assert len(rows) == 2
            assert rows[0]['name'] == 'John Doe'
            assert rows[1]['email'] == 'jane@example.com'
    
    def test_save_to_json(self, mock_authenticator, temp_dir):
        """Test saving data to JSON."""
        user_scraper = UserScraper(mock_authenticator)
        test_data = [
            {'id': '123', 'name': 'John Doe', 'email': 'john@example.com'},
            {'id': '456', 'name': 'Jane Smith', 'email': 'jane@example.com'}
        ]
        
        json_path = user_scraper.save_to_json(test_data, 'test_users.json')
        
        assert os.path.exists(json_path)
        
        # Read the JSON and verify content
        with open(json_path, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
            
            assert len(data) == 2
            assert data[0]['name'] == 'John Doe'
            assert data[1]['email'] == 'jane@example.com'
    
    def test_scrape_with_requests(self, mock_authenticator, mock_requests):
        """Test scraping user data with requests."""
        user_scraper = UserScraper(mock_authenticator)
        
        # Patch the _save_raw_html method to avoid file operations
        with mock.patch.object(user_scraper, '_save_raw_html'):
            user_data = user_scraper.scrape(use_selenium=False)
            
            assert user_data is not None
            assert len(user_data) > 0
            assert 'name' in user_data[0]
            assert 'email' in user_data[0]
    
    def test_scrape_with_selenium(self, mock_authenticator, mock_selenium):
        """Test scraping user data with Selenium."""
        user_scraper = UserScraper(mock_authenticator)
        user_scraper.driver = mock_selenium
        
        # Patch the _save_raw_html method to avoid file operations
        with mock.patch.object(user_scraper, '_save_raw_html'):
            user_data = user_scraper.scrape(use_selenium=True)
            
            assert user_data is not None
            assert len(user_data) > 0
            assert 'name' in user_data[0]
            assert 'email' in user_data[0]
    
    def test_scraping_error_handling(self, mock_authenticator, mock_requests):
        """Test error handling during scraping."""
        user_scraper = UserScraper(mock_authenticator)
        
        # Patch _fetch_with_retry to raise an exception
        with mock.patch.object(user_scraper, '_fetch_with_retry', side_effect=Exception("Test error")):
            with pytest.raises(UserScrapingError):
                user_scraper.scrape(use_selenium=False)
    
    def test_validate_user_record(self, mock_authenticator):
        """Test user record validation."""
        user_scraper = UserScraper(mock_authenticator)
        
        # Valid record with all required fields
        valid_record = {
            'id': '123',
            'name': 'John Doe',
            'email': 'john@example.com',
            'scrape_date': datetime.datetime.now().isoformat()
        }
        
        # Invalid record missing required fields
        invalid_record_1 = {
            'name': 'John Doe',
            'email': 'john@example.com'
            # Missing 'id' and 'scrape_date'
        }
        
        # Invalid record missing identifying fields
        invalid_record_2 = {
            'id': '123',
            'scrape_date': datetime.datetime.now().isoformat()
            # Missing 'name' and 'email'
        }
        
        assert user_scraper._validate_user_record(valid_record) is True
        assert user_scraper._validate_user_record(invalid_record_1) is False
        assert user_scraper._validate_user_record(invalid_record_2) is False


# Tests for Financial Scraper
class TestFinancialScraper:
    """Tests for the financial scraper."""
    
    def test_init_financial_scraper(self, mock_authenticator):
        """Test initializing the financial scraper."""
        financial_scraper = FinancialScraper(mock_authenticator)
        assert financial_scraper is not None
        assert financial_scraper.authenticator is mock_authenticator
    
    def test_init_without_auth(self):
        """Test initializing without authentication."""
        authenticator = Authenticator(use_selenium=False)
        
        with pytest.raises(FinancialScrapingError):
            FinancialScraper(authenticator)
    
    def test_scrape_with_requests(self, mock_authenticator, mock_requests):
        """Test scraping financial data with requests."""
        financial_scraper = FinancialScraper(mock_authenticator)
        
        # Patch the _save_raw_html method to avoid file operations
        with mock.patch.object(financial_scraper, '_save_raw_html', return_value=None):
            financial_data = financial_scraper.scrape(use_selenium=False)
            
            assert financial_data is not None
            assert isinstance(financial_data, dict)
            assert 'total_users' in financial_data
            assert 'paid_users' in financial_data
            assert 'total_revenue' in financial_data
    
    def test_scrape_with_selenium(self, mock_authenticator, mock_selenium):
        """Test scraping financial data with Selenium."""
        financial_scraper = FinancialScraper(mock_authenticator)
        financial_scraper.driver = mock_selenium
        
        # Patch the _save_raw_html method to avoid file operations
        with mock.patch.object(financial_scraper, '_save_raw_html', return_value=None):
            financial_data = financial_scraper.scrape(use_selenium=True)
            
            assert financial_data is not None
            assert isinstance(financial_data, dict)
            assert 'total_users' in financial_data
            assert 'paid_users' in financial_data
            assert 'total_revenue' in financial_data
    
    def test_extract_financial_metrics(self, mock_authenticator):
        """Test extracting financial metrics from HTML."""
        financial_scraper = FinancialScraper(mock_authenticator)
        metrics = financial_scraper._extract_financial_metrics(FINANCIAL_DATA_HTML)
        
        assert metrics is not None
        assert 'total_users' in metrics
        assert metrics['total_users'] == 500
        assert 'paid_users' in metrics
        assert metrics['paid_users'] == 350
        assert 'total_gmv' in metrics
        assert metrics['total_gmv'] == '$50,000'
        assert 'total_profit' in metrics
        assert metrics['total_profit'] == '$35,000'
    
    def test_clean_financial_data(self, mock_authenticator):
        """Test cleaning financial data."""
        financial_scraper = FinancialScraper(mock_authenticator)
        raw_data = {
            'total_users': '500',
            'paid_users': '350',
            'total_gmv': '$50,000',
            'total_profit': '$35,000'
        }
        
        cleaned_data = financial_scraper._clean_financial_data(raw_data)
        
        assert cleaned_data['total_users'] == 500
        assert cleaned_data['paid_users'] == 350
        assert cleaned_data['total_gmv'] == 50000
        assert cleaned_data['total_profit'] == 35000
    
    def test_flatten_data(self, mock_authenticator):
        """Test flattening hierarchical financial data."""
        financial_scraper = FinancialScraper(mock_authenticator)
        hierarchical_data = {
            'overview': {
                'total_users': 500,
                'paid_users': 350
            },
            'revenue': {
                'total': 50000,
                'breakdown': {
                    'course_1': 30000,
                    'course_2': 20000
                }
            }
        }
        
        flattened = financial_scraper.flatten_data(hierarchical_data)
        
        assert flattened['overview_total_users'] == 500
        assert flattened['overview_paid_users'] == 350
        assert flattened['revenue_total'] == 50000
        assert flattened['revenue_breakdown_course_1'] == 30000
        assert flattened['revenue_breakdown_course_2'] == 20000
    
    def test_scraping_error_handling(self, mock_authenticator, mock_requests):
        """Test error handling during scraping."""
        financial_scraper = FinancialScraper(mock_authenticator)
        
        # Patch _fetch_with_retry to raise an exception
        with mock.patch.object(financial_scraper, '_fetch_analytics_page', side_effect=Exception("Test error")):
            with pytest.raises(FinancialScrapingError):
                financial_scraper.scrape(use_selenium=False)


# Error handling tests
class TestErrorHandling:
    """Tests for error handling across the application."""
    
    def test_request_retry_mechanism(self, mock_authenticator):
        """Test the retry mechanism for failed requests."""
        user_scraper = UserScraper(mock_authenticator)
        
        # Mock session.get to fail twice then succeed
        mock_session = mock.MagicMock()
        mock_response_fail = mock.MagicMock()
        mock_response_fail.raise_for_status.side_effect = requests.exceptions.RequestException("Test error")
        
        mock_response_success = mock.MagicMock()
        mock_response_success.text = "Success"
        mock_response_success.raise_for_status.return_value = None
        
        mock_session.get.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success
        ]
        
        # Replace the session with our mock
        original_session = user_scraper.session
        user_scraper.session = mock_session
        
        try:
            # Set max_retries to 3 so our test will pass
            with mock.patch.object(settings, 'MAX_RETRIES', 3):
                # Also patch sleep to avoid waiting
                with mock.patch('time.sleep'):
                    result = user_scraper._fetch_with_retry("https://example.com")
                    
                    # Should have tried 3 times (2 fails + 1 success)
                    assert mock_session.get.call_count == 3
                    assert result == "Success"
        finally:
            # Restore the original session
            user_scraper.session = original_session
    
    def test_max_retries_exceeded(self, mock_authenticator):
        """Test behavior when max retries are exceeded."""
        user_scraper = UserScraper(mock_authenticator)
        
        # Mock session.get to always fail
        mock_session = mock.MagicMock()
        mock_response = mock.MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("Test error")
        mock_session.get.return_value = mock_response
        
        # Replace the session with our mock
        original_session = user_scraper.session
        user_scraper.session = mock_session
        
        try:
            # Set max_retries to 2 for faster testing
            with mock.patch.object(settings, 'MAX_RETRIES', 2):
                # Also patch sleep to avoid waiting
                with mock.patch('time.sleep'):
                    with pytest.raises(UserScrapingError):
                        user_scraper._fetch_with_retry("https://example.com")
                    
                    # Should have tried exactly MAX_RETRIES times
                    assert mock_session.get.call_count == 2
        finally:
            # Restore the original session
            user_scraper.session = original_session


# Integration tests
def test_full_scraping_workflow(mock_authenticator, mock_requests, temp_dir):
    """Test the full scraping workflow."""
    # Set up scrapers
    user_scraper = UserScraper(mock_authenticator)
    financial_scraper = FinancialScraper(mock_authenticator)
    
    # Patch save methods to avoid file operations
    with mock.patch.object(user_scraper, '_save_raw_html'):
        with mock.patch.object(financial_scraper, '_save_raw_html'):
            # Scrape data
            user_data = user_scraper.scrape(use_selenium=False)
            financial_data = financial_scraper.scrape(use_selenium=False)
            
            # Save to both formats
            user_csv = user_scraper.save_to_csv(user_data)
            user_json = user_scraper.save_to_json(user_data)
            
            # Verify files exist
            assert os.path.exists(user_csv)
            assert os.path.exists(user_json)
            
            # Verify data integrity
            assert len(user_data) > 0
            assert isinstance(financial_data, dict)
            assert 'total_users' in financial_data


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
