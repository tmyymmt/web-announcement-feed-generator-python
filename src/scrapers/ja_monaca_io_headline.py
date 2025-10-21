# -*- coding: utf-8 -*-

import datetime
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import re
import urllib.parse
import logging
from tempfile import mkdtemp
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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

def scrape(url: str, debug: bool = False, silent: bool = False) -> List[Dict[str, Any]]:
    """Monacaのヘッドラインページからお知らせをスクレイピングする"""
    if not silent:
        logger.info(f"Monaca ヘッドラインスクレイパーを実行中: {url}")
    
    # JavaScriptの遅延読み込みに対応するためSeleniumを使用
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280x1696")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-dev-tools")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument(f"--user-data-dir={mkdtemp()}")
    chrome_options.add_argument(f"--data-path={mkdtemp()}")
    chrome_options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    # SSL/TLS証明書エラーを無視
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    
    driver = None
    html = None
    
    try:
        # ChromeDriverを初期化（システムにインストール済みのものを使用）
        if debug:
            logger.debug("ChromeDriverを初期化中...")
        
        # まずシステムのchromedriverを使用
        try:
            service = Service('/usr/bin/chromedriver')
            driver = webdriver.Chrome(service=service, options=chrome_options)
            if debug:
                logger.debug("システムのchromedriverを使用します。")
        except Exception as e:
            if debug:
                logger.debug(f"システムのchromedriver使用失敗: {e}")
                logger.debug("webdriver-managerを使用してChromeDriverをダウンロード中...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        
        # ページが完全に読み込まれるまで待機
        if debug:
            logger.debug("ページの読み込みを待機中...")
        
        # JavaScriptでコンテンツが読み込まれるまで待機（最大10秒）
        # .headline-entries内にコンテンツが追加されるのを待つ
        try:
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_element(By.CLASS_NAME, "headline-entries").find_elements(By.CSS_SELECTOR, "div, article, a")) > 0
            )
            if debug:
                logger.debug("JavaScriptによるコンテンツの読み込みが完了しました。")
        except Exception as e:
            if debug:
                logger.debug(f"JavaScriptコンテンツの読み込み待機中にタイムアウト: {e}")
                logger.debug("現在のページ状態で処理を継続します。")
        
        # 追加で少し待機（JavaScriptアニメーションなどのため）
        import time
        time.sleep(2)
        
        if debug:
            logger.debug("ページの読み込みが完了しました。")
        
        # ページのHTMLを取得
        html = driver.page_source
    except Exception as e:
        logger.warning(f"Seleniumでのページ取得中にエラーが発生: {e}")
        logger.info("代替方法としてrequestsを使用します")
        
        # 失敗した場合は通常のrequestsでの取得を試みる
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            html = response.text
            if debug:
                logger.debug("requestsを使用してページを取得しました。")
        except Exception as e:
            logger.error(f"ページの取得に失敗しました: {e}")
            raise
    finally:
        if driver is not None:
            driver.quit()
    
    # HTMLをパース
    soup = BeautifulSoup(html, 'html.parser')
    
    # お知らせの項目を格納するリスト
    items = []
    
    # 複数のセレクタパターンを試す
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
            'entry': 'article',
            'date': 'time, .date, .published',
            'category': '.badge, .tag, .category',
            'content': '.content, .body, p',
            'title': 'a, h1, h2, h3, h4, .title'
        },
        {
            'entry': '.entry, .post',
            'date': '.date, time, .entry-date',
            'category': '.category, .tag',
            'content': '.entry-content, .post-content',
            'title': 'h1, h2, h3, .title, a'
        }
    ]
    
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
    
    if not silent:
        logger.info(f"合計 {len(items)} 個のアイテムを取得しました。")
    return items