# Web Announcement Feed Generator Python

A command-line tool that scrapes announcement information from specified websites, generates RSS feed files, and outputs a CSV list of items that match filtering criteria.

## Features

- Scrapes announcement information from specified URLs
- Converts announcement data into RSS 2.0 format feed
- Creates CSV files with filtered items based on specified criteria
- Supports incremental updates with diff mode
- Handles JavaScript-loaded content with Selenium
- Supports date filtering, category filtering, and customizable output file naming

## Prerequisites

- Ubuntu (Latest LTS version)
- Python 3 (Latest LTS version)
- Chrome browser
- The following Python packages (installed via requirements.txt):
  - beautifulsoup4
  - requests
  - selenium
  - webdriver-manager

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/username/web-announcement-feed-generator-python.git
   cd web-announcement-feed-generator-python
   ```

2. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Basic usage:

```bash
python src/main.py <url> [options]
```

### Arguments

- `url`: The URL of the webpage to scrape, or "all" to process all supported URLs

### Options

- `--since YYYY-MM-DD`: Only process items on or after this date
- `--until YYYY-MM-DD`: Only process items on or before this date
- `--category TEXT`: Only process items containing this category text
- `--exclude-category TEXT`: Exclude items containing this category text
- `--feed-output PATH`: Custom path for the RSS feed output file
- `--csv-output PATH`: Custom path for the CSV output file
- `--diff-mode`: Incremental update mode (only process items newer than the existing feed)
- `--with-date`: Add current date to the output filename
- `--debug`: Enable detailed debug logging
- `--silent`: Suppress all output

### Examples

Scrape a specific URL:
```bash
python src/main.py https://firebase.google.com/support/releases
```

Scrape all supported URLs:
```bash
python src/main.py all
```

Filter by date range:
```bash
python src/main.py https://firebase.google.com/support/releases --since 2025-01-01 --until 2025-03-31
```

Filter by category:
```bash
python src/main.py https://firebase.google.com/support/releases --category important
```

Use diff mode to only process new items:
```bash
python src/main.py https://firebase.google.com/support/releases --diff-mode
```

## Supported Websites

The following websites are currently supported:

- Firebase Release Notes: https://firebase.google.com/support/releases
- Monaca Headline (Japanese): https://ja.monaca.io/headline/

## Development

### Project Structure

```
.
├── LICENSE
├── README.md
├── README_ja.md
├── requirements.txt
└── src/
    ├── main.py
    └── scrapers/
        ├── __init__.py
        ├── firebase_google_com_support_releases.py
        ├── generic.py
        └── ja_monaca_io_headline.py
```

### Adding Support for New Websites

To add support for a new website:

1. Create a new scraper file in the `src/scrapers/` directory
   - The file should be named based on the URL (e.g., `example_com_news.py`)
2. Implement the `scrape(url, debug=False, silent=False)` function that:
   - Takes a URL as input
   - Returns a list of announcement items as dictionaries
   - Each dictionary should include:
     - `title`: The announcement title
     - `description`: The announcement content
     - `link`: URL to the full announcement
     - `pubDate`: Publication date (RFC 822 format)
     - `categories`: List of category strings
     - `guid`: Globally unique identifier for the item

### Testing

Test and debug the scraper against all supported URLs:

```bash
python src/main.py all --debug
```

## License

MIT-0 License. See the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Tomoya Yamamoto