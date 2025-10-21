#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to validate the Monaca scraper implementation
without requiring actual network access.

This script tests the core functionality of the scraper
using mocked data.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scrapers.config import (
    get_site_config,
    is_lambda_environment,
    get_chrome_options_for_lambda,
    get_chrome_options_for_local
)

def test_lambda_detection():
    """Test Lambda environment detection"""
    print("Testing Lambda environment detection...")
    
    # Test without environment variables
    is_lambda = is_lambda_environment()
    print(f"  Current environment Lambda: {is_lambda}")
    
    # Test with mock environment variable
    os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'test-function'
    is_lambda_after = is_lambda_environment()
    print(f"  After setting AWS_LAMBDA_FUNCTION_NAME: {is_lambda_after}")
    assert is_lambda_after == True, "Lambda detection should return True when env var is set"
    
    # Clean up
    del os.environ['AWS_LAMBDA_FUNCTION_NAME']
    
    print("  ✅ Lambda detection test passed\n")

def test_site_config():
    """Test site-specific configuration"""
    print("Testing site-specific configuration...")
    
    # Test Monaca config
    monaca_url = 'https://ja.monaca.io/headline/'
    config = get_site_config(monaca_url)
    
    print(f"  Monaca config:")
    print(f"    Name: {config['name']}")
    print(f"    Requires Selenium: {config['requires_selenium']}")
    print(f"    Wait time: {config['selenium_wait_time']}s")
    print(f"    Post-load wait: {config['post_load_wait']}s")
    print(f"    Min items: {config['min_items_threshold']}")
    
    assert config['name'] == 'Monaca Headline', "Monaca config should be loaded"
    assert config['selenium_wait_time'] == 20, "Wait time should be 20 seconds"
    assert config['post_load_wait'] == 8, "Post-load wait should be 8 seconds"
    assert config['min_items_threshold'] == 2, "Min items should be 2"
    
    # Test Firebase config
    firebase_url = 'https://firebase.google.com/support/releases'
    fb_config = get_site_config(firebase_url)
    
    print(f"\n  Firebase config:")
    print(f"    Name: {fb_config['name']}")
    print(f"    Requires Selenium: {fb_config['requires_selenium']}")
    
    assert fb_config['name'] == 'Firebase Release Notes', "Firebase config should be loaded"
    assert fb_config['requires_selenium'] == False, "Firebase should not require Selenium"
    
    # Test unknown URL (should return default)
    unknown_url = 'https://example.com/news'
    default_config = get_site_config(unknown_url)
    
    print(f"\n  Default config for unknown URL:")
    print(f"    Name: {default_config['name']}")
    
    assert default_config['name'] == 'Generic', "Unknown URL should get generic config"
    
    print("  ✅ Site config test passed\n")

def test_chrome_options():
    """Test Chrome options generation"""
    print("Testing Chrome options generation...")
    
    # Test Lambda options
    lambda_options = get_chrome_options_for_lambda()
    print(f"  Lambda options count: {len(lambda_options)}")
    
    assert '--single-process' in lambda_options, "Lambda options should include --single-process"
    assert '--headless=new' in lambda_options, "Lambda options should include --headless=new"
    assert '--no-sandbox' in lambda_options, "Lambda options should include --no-sandbox"
    
    # Test local options
    local_options = get_chrome_options_for_local()
    print(f"  Local options count: {len(local_options)}")
    
    assert '--headless=new' in local_options, "Local options should include --headless=new"
    assert '--single-process' not in local_options, "Local options should NOT include --single-process"
    
    print("  ✅ Chrome options test passed\n")

def test_parse_functions():
    """Test parsing functions"""
    print("Testing parse functions...")
    
    from scrapers.ja_monaca_io_headline import parse_date, detect_categories
    
    # Test date parsing
    test_dates = [
        ('2025年10月15日', 2025, 10, 15),
        ('2025-10-15', 2025, 10, 15),
        ('2025/10/15', 2025, 10, 15),
    ]
    
    for date_str, year, month, day in test_dates:
        parsed = parse_date(date_str)
        assert parsed.year == year, f"Year should be {year} for {date_str}"
        assert parsed.month == month, f"Month should be {month} for {date_str}"
        assert parsed.day == day, f"Day should be {day} for {date_str}"
    
    print(f"  ✅ Date parsing test passed ({len(test_dates)} patterns)")
    
    # Test category detection
    test_cases = [
        ('重要なお知らせ', ['Important']),
        ('リリースノート', ['Release']),
        ('メンテナンスのお知らせ', ['Maintenance']),
    ]
    
    for text, expected in test_cases:
        categories = detect_categories(text)
        for exp_cat in expected:
            assert exp_cat in categories, f"Category {exp_cat} should be detected in '{text}'"
    
    print(f"  ✅ Category detection test passed ({len(test_cases)} cases)\n")

def main():
    """Run all tests"""
    print("=" * 60)
    print("Monaca Scraper Implementation Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_lambda_detection()
        test_site_config()
        test_chrome_options()
        test_parse_functions()
        
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
