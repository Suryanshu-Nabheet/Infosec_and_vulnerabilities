#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Course Platform Scraper - Main Entry Point

This script is the main entry point for the course platform scraper.
It handles command-line arguments, authentication, scraping, and data export.
"""

import os
import sys
import time
import logging
import argparse
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'course_scraper', 'course_scraper'))

# Import our modules
from config import settings
from src.auth.authenticator import Authenticator
from src.scrapers.user_scraper import UserScraper, UserScrapingError
from src.scrapers.financial_scraper import FinancialScraper, FinancialScrapingError
from utils.logger import setup_logger


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description='Course Platform Scraper',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Authentication options
    auth_group = parser.add_argument_group('Authentication')
    auth_group.add_argument('-u', '--username', help='Username/email for login')
    auth_group.add_argument('-p', '--password', help='Password for login')
    auth_group.add_argument('--use-stored-cookies', action='store_true', 
                            help='Use stored cookies for authentication')
    
    # Scraping options
    scrape_group = parser.add_argument_group('Scraping Options')
    scrape_group.add_argument('--use-selenium', action='store_true',
                             help='Use Selenium for scraping (for dynamic content)')
    scrape_group.add_argument('--user-data', action='store_true',
                             help='Scrape user data')
    scrape_group.add_argument('--financial-data', action='store_true',
                             help='Scrape financial data')
    scrape_group.add_argument('--all-data', action='store_true',
                             help='Scrape all available data')
    
    # Rate limiting options
    rate_group = parser.add_argument_group('Rate Limiting')
    rate_group.add_argument('--delay', type=float, default=settings.REQUEST_DELAY,
                           help='Delay between requests in seconds')
    rate_group.add_argument('--random-delay', action='store_true', default=settings.RANDOMIZE_DELAY,
                           help='Randomize delay between requests')
    rate_group.add_argument('--min-delay', type=float, default=settings.MIN_REQUEST_DELAY,
                           help='Minimum delay between requests in seconds (when using random delay)')
    rate_group.add_argument('--max-delay', type=float, default=settings.MAX_REQUEST_DELAY,
                           help='Maximum delay between requests in seconds (when using random delay)')
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('--format', choices=['json', 'csv', 'both'], default='both',
                             help='Output format for scraped data')
    output_group.add_argument('--output-dir', default=settings.PROCESSED_DATA_DIR,
                             help='Directory to save output files')
    output_group.add_argument('--prefix', default='',
                             help='Prefix for output filenames')
    
    # Logging options
    logging_group = parser.add_argument_group('Logging Options')
    logging_group.add_argument('-v', '--verbose', action='count', default=0,
                              help='Increase verbosity (can be used multiple times)')
    logging_group.add_argument('--log-file', default=settings.LOG_FILE,
                              help='Log file path')
    logging_group.add_argument('--no-console-log', action='store_true',
                              help='Disable logging to console')
    
    # Advanced options
    advanced_group = parser.add_argument_group('Advanced Options')
    advanced_group.add_argument('--proxy', help='Proxy URL (e.g., http://user:pass@host:port)')
    advanced_group.add_argument('--user-agent', help='Custom user agent string')
    advanced_group.add_argument('--retries', type=int, default=settings.MAX_RETRIES,
                               help='Maximum number of retry attempts for failed requests')
    advanced_group.add_argument('--timeout', type=int, default=settings.REQUEST_TIMEOUT,
                               help='Request timeout in seconds')
    
    return parser.parse_args()


def configure_settings(args: argparse.Namespace) -> None:
    """
    Update settings based on command-line arguments.
    
    Args:
        args: Parsed command-line arguments
    """
    # Update rate limiting settings
    settings.REQUEST_DELAY = args.delay
    settings.RANDOMIZE_DELAY = args.random_delay
    settings.MIN_REQUEST_DELAY = args.min_delay
    settings.MAX_REQUEST_DELAY = args.max_delay
    
    # Update request settings
    settings.MAX_RETRIES = args.retries
    settings.REQUEST_TIMEOUT = args.timeout
    
    # Update output settings
    if args.output_dir:
        settings.PROCESSED_DATA_DIR = args.output_dir
        os.makedirs(settings.PROCESSED_DATA_DIR, exist_ok=True)


def setup_logging(args: argparse.Namespace) -> logging.Logger:
    """
    Set up logging based on verbosity level.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        logging.Logger: Configured logger
    """
    # Map verbosity count to logging level
    verbosity_map = {
        0: logging.WARNING,  # Default
        1: logging.INFO,     # -v
        2: logging.DEBUG     # -vv
    }
    
    # Get the appropriate log level (cap at highest level of verbosity)
    console_log_level = verbosity_map.get(min(args.verbose, 2), logging.DEBUG)
    
    # Set up logger
    logger = setup_logger(
        console_level=console_log_level,
        file_level=logging.DEBUG,
        log_file=args.log_file,
        console_enabled=not args.no_console_log,
        file_enabled=True
    )
    
    return logger


def get_credentials(args: argparse.Namespace) -> Tuple[str, str]:
    """
    Get authentication credentials from arguments or prompt the user.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Tuple[str, str]: Username and password
    """
    username = args.username
    password = args.password
    
    # Prompt for username if not provided
    if not username:
        username = input("Enter your username/email: ")
    
    # Prompt for password if not provided
    if not password:
        import getpass
        password = getpass.getpass("Enter your password: ")
    
    return username, password


def authenticate(args: argparse.Namespace, logger: logging.Logger) -> Authenticator:
    """
    Authenticate with the course platform.
    
    Args:
        args: Parsed command-line arguments
        logger: Logger instance
        
    Returns:
        Authenticator: Authenticated authenticator instance
        
    Raises:
        Exception: If authentication fails
    """
    logger.info("Starting authentication process")
    
    # Initialize the authenticator
    authenticator = Authenticator(use_selenium=args.use_selenium)
    
    # Try to use stored cookies if requested
    if args.use_stored_cookies and os.path.exists(settings.COOKIES_FILE):
        logger.info("Attempting to use stored cookies")
        try:
            authenticator.load_cookies(settings.COOKIES_FILE)
            if authenticator.validate_session():
                logger.info("Successfully authenticated using stored cookies")
                return authenticator
            else:
                logger.warning("Stored cookies are invalid or expired")
        except Exception as e:
            logger.warning(f"Error using stored cookies: {e}")
    
    # Get credentials and authenticate
    username, password = get_credentials(args)
    
    logger.info(f"Authenticating as user: {username}")
    try:
        authenticator.login(username, password)
        logger.info("Authentication successful")
        
        # Save cookies for future use if enabled
        if settings.STORE_COOKIES:
            authenticator.save_cookies(settings.COOKIES_FILE)
            logger.info(f"Saved authentication cookies to {settings.COOKIES_FILE}")
        
        return authenticator
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise


def scrape_user_data(authenticator: Authenticator, args: argparse.Namespace, 
                    logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Scrape user data from the course platform.
    
    Args:
        authenticator: Authenticated authenticator instance
        args: Parsed command-line arguments
        logger: Logger instance
        
    Returns:
        List[Dict[str, Any]]: List of user data dictionaries
    """
    logger.info("Starting user data scraping")
    
    try:
        # Initialize the user scraper
        user_scraper = UserScraper(authenticator)
        
        # Perform the scraping
        start_time = time.time()
        user_data = user_scraper.scrape(use_selenium=args.use_selenium)
        elapsed_time = time.time() - start_time
        
        logger.info(f"User data scraping completed in {elapsed_time:.2f} seconds")
        logger.info(f"Scraped data for {len(user_data)} users")
        
        # Save the data based on the requested format
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_prefix = args.prefix + "users_" if args.prefix else "users_"
        
        if args.format in ['json', 'both']:
            json_filename = f"{filename_prefix}{timestamp}.json"
            json_path = user_scraper.save_to_json(user_data, json_filename)
            logger.info(f"Saved user data to JSON: {json_path}")
        
        if args.format in ['csv', 'both']:
            csv_filename = f"{filename_prefix}{timestamp}.csv"
            csv_path = user_scraper.save_to_csv(user_data, csv_filename)
            logger.info(f"Saved user data to CSV: {csv_path}")
        
        return user_data
        
    except UserScrapingError as e:
        logger.error(f"User scraping error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during user scraping: {e}")
        raise


