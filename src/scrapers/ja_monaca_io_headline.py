# -*- coding: utf-8 -*-

import datetime
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import re
import urllib.parse
import logging
from tempfile import mkdtemp
import time

# ロガーの設定
logger = logging.getLogger(__name__)

def parse_date(date_text: str) -> datetime.datetime:
    """日付テキストを解析してdatetimeオブジェクトに変換する"""
    # ISO 8601形式 (例: "2025-10-15" or "2025-10-15T12:00:00")
    iso_pattern = r'(\d{4})-(\d{1,2})-(\d{1,2})'
    iso_match = re.search(iso_pattern, date_text)
    
    if iso_match:
        year, month, day = iso_match.groups()
        return datetime.datetime(int(year), int(month), int(day))
    
    # 日本語の日付パターン (例: "2025年4月17日")
    jp_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
    jp_match = re.search(jp_pattern, date_text)
    
    if jp_match:
        year, month, day = jp_match.groups()
        return datetime.datetime(int(year), int(month), int(day))
    
    # 数字のみの日付パターン (例: "2025.4.17" or "2025/4/17")
    num_pattern = r'(\d{4})[./](\d{1,2})[./](\d{1,2})'
    num_match = re.search(num_pattern, date_text)
    
    if num_match:
        year, month, day = num_match.groups()
        return datetime.datetime(int(year), int(month), int(day))
    
    # その他のパターンが見つからない場合は現在の日時を返す
    return datetime.datetime.now()

def detect_categories(text: str) -> List[str]:
    """テキスト内の特定のキーワードからカテゴリを検出する"""
    categories = []
    
    # 日本語のキーワードとカテゴリのマッピング
    keywords = {
        '重要': 'Important',
        '緊急': 'Important',
        '注意': 'Notice',
        'お知らせ': 'Notice',
        'リリース': 'Release',
        '更新': 'Update',
        'アップデート': 'Update',
        '新機能': 'New Feature',
        '機能追加': 'New Feature',
        'バグ修正': 'Bugfix',
        '不具合修正': 'Bugfix',
        '修正': 'Fix',
        'セキュリティ': 'Security',
        'メンテナンス': 'Maintenance',
        '廃止': 'Deprecated',
        '提供終了': 'Deprecated',
        '終了': 'End of Service',
        'サポート終了': 'End of Support',
        'サービス終了': 'End of Service',
        # 英語キーワードも追加
        'deprecated': 'Deprecated',
        'shutdown': 'End of Service',
        'important': 'Important'
    }
    
    text_lower = text.lower()
    
    for keyword, category in keywords.items():
        if keyword.lower() in text_lower:
            categories.append(category)
    
    # カテゴリが検出されなかった場合は「その他」を追加
    if not categories:
        categories.append('Other')
    
    return list(set(categories))  # 重複を削除

