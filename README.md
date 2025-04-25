# Web Announcement Feed Generator Python

A CLI tool that scrapes announcement information from specified web pages and converts it into RSS 2.0 feed and CSV file formats.

## Features

- Supported websites:
  - Firebase Release Notes (`https://firebase.google.com/support/releases`)
  - Monaca News (`https://ja.monaca.io/headline/`)
- RSS 2.0 feed generation
- CSV export of announcements
- Date range filtering
- Category filtering
- Differential mode to extract only updates since the last feed

## Requirements

- Ubuntu LTS (latest version)
- Python 3.x (latest LTS version)
- Chrome browser (for Selenium)
- Required packages (automatically installed via requirements.txt):
  - requests
  - beautifulsoup4
  - selenium
  - webdriver-manager

## Installation

### Local Installation

This tool is not currently published to the npm registry. Please install it using the following method:

```bash
# Clone the repository
git clone https://github.com/yourusername/get-info-from-no-feed-page.git
cd get-info-from-no-feed-page

# Install dependencies
npm install

# Build the project
npm run build

# Link the package globally (makes the development package available globally)
npm link
```

This will make the `web-feed` command available globally.

## Usage

### Running from command line

```bash
# When installed globally
web-feed <url> [options]

# When installed locally
npx web-feed <url> [options]
```

### Arguments

- `<url>`: URL of the target webpage. Use "all" to process all supported sites

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