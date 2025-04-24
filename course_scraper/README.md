# Course Platform Scraper

A comprehensive web scraping solution designed to extract, process, and store data from online course platforms, with specific support for "harkirat.classx.co.in".

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Features

- **Flexible Scraping Methods**: Supports both Selenium (for dynamic content) and Requests-based scraping
- **User Data Extraction**: Retrieves comprehensive user information including names, emails, join dates, and payment status
- **Financial Data Analysis**: Extracts financial metrics, payment history, and revenue data
- **Robust Authentication**: Securely handles login and session management with cookie persistence
- **Rate Limiting**: Configurable delays and randomization to avoid detection
- **Error Handling**: Comprehensive error capture with screenshots and logging
- **Data Export**: Exports data in both CSV and JSON formats
- **Proxy Support**: Optional proxy usage for avoiding IP blocks
- **User-Agent Rotation**: Randomizes browser identification to avoid detection
- **Configurable Settings**: Extensive configuration options for all aspects of the scraper

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/course_scraper.git
   cd course_scraper
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   
   # On Windows
   .venv\Scripts\activate
   
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

Run the scraper with default settings:

```bash
python course_scraper/main.py
```

You will be prompted to enter your username and password for the course platform.

### Command-Line Arguments

#### Authentication Options

```bash
# Provide credentials directly
python course_scraper/main.py -u your_email@example.com -p your_password

# Use previously stored cookies (if available)
python course_scraper/main.py --use-stored-cookies
```

#### Scraping Options

```bash
# Scrape user data only
python course_scraper/main.py --user-data

# Scrape financial data only
python course_scraper/main.py --financial-data

# Scrape all available data
python course_scraper/main.py --all-data

# Use Selenium for handling dynamic content
python course_scraper/main.py --use-selenium
```

#### Output Options

```bash
# Save data as JSON only
python course_scraper/main.py --format json

# Save data as CSV only
python course_scraper/main.py --format csv

# Specify custom output directory
python course_scraper/main.py --output-dir /path/to/output/directory

# Add a prefix to output filenames
python course_scraper/main.py --prefix my_project_
```

#### Rate Limiting Options

```bash
# Set specific delay between requests
python course_scraper/main.py --delay 5

# Use random delays between requests
python course_scraper/main.py --random-delay --min-delay 2 --max-delay 8
```

#### Logging Options

```bash
# Increase verbosity (info level)
python course_scraper/main.py -v

# Increase verbosity further (debug level)
python course_scraper/main.py -vv

# Specify custom log file path
python course_scraper/main.py --log-file /path/to/logfile.log

# Disable console logging (log to file only)
python course_scraper/main.py --no-console-log
```

#### Advanced Options

```bash
# Use a proxy
python course_scraper/main.py --proxy http://user:pass@proxyserver:port

# Use a custom user agent
python course_scraper/main.py --user-agent "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

# Modify retry settings
python course_scraper/main.py --retries 5 --timeout 60
```

## Configuration

The scraper's behavior can be configured through the settings module at `course_scraper/course_scraper/config/settings.py`. Key configuration options include:

### URL Configuration

- `BASE_URL`: Base URL of the course platform
- `LOGIN_URL`: URL for the login page
- `COURSE_URL`: URL for the course data
- `DASHBOARD_URL`: URL for the dashboard page

### Request Settings

- `REQUEST_TIMEOUT`: Timeout for HTTP requests in seconds
- `REQUEST_DELAY`: Default delay between requests
- `MAX_RETRIES`: Number of retry attempts for failed requests

### Rate Limiting

- `RATE_LIMIT_ENABLED`: Enable/disable rate limiting
- `RANDOMIZE_DELAY`: Use random delays between requests
- `MIN_REQUEST_DELAY`/`MAX_REQUEST_DELAY`: Range for random delays

### Selenium Settings

- `HEADLESS`: Run browser in headless mode
- `SELENIUM_TIMEOUT`: Timeout for Selenium operations
- `SELENIUM_WINDOW_SIZE`: Browser window size

### Output Settings

- `DATA_DIR`: Base directory for all data
- `PROCESSED_DATA_DIR`: Directory for processed output files
- `RAW_DATA_DIR`: Directory for raw data
- `CSV_DELIMITER`: Delimiter for CSV output
- `JSON_INDENT`: Indentation for JSON output

### Authentication Settings

- `STORE_COOKIES`: Enable/disable cookie storage
- `COOKIES_EXPIRY_DAYS`: Days until stored cookies expire
- `AUTO_RELOGIN`: Attempt relogin if session expires

## Project Structure

```
course_scraper/
├── .venv/                    # Virtual environment
├── course_scraper/           # Main package
│   ├── course_scraper/
│   │   ├── config/           # Configuration
│   │   │   └── settings.py   # Settings module
│   │   ├── data/             # Data storage
│   │   │   ├── processed/    # Processed output
│   │   │   └── raw/          # Raw data (HTML)
│   │   ├── logs/             # Log files
│   │   ├── src/              # Source code
│   │   │   ├── auth/         # Authentication
│   │   │   │   ├── __init__.py
│   │   │   │   └── authenticator.py
│   │   │   ├── models/       # Data models
│   │   │   │   ├── __init__.py
│   │   │   │   └── data_models.py
│   │   │   └── scrapers/     # Scrapers
│   │   │       ├── __init__.py
│   │   │       ├── financial_scraper.py
│   │   │       └── user_scraper.py
│   │   └── utils/            # Utilities
│   │       ├── data_storage.py
│   │       └── logger.py
│   ├── main.py               # Main entry point
│   └── requirements.txt      # Dependencies
└── README.md                 # This file
```

## Requirements

- Python 3.8+
- requests
- beautifulsoup4
- selenium
- lxml
- webdriver-manager (for Selenium driver management)

See `requirements.txt` for complete dependencies.

## Error Handling and Troubleshooting

### Common Issues

#### Authentication Failures

- Verify your username and password
- Check if the login page structure has changed
- Try using Selenium if the site has enhanced security measures

```bash
# Force use of Selenium for authentication
python course_scraper/main.py --use-selenium
```

#### Rate Limiting / IP Blocking

- Increase delay between requests
- Use random delays
- Consider using a proxy

```bash
# Use longer random delays
python course_scraper/main.py --random-delay --min-delay 5 --max-delay 15

# Use a proxy
python course_scraper/main.py --proxy http://your-proxy-url
```

#### Selenium WebDriver Issues

- Ensure you have the correct browser driver installed
- Try updating your browser
- Check the Selenium driver logs

#### Data Parsing Errors

- The site structure may have changed
- Check the raw HTML files saved in the `data/raw/html` directory
- Adjust the CSS selectors in the settings file

### Debugging

For detailed debugging information, run the scraper with increased verbosity:

```bash
python course_scraper/main.py -vv
```

Check the log files in the `logs` directory for detailed error messages.

## Contributing

Contributions are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request

Please ensure your code follows the existing style and includes appropriate tests.

### Development Setup

1. Set up the development environment:
   ```bash
   git clone https://github.com/yourusername/course_scraper.git
   cd course_scraper
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Additional dev dependencies
   ```

2. Run tests:
   ```bash
   pytest
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- The scraper was designed specifically for educational purposes
- Special thanks to the open-source community for the excellent tools and libraries that made this project possible