def scrape_with_selenium(
    url: str,
    wait_time: int = 20,
    post_load_wait: int = 8,
    use_lambda_optimization: bool = False,
    debug: bool = False,
    debug_selenium: bool = False
) -> Optional[str]:
    """Seleniumを使用してページをスクレイピングする
    
    Args:
        url: スクレイピング対象のURL
        wait_time: Seleniumの待機時間（秒）
        post_load_wait: ページロード後の追加待機時間（秒）
        use_lambda_optimization: Lambda最適化を使用するか
        debug: デバッグモード
        debug_selenium: Seleniumの詳細ログを出力するか
        
    Returns:
        取得したHTMLまたはNone（失敗時）
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError as e:
        logger.error(f"Seleniumのインポートに失敗しました: {e}")
        return None
    
    try:
        # config.pyから設定を取得
        try:
            from .config import (
                is_lambda_environment,
                get_chrome_options_for_lambda,
                get_chrome_options_for_local
            )
        except ImportError:
            # config.pyが利用できない場合はローカル関数を使用
            def is_lambda_environment():
                import os
                return bool(os.environ.get('AWS_LAMBDA_FUNCTION_NAME') or 
                           os.environ.get('LAMBDA_TASK_ROOT'))
            
            def get_chrome_options_for_lambda():
                return [
                    '--headless=new', '--no-sandbox', '--disable-gpu',
                    '--window-size=1280x1696', '--disable-dev-shm-usage',
                    '--disable-dev-tools', '--no-zygote', '--single-process',
                    '--disable-software-rasterizer', '--disable-extensions',
                    '--remote-debugging-port=9222',
                ]
            
            def get_chrome_options_for_local():
                return [
                    '--headless=new', '--no-sandbox', '--disable-gpu',
                    '--window-size=1280x1696', '--disable-dev-shm-usage',
                    '--remote-debugging-port=9222',
                ]
        
        # Lambda環境を自動検出
        is_lambda = is_lambda_environment() or use_lambda_optimization
        
        if debug:
            logger.debug(f"Lambda環境: {is_lambda}")
            logger.debug(f"待機時間: {wait_time}秒、ポストロード待機: {post_load_wait}秒")
        
        # Chrome optionsを設定
        chrome_options = Options()
        
        if is_lambda:
            option_list = get_chrome_options_for_lambda()
            if debug:
                logger.debug("Lambda最適化モードを使用")
        else:
            option_list = get_chrome_options_for_local()
            if debug:
                logger.debug("ローカルモードを使用")
        
        # Optionsにオプションを追加
        for option in option_list:
            chrome_options.add_argument(option)
        
        # 一時ディレクトリを作成
        chrome_options.add_argument(f"--user-data-dir={mkdtemp()}")
        chrome_options.add_argument(f"--data-path={mkdtemp()}")
        chrome_options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        
        # User-Agentを設定
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        
        # SSL/TLS証明書エラーを無視
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--allow-insecure-localhost")
        chrome_options.add_argument("--ignore-certificate-errors-spki-list")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        # SSL証明書の検証を無効化（Seleniumレベル）
        chrome_options.set_capability('acceptInsecureCerts', True)
        
        # パフォーマンス最適化：不要なリソースの読み込みを無効化
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # 画像を無効化
            "profile.managed_default_content_settings.stylesheets": 2,  # CSSを無効化
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        driver = None
        
        if debug_selenium or debug:
            logger.debug("ChromeDriverを初期化中...")
        
        # まずシステムのchromedriverを使用
        try:
            service = Service('/usr/bin/chromedriver')
            driver = webdriver.Chrome(service=service, options=chrome_options)
            if debug_selenium or debug:
                logger.debug("システムのchromedriverを使用します。")
        except Exception as e:
            if debug_selenium or debug:
                logger.debug(f"システムのchromedriver使用失敗: {e}")
                logger.debug("webdriver-managerを使用してChromeDriverをダウンロード中...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        
        if debug_selenium or debug:
            logger.debug(f"URLにアクセス中: {url}")
        
        driver.get(url)
        
        # ページが完全に読み込まれるまで待機
        if debug_selenium or debug:
            logger.debug(f"ページの読み込みを待機中（最大{wait_time}秒）...")
        
        # JavaScriptでコンテンツが読み込まれるまで待機
        # .headline-entries内にコンテンツが追加されるのを待つ
        try:
            WebDriverWait(driver, wait_time).until(
                lambda d: len(d.find_element(By.CLASS_NAME, "headline-entries").find_elements(By.CSS_SELECTOR, "div, article, a")) > 0
            )
            if debug_selenium or debug:
                logger.debug("JavaScriptによるコンテンツの読み込みが完了しました。")
        except Exception as e:
            if debug_selenium or debug:
                logger.debug(f"JavaScriptコンテンツの読み込み待機中にタイムアウト: {e}")
                logger.debug("現在のページ状態で処理を継続します。")
        
        # 追加で待機（JavaScriptアニメーションなどのため）
        if post_load_wait > 0:
            if debug_selenium or debug:
                logger.debug(f"追加で{post_load_wait}秒待機中...")
            time.sleep(post_load_wait)
        
        if debug_selenium or debug:
            logger.debug("ページの読み込みが完了しました。")
        
        # ページのHTMLを取得
        html = driver.page_source
        
        driver.quit()
        return html
        
    except Exception as e:
        logger.warning(f"Seleniumでのページ取得中にエラーが発生: {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        return None

def scrape_with_requests(url: str, debug: bool = False) -> Optional[str]:
    """requestsを使用してページをスクレイピングする
    
    Args:
        url: スクレイピング対象のURL
        debug: デバッグモード
        
    Returns:
        取得したHTMLまたはNone（失敗時）
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        if debug:
            logger.debug("requestsを使用してページを取得しました。")
        return response.text
    except Exception as e:
        logger.warning(f"requestsでのページ取得中にエラーが発生: {e}")
        return None

