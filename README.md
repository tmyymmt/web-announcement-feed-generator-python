# Web Announcement Feed Generator

A CLI tool that scrapes announcement information from specified web pages, outputs RSS feed files, and generates CSV lists of items that match filter conditions.

## Features

- **Scrapes announcements from web pages without existing RSS feeds**
- **Only uses information available on the specified web pages**
- Extracts date, title, content, and category information from announcements
- Handles JavaScript-rendered content using Selenium
- Outputs RSS 2.0 formatted feed files and CSV lists
- Filters announcements by date, category inclusion/exclusion
- Supports multiple websites with specialized scrapers
- Differential mode to only process new items

## Requirements

- Ubuntu LTS (latest version)
- Python 3.x (latest LTS version)
- Required packages (automatically installed via requirements.txt):
  - requests
  - beautifulsoup4
  - selenium
  - webdriver-manager

## Installation

1. Clone the repository
2. Install required packages:

```sh
pip install -r requirements.txt
```

## Usage

```
python src/main.py [URL] [options]
```

### Arguments

- `URL`: Target webpage URL to scrape, or "all" to scrape all supported URLs

### Options

- `--since YYYY-MM-DD`: Only include items published on or after the specified date
- `--until YYYY-MM-DD`: Only include items published on or before the specified date
- `--category CATEGORY`: Only include items containing the specified category
- `--exclude-category CATEGORY`: Exclude items containing the specified category
- `--feed-output PATH`: Specify output path for the RSS feed file
- `--csv-output PATH`: Specify output path for the CSV file
- `--diff-mode`: Only output items newer than the latest item in the existing feed file
- `--with-date`: Add current date to output filenames (_YYYYMMDD format)
- `--debug`: Enable detailed debugging output

### Example Commands

```sh
# Scrape announcements from Firebase releases page
python src/main.py https://firebase.google.com/support/releases

# Scrape all supported websites
python src/main.py all --with-date

# Get only important announcements from Firebase
python src/main.py https://firebase.google.com/support/releases --category important

# Get all announcements except deprecated ones
python src/main.py https://firebase.google.com/support/releases --exclude-category deprecated

# Get announcements published after Jan 1, 2025
python src/main.py https://firebase.google.com/support/releases --since 2025-01-01

# Differential mode: only get new items since last run
python src/main.py https://firebase.google.com/support/releases --diff-mode
```

## Supported Websites

- Firebase Release Notes: https://firebase.google.com/support/releases
  - Extracts announcements with specific release-* class designations
  - Categorizes based on class names and content keywords
- Monaca Headline: https://ja.monaca.io/headline/
  - Handles Japanese language content
  - Extracts from headline-entry class elements

## Implementation Details

- URL-specific scraping logic is implemented in separate files to handle different site structures
  - Scrapers are stored in the `src/scrapers/` directory with filenames based on domain names and paths
  - Each target URL dynamically loads the appropriate scraping logic at runtime
  - Scraper filename convention:
    - Based on URL domain and path (e.g., firebase_google_com.py)
    - Converted to be compatible with all OS and URL formats (replacing dots with underscores, etc.)
  - Generic scraper is used for unsupported URLs
- Uses Selenium with Chrome in headless mode for JavaScript-rendered content
  - Uses chrome-aws-lambda-layer in AWS Lambda environments
- Uses the latest Chrome User-Agent for requests
- CSV date format is YYYY/MM/DD
- Default output filenames are based on the URL and optionally include the current date

## License

This project is licensed under the MIT-0 License - see the [LICENSE](LICENSE) file for details.