# Web Page Feed Extractor

A CLI tool to extract feed data from web pages that don't provide RSS/Atom feeds, and output them as RSS feed and CSV.

## Features

- Extracts announcements/news information from specified web pages
- Converts the extracted information into RSS 2.0 feed format
- Allows filtering by date range and category
- Outputs both RSS feed file and CSV file
- Automatically detects categories based on content keywords
- Supports differential mode to extract only new items since the last run
- Automatically generates filenames based on URL and current date

## Requirements

- Python 3.8+
- Required packages: requests, beautifulsoup4

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/get-info-from-no-feed-page.git
cd get-info-from-no-feed-page
```

2. Install the required packages:
```
pip install -r requirements.txt
```

## Usage

Basic usage:
```
python src/main.py URL [options]
```

Options:
- `--since YYYY-MM-DD`: Filter items published on or after this date
- `--until YYYY-MM-DD`: Filter items published on or before this date
- `--category CATEGORY`: Filter items by category
- `--feed-output PATH`: Specify the output path for the RSS feed file (default: auto-generated based on URL and date)
- `--csv-output PATH`: Specify the output path for the CSV file (default: auto-generated based on URL and date)
- `--diff-mode`: Extract only items newer than the most recent date in the existing feed file

## Example

Extract feed data from Firebase release notes:
```
python src/main.py https://firebase.google.com/support/releases
```

Filter for important updates since January 1, 2024:
```
python src/main.py https://firebase.google.com/support/releases --since 2024-01-01 --category Important
```

Extract only new items since the last run:
```
python src/main.py https://firebase.google.com/support/releases --diff-mode
```

## Output Files

By default, the tool generates two output files:
1. An RSS feed file (XML format) containing all extracted items
2. A CSV file with the same items in a tabular format

Default filenames are based on the URL and current date (e.g., `firebase_google_com_support_releases_20250414.xml` and corresponding `.csv` file).

In differential mode, if files already exist, the tool creates new files with incremental numbers appended (e.g., `firebase_google_com_support_releases_20250414_1.xml`).

## Extending

To add support for a specific website, create a new Python script in the `src/scrapers` directory. The filename should follow the pattern `domain_name.py` (with dots replaced by underscores).

For example, to add support for `example.com`, create a file `src/scrapers/example_com.py` with a `scrape(url)` function that returns a list of dictionaries with the following keys:
- `title`: Title of the announcement
- `description`: Content of the announcement
- `link`: URL of the announcement
- `pubDate`: Publication date
- `categories`: List of categories
- `guid`: Globally unique identifier