def parse_html_content(
    html: str,
    url: str,
    selector_patterns: List[Dict[str, Optional[str]]],
    debug: bool = False
) -> List[Dict[str, Any]]:
    """HTMLをパースしてアイテムを抽出する
    
    Args:
        html: パース対象のHTML
        url: ベースURL
        selector_patterns: CSSセレクターパターンのリスト
        debug: デバッグモード
        
    Returns:
        抽出されたアイテムのリスト
    """
    # HTMLをパース
    soup = BeautifulSoup(html, 'html.parser')
    
    # お知らせの項目を格納するリスト
    items = []
    
    for pattern_idx, pattern in enumerate(selector_patterns):
        headline_entries = soup.select(pattern['entry'])
        
        if debug and headline_entries:
            logger.debug(f"パターン{pattern_idx + 1}で{len(headline_entries)}件のエントリーを検出しました")
        
        if not headline_entries:
            continue
            
        for entry in headline_entries:
            # 日付を取得
            date_element = entry.select_one(pattern['date']) if pattern['date'] else None
            date_str = "不明"
            
            if date_element:
                # datetime属性がある場合はそれを優先
                if date_element.has_attr('datetime'):
                    date_str = date_element['datetime']
                else:
                    date_str = date_element.get_text(strip=True)
            
            # 日付が見つからない場合、テキストから検索
            if date_str == "不明":
                entry_text = entry.get_text()
                date_pattern = r'(\d{4}年\d{1,2}月\d{1,2}日|\d{4}[./\-]\d{1,2}[./\-]\d{1,2})'
                date_match = re.search(date_pattern, entry_text)
                if date_match:
                    date_str = date_match.group(0)
            
            # 日付をパース
            if date_str != "不明":
                try:
                    date_obj = parse_date(date_str)
                    formatted_pub_date = date_obj.strftime('%a, %d %b %Y %H:%M:%S +0000')
                except Exception as e:
                    if debug:
                        logger.debug(f"日付のパースに失敗: {date_str}, エラー: {e}")
                    formatted_pub_date = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
            else:
                formatted_pub_date = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
            
            # カテゴリを取得
            category_element = entry.select_one(pattern['category']) if pattern['category'] else None
            category_text = category_element.get_text(strip=True) if category_element else "その他"
            
            # 内容を取得
            content = ""
            if pattern['content']:
                content_element = entry.select_one(pattern['content'])
                if content_element:
                    content = content_element.get_text(strip=True)
            
            # 内容が取得できない場合はエントリ全体から取得
            if not content:
                content = entry.get_text(strip=True)
            
            # タイトルを取得
            title = ""
            if pattern['title']:
                title_element = entry.select_one(pattern['title'])
                if title_element:
                    title = title_element.get_text(strip=True)
            
            # タイトルが取得できない場合は内容の最初の部分をタイトルとして使用
            if not title and content:
                title = content[:50] + ('...' if len(content) > 50 else '')
            elif not title:
                title = "お知らせ"
            
            # リンクを取得
            a_tag = entry.select_one('a')
            if a_tag and 'href' in a_tag.attrs:
                link = urllib.parse.urljoin(url, a_tag['href'])
            else:
                link = url
            
            # カテゴリを検出
            categories = [category_text] if category_text and category_text != "その他" else []
            detected_categories = detect_categories(title + " " + content)
            categories.extend(detected_categories)
            categories = list(set(categories))  # 重複を削除
            
            # カテゴリが空の場合は「その他」を追加
            if not categories:
                categories = ["その他"]
            
            # 項目を追加
            item = {
                'title': title,
                'description': content,
                'link': link,
                'pubDate': formatted_pub_date,
                'categories': categories,
                'guid': f"{link}#{date_str}-{hash(content)}"
            }
            
            items.append(item)
            if debug:
                logger.debug(f"アイテムを追加しました: {title[:30]}... (カテゴリ: {', '.join(categories)})")
        
        # アイテムが見つかった場合は他のパターンを試さない
        if items:
            break
    
    return items

