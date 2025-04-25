# Web Announcement Feed Generator Python

A CLI tool that scrapes announcement information from specified web pages and converts it into RSS 2.0 feed and CSV file formats.

## Features

<<<<<<< HEAD
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
=======
- Scrapes announcements from web pages without existing RSS feeds
- Extracts date, title, content, and category information from announcements
- Outputs RSS 2.0 formatted feed files
- Generates CSV lists filtered by various conditions
- Supports multiple websites with specialized scrapers
- Differential mode to only process new items

## Requirements

- Python 3.x
- Required packages:
>>>>>>> parent of f034961 (fixed prompt.md, and effect it for all files.)
  - requests
  - beautifulsoup4

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
- Monaca Headline: https://ja.monaca.io/headline/

## License

See [LICENSE](LICENSE) file for details.