# Web Announcement Feed Generator

A CLI tool that scrapes announcement information from specified web pages, outputs RSS feed files, and generates CSV lists of items that match filter conditions.

## Features

- Scrapes announcements from web pages without existing RSS feeds
- Extracts date, title, content, and category information from announcements
- Outputs RSS 2.0 formatted feed files
- Generates CSV lists filtered by various conditions
- Supports multiple websites with specialized scrapers
- Differential mode to only process new items

## Requirements

- Python 3.x
- Required packages:
  - requests
  - beautifulsoup4

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
- Monaca Headline: https://ja.monaca.io/headline/

## License

See [LICENSE](LICENSE) file for details.