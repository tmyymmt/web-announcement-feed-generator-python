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

- Node.js 14.0.0 or higher
- Chrome browser (for Selenium)

## Prerequisites

- Make sure the `chromedriver` version in `package.json` dependencies matches your Chrome browser version
- Install Japanese fonts if not already installed, for proper display of Japanese content
- Run `webdriver-manager start --detach` if necessary for Selenium to work properly

## Development

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/web-announcement-feed-generator-python.git
cd web-announcement-feed-generator-python
```

2. Install dependencies:
```bash
npm install
```

### Building

To build the project:
```bash
npm run build
```

This compiles TypeScript files (.ts) to JavaScript (.js) and outputs them to the `dist` directory.

### Running during development

To run the application during development:
```bash
npm run dev -- <url> [options]
```

Or after building:
```bash
node dist/index.js <url> [options]
```

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

- `-o, --output <path>`: Output file path
- `--with-date`: Add date to the output filename
- `-s, --start-date <date>`: Filter announcements after specified date (YYYY-MM-DD)
- `-e, --end-date <date>`: Filter announcements before specified date (YYYY-MM-DD)
- `-ic, --include-category <text>`: Filter announcements where category contains specified text
- `-ec, --exclude-category <text>`: Filter announcements where category doesn't contain specified text
- `-d, --diff-mode`: Output only updates since the last feed
- `--silent`: Suppress log output
- `-h, --help`: Display help
- `-V, --version`: Display version

## Examples

### Generate feed for a specific site

```bash
web-feed https://ja.monaca.io/headline/ --with-date
```

### Generate feeds for all sites

```bash
web-feed all --with-date
```

### Export CSV with filtering conditions

```bash
web-feed https://firebase.google.com/support/releases --start-date 2023-01-01 --include-category important
```

### Run in differential mode

```bash
web-feed https://ja.monaca.io/headline/ -d
```

## Output Files

The program generates two files:

1. RSS 2.0 feed (XML file)
2. CSV file with the announcement list

By default, output filenames are automatically generated based on the domain and path of the webpage.
When using the `--with-date` option, the date is added to the filename.

## License

This project is licensed under the MIT No Attribution License (MIT-0). See the [LICENSE](./LICENSE) file for details.

The MIT-0 license allows you to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software without attribution requirements.

## Issues & Improvements

- To add support for a new website, create a new scraper class in the `src/scrapers/` directory and register it in `scraper-factory.ts`.
- If there's a version mismatch between ChromeDriver and Chrome browser, install the appropriate version of ChromeDriver.