def scrape_financial_data(authenticator: Authenticator, args: argparse.Namespace, 
                         logger: logging.Logger) -> Dict[str, Any]:
    """
    Scrape financial data from the course platform.
    
    Args:
        authenticator: Authenticated authenticator instance
        args: Parsed command-line arguments
        logger: Logger instance
        
    Returns:
        Dict[str, Any]: Financial data dictionary
    """
    logger.info("Starting financial data scraping")
    
    try:
        # Initialize the financial scraper
        financial_scraper = FinancialScraper(authenticator)
        
        # Perform the scraping
        start_time = time.time()
        financial_data = financial_scraper.scrape(use_selenium=args.use_selenium)
        elapsed_time = time.time() - start_time
        
        logger.info(f"Financial data scraping completed in {elapsed_time:.2f} seconds")
        
        # Save the data based on the requested format
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_prefix = args.prefix + "financial_" if args.prefix else "financial_"
        
        if args.format in ['json', 'both']:
            json_filename = f"{filename_prefix}{timestamp}.json"
            json_path = os.path.join(settings.PROCESSED_DATA_DIR, json_filename)
            
            with open(json_path, 'w', encoding=settings.EXPORT_ENCODING) as f:
                json.dump(financial_data, f, indent=settings.JSON_INDENT)
                
            logger.info(f"Saved financial data to JSON: {json_path}")
        
        # For CSV, we might need special handling since financial data might be hierarchical
        if args.format in ['csv', 'both']:
            csv_filename = f"{filename_prefix}{timestamp}.csv"
            csv_path = os.path.join(settings.PROCESSED_DATA_DIR, csv_filename)
            
            # Flatten the financial data for CSV if needed
            import csv
            try:
                flattened_data = financial_scraper.flatten_data(financial_data)
                
                with open(csv_path, 'w', newline='', encoding=settings.EXPORT_ENCODING) as f:
                    writer = csv.DictWriter(
                        f, 
                        fieldnames=flattened_data.keys(),
                        delimiter=settings.CSV_DELIMITER,
                        quotechar=settings.CSV_QUOTECHAR,
                        quoting=settings.CSV_QUOTING
                    )
                    writer.writeheader()
                    writer.writerow(flattened_data)
                
                logger.info(f"Saved financial data to CSV: {csv_path}")
            except Exception as e:
                logger.warning(f"Could not save financial data to CSV: {e}")
        
        return financial_data
        
    except FinancialScrapingError as e:
        logger.error(f"Financial scraping error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during financial scraping: {e}")
        raise


