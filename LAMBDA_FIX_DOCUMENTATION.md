# Monaca Headline Scraper - Lambda Environment Fixes

## Problem Description

The Monaca headline scraper (https://ja.monaca.io/headline/) was not working properly in AWS Lambda environment. It was only retrieving 1 item instead of multiple items due to JavaScript content loading issues.

## Root Cause

The Monaca headline page loads its content dynamically via JavaScript by fetching data from an API endpoint (`https://monaca.mobi/ja/api/news/list`). The content is not present in the initial HTML but is populated after the page loads. In Lambda environments with limited resources and network restrictions, the JavaScript might not execute properly or might timeout before the content is loaded.

## Implemented Solutions

### 1. Lambda Environment Auto-Detection (✅ Required)

- **File**: `src/scrapers/config.py`
- **Function**: `is_lambda_environment()`
- Automatically detects if running in AWS Lambda by checking environment variables:
  - `AWS_LAMBDA_FUNCTION_NAME`
  - `LAMBDA_TASK_ROOT`
  - `AWS_EXECUTION_ENV`

### 2. Monaca-Specific Selenium Optimizations (✅ Required)

- **File**: `src/scrapers/ja_monaca_io_headline.py`
- Extended Selenium wait time from 10 to 20 seconds
- Added 8-second post-load wait after page loads
- Strengthened Chrome settings for Lambda:
  - `--single-process`: Runs Chrome in single-process mode (essential for Lambda)
  - `--disable-dev-shm-usage`: Prevents shared memory issues
  - `--disable-software-rasterizer`: Disables software rendering
  - `--disable-extensions`: Disables extensions
  - Additional memory and performance optimizations

### 3. Site-Specific Configuration (✅ Implemented)

- **File**: `src/scrapers/config.py`
- **Dictionary**: `SITE_CONFIGS`
- Allows configuring per-site parameters:
  - `selenium_wait_time`: Wait time for JavaScript loading
  - `post_load_wait`: Additional wait after page load
  - `requires_selenium`: Whether Selenium is required
  - `use_lambda_optimization`: Whether to use Lambda optimizations
  - `css_selectors`: List of CSS selector patterns to try
  - `min_items_threshold`: Minimum number of items expected

Example configuration for Monaca:
```python
'https://ja.monaca.io/headline/': {
    'name': 'Monaca Headline',
    'requires_selenium': True,
    'selenium_wait_time': 20,
    'post_load_wait': 8,
    'use_lambda_optimization': True,
    'css_selectors': ['.headline-entry', '.news-item', ...],
    'min_items_threshold': 2,
}
```

### 4. Fallback Mechanism (✅ Implemented)

- **File**: `src/scrapers/ja_monaca_io_headline.py`
- **Function**: `scrape()`
- Tries multiple scraping methods in order:
  1. **Selenium Optimized** (20s wait, Lambda settings)
  2. **Selenium Standard** (10s wait, standard settings)
  3. **requests + BeautifulSoup** (fallback without JavaScript)
- Each method logs the number of items retrieved
- Automatically switches to next method if insufficient items found
- Uses the method that retrieves the most items

### 5. Command-Line Arguments (✅ Implemented)

- **File**: `src/main.py`
- New arguments added:
  - `--selenium-wait <seconds>`: Override default Selenium wait time
  - `--post-load-wait <seconds>`: Override default post-load wait time
  - `--lambda-optimized`: Explicitly enable Lambda optimization mode
  - `--debug-selenium`: Enable detailed Selenium debug logging

Example usage:
```bash
python src/main.py https://ja.monaca.io/headline/ --selenium-wait 30 --post-load-wait 10 --lambda-optimized
```

### 6. Enhanced Error Handling and Logging (✅ Implemented)

- Detailed logging of each scraping attempt
- Reports number of items retrieved by each method
- Warns when retrieved item count is below threshold
- Distinguishes between timeout errors and element-not-found errors
- Logs Lambda environment detection status

### 7. SSL Certificate Handling (✅ Implemented)

- Added multiple SSL/TLS error handling flags:
  - `--ignore-certificate-errors`
  - `--ignore-ssl-errors`
  - `--ignore-certificate-errors-spki-list`
  - `--allow-insecure-localhost`
  - `--allow-running-insecure-content`
  - `acceptInsecureCerts` capability
- Handles self-signed certificates and certificate validation issues

## Testing

### Local Testing

```bash
# Test with debug output
python src/main.py https://ja.monaca.io/headline/ --debug

# Test with custom wait times
python src/main.py https://ja.monaca.io/headline/ --selenium-wait 30 --post-load-wait 10

# Test with Lambda optimization mode
python src/main.py https://ja.monaca.io/headline/ --lambda-optimized --debug
```

### Lambda Testing

If AWS SAM is available:

```bash
# Test locally with SAM
sam local invoke --event event.json

# Deploy and test
sam deploy
sam logs -n <function-name> --tail
```

## Known Limitations

1. **Network Dependency**: The scraper requires access to `https://monaca.mobi` API endpoint. In restricted network environments where this domain is not accessible, the scraper will not be able to retrieve content even with extended wait times.

2. **DNS Resolution**: Some environments (including certain CI/CD runners) may have DNS resolution issues that prevent accessing external domains.

3. **JavaScript Execution**: The page relies heavily on JavaScript to load content. Environments that block JavaScript execution or have very limited resources may still fail to load content.

## Production Deployment Checklist

- [ ] Ensure Lambda has internet access (VPC configuration if needed)
- [ ] Verify that `monaca.mobi` domain is accessible from Lambda
- [ ] Set appropriate Lambda timeout (recommend 60+ seconds)
- [ ] Set appropriate Lambda memory (recommend 1024+ MB)
- [ ] Test with `--lambda-optimized` flag
- [ ] Monitor CloudWatch logs for errors
- [ ] Set up retry logic for transient failures

## Architecture Changes

```
Old Flow:
User Request → main.py → ja_monaca_io_headline.py → Selenium (10s wait) → Parse HTML → Return Items

New Flow:
User Request → main.py (with new args) 
            ↓
            → config.py (detect Lambda, get site config)
            ↓
            → ja_monaca_io_headline.py
                ↓
                → Try Method 1: Selenium Optimized (20s wait, Lambda settings)
                → Check if enough items (>= 2)
                → If not, Try Method 2: Selenium Standard (10s wait)
                → If not, Try Method 3: requests + BeautifulSoup
                ↓
            → Return best result
```

## Security

- ✅ CodeQL security scan passed with 0 alerts
- SSL certificate validation is intentionally relaxed for compatibility
- No credentials or sensitive data are stored
- All external requests use HTTPS

## Files Modified

1. **src/main.py**
   - Added new command-line arguments
   - Updated scrape function call to pass new parameters

2. **src/scrapers/ja_monaca_io_headline.py**
   - Complete refactor with fallback mechanisms
   - Separated scraping methods (Selenium, requests)
   - Added Lambda-specific optimizations
   - Enhanced error handling and logging

3. **src/scrapers/config.py** (NEW)
   - Site-specific configuration dictionary
   - Lambda environment detection
   - Chrome options for Lambda and local environments

## Future Improvements

1. Add retry mechanism with exponential backoff
2. Implement caching to reduce API calls
3. Add metrics/monitoring integration
4. Support for custom Chrome binary path
5. Add support for proxy configuration
