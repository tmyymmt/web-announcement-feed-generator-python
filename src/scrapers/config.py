# -*- coding: utf-8 -*-
"""
Site-specific configuration for scrapers
"""

import os
from typing import Dict, Any

# サイト別の設定
SITE_CONFIGS = {
    'https://ja.monaca.io/headline/': {
        'name': 'Monaca Headline',
        'requires_selenium': True,
        'selenium_wait_time': 20,  # Seleniumの待機時間（秒）
        'post_load_wait': 8,  # ページロード後の追加待機時間（秒）
        'use_lambda_optimization': True,
        'css_selectors': [
            '.headline-entry',
            '.news-item',
            'article.news-item',
            '.headline-item',
            'article',
        ],
        'min_items_threshold': 2,  # 最低限取得すべきアイテム数
    },
    'https://firebase.google.com/support/releases': {
        'name': 'Firebase Release Notes',
        'requires_selenium': False,
        'selenium_wait_time': 5,
        'post_load_wait': 0,
        'use_lambda_optimization': False,
        'css_selectors': [
            'article',
            '.release-note',
        ],
        'min_items_threshold': 1,
    },
}

def get_site_config(url: str) -> Dict[str, Any]:
    """URLからサイト設定を取得する
    
    Args:
        url: 対象URL
        
    Returns:
        サイト設定の辞書。該当する設定がない場合はデフォルト設定を返す
    """
    # 完全一致で検索
    if url in SITE_CONFIGS:
        return SITE_CONFIGS[url]
    
    # URLに含まれるドメインで検索
    for config_url, config in SITE_CONFIGS.items():
        if config_url in url or url in config_url:
            return config
    
    # デフォルト設定を返す
    return {
        'name': 'Generic',
        'requires_selenium': False,
        'selenium_wait_time': 10,
        'post_load_wait': 2,
        'use_lambda_optimization': False,
        'css_selectors': ['article', '.news-item', '.entry'],
        'min_items_threshold': 1,
    }

def is_lambda_environment() -> bool:
    """AWS Lambda環境で実行されているかを判定する
    
    Returns:
        Lambda環境の場合True、それ以外はFalse
    """
    # Lambda環境を示す環境変数をチェック
    lambda_indicators = [
        'AWS_LAMBDA_FUNCTION_NAME',
        'LAMBDA_TASK_ROOT',
        'AWS_EXECUTION_ENV',
    ]
    
    for indicator in lambda_indicators:
        if os.environ.get(indicator):
            return True
    
    return False

def get_chrome_options_for_lambda():
    """Lambda環境用のChrome optionsを取得する
    
    Returns:
        Lambda環境用に最適化されたChromeOptionsのリスト
    """
    options = [
        '--headless=new',
        '--no-sandbox',
        '--disable-gpu',
        '--window-size=1280x1696',
        '--disable-dev-shm-usage',
        '--disable-dev-tools',
        '--no-zygote',
        '--single-process',  # Lambda環境用
        '--disable-software-rasterizer',
        '--disable-extensions',
        '--disable-background-networking',
        '--disable-sync',
        '--metrics-recording-only',
        '--disable-default-apps',
        '--mute-audio',
        '--no-first-run',
        '--disable-setuid-sandbox',
        '--disable-web-security',
        '--disable-blink-features=AutomationControlled',
        '--remote-debugging-port=9222',
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        '--ignore-certificate-errors',
        '--ignore-ssl-errors',
        '--ignore-certificate-errors-spki-list',
        '--allow-insecure-localhost',
        '--allow-running-insecure-content',
        '--unsafely-treat-insecure-origin-as-secure=https://ja.monaca.io',
        '--disable-web-security',
    ]
    
    return options

def get_chrome_options_for_local():
    """ローカル環境用のChrome optionsを取得する
    
    Returns:
        ローカル環境用のChromeOptionsのリスト
    """
    options = [
        '--headless=new',
        '--no-sandbox',
        '--disable-gpu',
        '--window-size=1280x1696',
        '--disable-dev-shm-usage',
        '--disable-dev-tools',
        '--no-zygote',
        '--remote-debugging-port=9222',
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        '--ignore-certificate-errors',
        '--ignore-ssl-errors',
        '--ignore-certificate-errors-spki-list',
        '--allow-insecure-localhost',
        '--allow-running-insecure-content',
        '--unsafely-treat-insecure-origin-as-secure=https://ja.monaca.io',
    ]
    
    return options