def main() -> int:
    """
    Main entry point for the course platform scraper.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Parse command-line arguments
    args = parse_arguments()
    
    # Configure settings based on arguments
    configure_settings(args)
    
    # Set up logging
    logger = setup_logging(args)
    
    logger.info("=" * 80)
    logger.info("Course Platform Scraper - Starting")
    logger.info("=" * 80)
    
    try:
        # Authenticate
        authenticator = authenticate(args, logger)
        
        # Determine what to scrape
        scrape_users = args.user_data or args.all_data
        scrape_financials = args.financial_data or args.all_data
        
        # If nothing specified, scrape users by default
        if not (scrape_users or scrape_financials):
            scrape_users = True
        
        # Perform the scraping
        results = {}
        
        if scrape_users:
            logger.info("User data scraping selected")
            results['users'] = scrape_user_data(authenticator, args, logger)
        
        if scrape_financials:
            logger.info("Financial data scraping selected")
            results['financials'] = scrape_financial_data(authenticator, args, logger)
        
        # Final summary
        logger.info("=" * 80)
        logger.info("Scraping completed successfully")
        
        # Print summary of scraped data
        if scrape_users and 'users' in results:
            logger.info(f"Scraped {len(results['users'])} user records")
            
        if scrape_financials and 'financials' in results:
            financial_summary = []
            for key, value in results['financials'].items():
                if isinstance(value, (int, float, str, bool)):
                    financial_summary.append(f"{key}: {value}")
            if financial_summary:
                logger.info("Financial data summary:")
                for item in financial_summary:
                    logger.info(f"  {item}")
        
        logger.info("=" * 80)
        
        # Cleanup
        if hasattr(authenticator, 'driver') and authenticator.driver:
            logger.info("Closing Selenium WebDriver")
            try:
                authenticator.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")
        
        return 0  # Success
        
    except KeyboardInterrupt:
        logger.warning("Scraping interrupted by user")
        return 130  # Standard Unix code for SIGINT
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        
        # Attempt to take a screenshot if possible on error
        if settings.TAKE_SCREENSHOT_ON_ERROR and hasattr(authenticator, 'driver') and authenticator.driver:
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                screenshot_path = os.path.join(settings.ERROR_SCREENSHOTS_DIR, f"error_{timestamp}.png")
                authenticator.driver.save_screenshot(screenshot_path)
                logger.info(f"Error screenshot saved to {screenshot_path}")
            except Exception as screenshot_e:
                logger.warning(f"Failed to save error screenshot: {screenshot_e}")
        
        # Cleanup on error
        if 'authenticator' in locals() and hasattr(authenticator, 'driver') and authenticator.driver:
            logger.info("Closing Selenium WebDriver after error")
            try:
                authenticator.driver.quit()
            except Exception as driver_e:
                logger.warning(f"Error closing WebDriver: {driver_e}")
        
        return 1  # Error


def display_progress(message: str, progress: float, width: int = 50) -> None:
    """
    Display a progress bar in the console.
    
    Args:
        message: Message to display before the progress bar
        progress: Progress value between 0 and 1
        width: Width of the progress bar in characters
    """
    progress = max(0, min(1, progress))  # Ensure progress is between 0 and 1
    filled_width = int(width * progress)
    bar = '█' * filled_width + '░' * (width - filled_width)
    percent = int(progress * 100)
    print(f"\r{message}: |{bar}| {percent}%", end='', flush=True)
    if progress >= 1:
        print()  # Print a newline when complete


def check_dependencies() -> bool:
    """
    Check if all required dependencies are installed.
    
    Returns:
        bool: True if all dependencies are met, False otherwise
    """
    required_packages = [
        'requests',
        'beautifulsoup4',
        'selenium',
        'lxml',  # For better HTML parsing performance
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Error: Missing required dependencies:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nPlease install them using:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True


if __name__ == "__main__":
    # Check dependencies before running
    if not check_dependencies():
        sys.exit(1)
    
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