def scrape(
    url: str,
    debug: bool = False,
    silent: bool = False,
    selenium_wait: Optional[int] = None,
    post_load_wait: Optional[int] = None,
    lambda_optimized: bool = False,
    debug_selenium: bool = False
) -> List[Dict[str, Any]]:
    """Monacaのヘッドラインページからお知らせをスクレイピングする
    
    Args:
        url: スクレイピング対象のURL
        debug: デバッグモード
        silent: サイレントモード
        selenium_wait: Seleniumの待機時間（秒）
        post_load_wait: ページロード後の追加待機時間（秒）
        lambda_optimized: Lambda最適化モードを明示的に有効化
        debug_selenium: Seleniumの詳細ログを出力
        
    Returns:
        スクレイピングされたアイテムのリスト
    """
    if not silent:
        logger.info(f"Monaca ヘッドラインスクレイパーを実行中: {url}")
    
    # サイト設定を取得
    try:
        from .config import get_site_config, is_lambda_environment
        site_config = get_site_config(url)
        is_lambda = is_lambda_environment() or lambda_optimized
    except ImportError:
        # config.pyが利用できない場合はデフォルト値を使用
        site_config = {
            'selenium_wait_time': 20,
            'post_load_wait': 8,
            'min_items_threshold': 2,
        }
        import os
        is_lambda = bool(os.environ.get('AWS_LAMBDA_FUNCTION_NAME')) or lambda_optimized
    
    # コマンドライン引数で指定された値を優先
    wait_time = selenium_wait if selenium_wait is not None else site_config.get('selenium_wait_time', 20)
    post_wait = post_load_wait if post_load_wait is not None else site_config.get('post_load_wait', 8)
    min_items = site_config.get('min_items_threshold', 2)
    
    if debug:
        logger.debug(f"設定: 待機時間={wait_time}秒, ポストロード待機={post_wait}秒, 最小アイテム数={min_items}")
        logger.debug(f"Lambda環境: {is_lambda}")
    
    # CSSセレクターパターン
    selector_patterns = [
        {
            'entry': '.headline-entry',
            'date': '.headline-entry-date',
            'category': '.headline-entry-type-badge',
            'content': '.headline-entry-content',
            'title': None
        },
        {
            'entry': '.news-item, article.news-item',
            'date': '.date, time, .news-date',
            'category': '.badge, .category, .news-category',
            'content': '.content, .news-content, .description',
            'title': 'a, h1, h2, h3, .title'
        },
        {
            'entry': '.headline-item',
            'date': 'time, .date, .headline-date',
            'category': '.badge, .tag',
            'content': '.content, .body',
            'title': 'a, h1, h2, h3'
        },
        {
            'entry': 'article',
            'date': 'time, .date, .published',
            'category': '.badge, .tag, .category',
            'content': '.content, .body, p',
            'title': 'a, h1, h2, h3, h4, .title'
        },
    ]
    
    items = []
    
    # 手法1: Selenium最適版
    if debug:
        logger.info("手法1: Selenium最適版を試行中...")
    
    html = scrape_with_selenium(
        url=url,
        wait_time=wait_time,
        post_load_wait=post_wait,
        use_lambda_optimization=is_lambda or lambda_optimized,
        debug=debug,
        debug_selenium=debug_selenium
    )
    
    if html:
        items = parse_html_content(html, url, selector_patterns, debug)
        if debug:
            logger.info(f"Selenium最適版で {len(items)} 個のアイテムを取得しました。")
        
        # 十分なアイテムが取得できた場合は成功
        if len(items) >= min_items:
            if not silent:
                logger.info(f"合計 {len(items)} 個のアイテムを取得しました。")
            return items
    
    # 手法2: Selenium標準版（待機時間を短くして再試行）
    if debug:
        logger.info("手法2: Selenium標準版を試行中...")
    
    html = scrape_with_selenium(
        url=url,
        wait_time=10,
        post_load_wait=2,
        use_lambda_optimization=False,
        debug=debug,
        debug_selenium=debug_selenium
    )
    
    if html:
        items2 = parse_html_content(html, url, selector_patterns, debug)
        if debug:
            logger.info(f"Selenium標準版で {len(items2)} 個のアイテムを取得しました。")
        
        # より多くのアイテムを取得できた方を使用
        if len(items2) > len(items):
            items = items2
        
        if len(items) >= min_items:
            if not silent:
                logger.info(f"合計 {len(items)} 個のアイテムを取得しました。")
            return items
    
    # 手法3: requests + BeautifulSoup
    if debug:
        logger.info("手法3: requests + BeautifulSoupを試行中...")
    
    html = scrape_with_requests(url, debug)
    
    if html:
        items3 = parse_html_content(html, url, selector_patterns, debug)
        if debug:
            logger.info(f"requests + BeautifulSoupで {len(items3)} 個のアイテムを取得しました。")
        
        # より多くのアイテムを取得できた方を使用
        if len(items3) > len(items):
            items = items3
    
    # すべての手法を試した後
    if len(items) < min_items:
        logger.warning(f"警告: 取得できたアイテム数（{len(items)}個）が最小しきい値（{min_items}個）を下回っています。")
    
    if not silent:
        logger.info(f"合計 {len(items)} 個のアイテムを取得しました。")
    
    return items