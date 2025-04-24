# Course Platform Scraper

A Python-based web scraper for extracting user and financial data from the Harkirat ClassX course platform.

## Overview

This tool scrapes data from the course selling website at https://harkirat.classx.co.in/new-courses/8-live-0-100-complete to extract information about:

- List of all paid users
- Total number of users
- Total GMV (Gross Merchandise Value)
- Total profit
- Additional user details available through the platform

## Project Structure

```
course_scraper/
│
├── config/
│   └── settings.py          # Configuration settings and constants
│
├── src/
│   ├── auth/                # Authentication related modules
│   │   ├── __init__.py
│   │   └── authenticator.py # Handles login and session management
│   │
│   ├── models/              # Data models
│   │   ├── __init__.py
│   │   └── data_models.py   # Defines User and FinancialMetrics models
│   │
│   └── scrapers/            # Scraper modules
│       ├── __init__.py
│       ├── user_scraper.py  # Extracts user data
│       └── financial_scraper.py # Extracts financial metrics
│
├── utils/
│   ├── logger.py            # Logging configuration
│   └── data_storage.py      # Functions for saving data
│
├── data/
│   ├── raw/                 # Raw HTML and other data
│   │   └── html/            # Stored HTML pages for debugging
│   └── processed/           # Processed CSV and JSON output
│
├── logs/                    # Log files
│
├── main.py                  # Main entry point
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

## Requirements

- Python 3.7+
- Required Python packages (see `requirements.txt`):
  - requests
  - beautifulsoup4
  - selenium
  - lxml
  - tqdm
  - python-dotenv
  - colorama
  - jsonschema
- Chrome/Chromium browser (if using Selenium)

## Installation

### Standard Installation

1. Clone this repository or download the source code:

```bash
git clone https://github.com/yourusername/course_scraper.git
cd course_scraper
```

2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

3. If you plan to use Selenium:
   - Ensure you have Chrome/Chromium installed
   - The script will automatically download the appropriate ChromeDriver version using webdriver-manager

### Installation with Virtual Environment (Recommended)

1. Clone the repository:

```bash
git clone https://github.com/yourusername/course_scraper.git
cd course_scraper
```

2. Create and activate a virtual environment:

```bash
# On macOS/Linux
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the script with your login credentials:

```bash
python main.py --email YOUR_EMAIL --password YOUR_PASSWORD
```

### Command Line Arguments

- `--email` (required): Email for authentication
- `--password` (required): Password for authentication
- `--use-selenium`: Use Selenium for handling JavaScript-heavy pages
- `--output-dir`: Custom directory for output files (default: './data/processed')
- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `--config-file`: Path to custom configuration file

### Examples

**Basic scraping with requests:**
```bash
python main.py --email admin@example.com --password mysecretpassword
```

**Using Selenium for dynamic content:**
```bash
python main.py --email admin@example.com --password mysecretpassword --use-selenium
```

**Custom output directory and verbose logging:**
```bash
python main.py --email admin@example.com --password mysecretpassword --output-dir ./my_data --log-level DEBUG
```

**Using environment variables for credentials:**

Create a `.env` file with:
```
EMAIL=admin@example.com
PASSWORD=mysecretpassword
```

Then run:
```bash
python main.py
```

## Output Files

The scraper generates the following files:

1. **User Data**: `data/processed/user_data.csv`
   - Contains information about each user (name, email, payment status, etc.)

2. **Financial Data**: `data/processed/financial_data.json`
   - Contains aggregated financial metrics (GMV, profit, total users, etc.)

3. **Raw HTML**: `data/raw/html/`
   - Contains raw HTML files saved during scraping for debugging

4. **Logs**: `logs/scraper.log`
   - Contains detailed logs of the scraping process

## Configuration

The scraper behavior can be customized by modifying the settings in `config/settings.py`:

### Key Settings

- **URLs**: Change target URLs if the platform structure changes
- **Selectors**: Update CSS selectors if the website's HTML structure changes
- **Request Settings**: Adjust timeouts, delays, and retry attempts
- **Selenium Settings**: Configure headless mode, window size, etc.
- **Output Paths**: Change file paths and formats

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify your credentials are correct
   - Check if the website login form has changed
   - Try using `--use-selenium` as it handles complex login forms better

2. **Element Not Found Errors**
   - The website may have changed its HTML structure
   - Update the CSS selectors in `config/settings.py`

3. **Selenium WebDriver Issues**
   - Ensure Chrome/Chromium is installed
   - Try updating your Chrome browser to match ChromeDriver version
   - Check if `--headless` mode is causing issues, you can disable it in settings

4. **Rate Limiting**
   - Increase `REQUEST_DELAY` in settings to avoid hitting rate limits
   - Use a VPN if the website is blocking your IP

### Debugging

For troubleshooting, enable DEBUG level logging:

```bash
python main.py --email YOUR_EMAIL --password YOUR_PASSWORD --log-level DEBUG
```

Check the generated files in `data/raw/html/` to see the HTML content that was parsed.

## Development

### Setting Up Development Environment

1. Follow the installation steps with virtual environment
2. Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

3. Set up pre-commit hooks:

```bash
pre-commit install
```

### Project Architecture

- **Modular Design**: Each component is designed to be modular and reusable
- **Separation of Concerns**: Authentication, scraping, data processing, and storage are separated
- **Type Hints**: All functions include type hints for better code quality
- **Documentation**: Comprehensive docstrings for all classes and functions

### Adding New Features

1. **New Data Type**: Add a new model in `src/models/data_models.py` and a corresponding scraper
2. **New Website**: Update selectors in `config/settings.py` and adjust scraping logic if needed
3. **New Export Format**: Add export functions in `utils/data_storage.py`

## Testing

Run the tests to ensure everything is working correctly:

```bash
pytest
```

To run specific test categories:

```bash
pytest tests/test_auth.py  # Test authentication only
pytest tests/test_scrapers.py  # Test scrapers only
```

To run tests with coverage report:

```bash
pytest --cov=src
```

## Ethical Considerations

This scraper is intended for authorized use only. Please ensure you have permission to access and extract data from the target platform. Respect rate limits and the website's terms of service.

Some ethical guidelines:

- Always respect robots.txt directives
- Implement proper rate limiting to avoid overloading the server
- Store only the data you need and handle it according to privacy laws
- Do not distribute scraped data without permission

## License

This project is for educational and authorized use only. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
