# -*- coding: utf-8 -*-

import re
import datetime
import requests
import os
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ロガーの設定
logger = logging.getLogger(__name__)

# AWS Lambda 環境かどうかを確認する関数
def is_running_in_lambda():
    return os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None

# 適切なWebDriverを準備する
def setup_webdriver():
    chrome_options = None
    driver = None
    
    if is_running_in_lambda():
        try:
            # Lambda環境の場合は chrome-aws-lambda-layer を使用
            import chrome_aws_lambda
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(f"--user-agent={get_latest_chrome_user_agent()}")
            chrome_options.binary_location = chrome_aws_lambda.binary_path
            
            driver = webdriver.Chrome(
                executable_path=chrome_aws_lambda.binary_path,
                options=chrome_options
            )
            
            logger.info("AWS Lambda 環境用の chrome-aws-lambda-layer を使用してWebDriverを初期化しました")
        except ImportError:
            logger.warning("chrome-aws-lambda-layerのインポートに失敗しました。通常のrequestsを使用します")
            return None
    else:
        # 通常環境の場合
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(f"--user-agent={get_latest_chrome_user_agent()}")
            
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("通常環境用のWebDriverを初期化しました")
        except Exception as e:
            logger.error(f"WebDriverの初期化に失敗しました: {e}")
            return None
    
    return driver

def extract_date(date_str: str) -> datetime.datetime:
    """日付文字列をパースしてdatetimeオブジェクトに変換する"""
    # 日付フォーマットの例: "April 2, 2025" や "Apr 2, 2025"
    months = {
        'January': 1, 'Jan': 1,
        'February': 2, 'Feb': 2,
        'March': 3, 'Mar': 3,
        'April': 4, 'Apr': 4,
        'May': 5,
        'June': 6, 'Jun': 6,
        'July': 7, 'Jul': 7,
        'August': 8, 'Aug': 8,
        'September': 9, 'Sep': 9,
        'October': 10, 'Oct': 10,
        'November': 11, 'Nov': 11,
        'December': 12, 'Dec': 12
    }
    
    # 日付文字列からスペースと不要な文字を削除
    date_str = date_str.strip()
    
    # 日付フォーマットのパターンを検出
    pattern = r'(\w+)\s+(\d+),?\s+(\d{4})'
    match = re.search(pattern, date_str)
    
    if match:
        month_name, day, year = match.groups()
        month = months.get(month_name, 1)  # 不明な月名の場合はデフォルトで1月とする
        
        # datetimeオブジェクトを作成
        dt = datetime.datetime(int(year), month, int(day))
        return dt
    
    # パターンにマッチしない場合は現在の日時を返す
    return datetime.datetime.now()

def extract_category_from_class(class_name: str) -> str:
    """release-* 形式のクラス名からカテゴリ名を抽出する"""
    if class_name and class_name.startswith('release-'):
        # release- プレフィックスを削除
        return class_name.replace('release-', '')
    return 'other'

def detect_categories(title: str, description: str, class_names: List[str] = None) -> List[str]:
    """タイトル、説明文、クラス名からカテゴリを検出する"""
    categories = []
    
    # クラス名からカテゴリを抽出
    if class_names:
        for class_name in class_names:
            if class_name.startswith('release-'):
                category = extract_category_from_class(class_name)
                if category:
                    categories.append(category)
    
    # 特定のキーワードに基づいてカテゴリを検出
    keywords = {
        'deprecated': 'deprecated',
        'deprecation': 'deprecated',
        'important': 'important',
        'shutdown': 'shutdown',
        'update': 'changed',
        'new': 'feature',
        'feature': 'feature',
        'release': 'release',
        'beta': 'beta',
        'alpha': 'alpha',
        'preview': 'preview',
        'bug': 'fixed',
        'fix': 'fixed',
        'security': 'security',
        'removed': 'removed',
        'changed': 'changed',
        'admin': 'admin',
        'android': 'android',
        'cli': 'cli',
        'cpp': 'cpp',
        'flutter': 'flutter',
        'functions': 'functions',
        'ios': 'ios',
        'javascript': 'javascript',
        'rules': 'rules',
        'unity': 'unity',
        'issue': 'issue'
    }
    
    text = (title + ' ' + description).lower()
    
    for keyword, category in keywords.items():
        if keyword.lower() in text:
            categories.append(category)
    
    # カテゴリが検出されなかった場合は「その他」を追加
    if not categories:
        categories.append('other')
    
    return list(set(categories))  # 重複を削除

def get_latest_chrome_user_agent():
    """最新のChromeのUser-Agentを返す"""
    return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def scrape(url: str) -> List[Dict[str, Any]]:
    """Firebaseのリリースページからリリースノートをスクレイピングする"""
    logger.info(f"Firebase スクレイパーを実行中: {url}")
    
    # 適切なWebDriverをセットアップ
    driver = setup_webdriver()
    
    try:
        if driver:
            # Selenium WebDriverを使用する場合
            driver.get(url)
            
            # ページが完全に読み込まれるまで待機
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "changelog"))
                )
            except:
                logger.warning("待機条件が満たされませんでした。ページを読み込み完了と仮定して続行します。")
            
            # ページのHTMLを取得
            html = driver.page_source
            logger.debug("Seleniumでページの取得に成功しました。")
        else:
            # WebDriverが利用できない場合はrequestsを使用
            logger.info("WebDriverが利用できないため、requestsを使用します")
            headers = {
                'User-Agent': get_latest_chrome_user_agent()
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            html = response.text
    except Exception as e:
        logger.error(f"ページ取得中にエラーが発生: {e}")
        logger.info("代替方法としてrequestsを使用します")
        
        # 失敗した場合は通常のrequestsでの取得を試みる
        headers = {
            'User-Agent': get_latest_chrome_user_agent()
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        html = response.text
    finally:
        if driver:
            driver.quit()
    
    # HTMLをパース
    soup = BeautifulSoup(html, 'html.parser')
    
    # リリースノートの項目を格納するリスト
    items = []
    
    # リリースヘッダーを探す - Firebaseのリリースページでは通常 h2 (日付) と h3 (製品名) が使われる
    release_headers = soup.select('h2[id], h3[id]')
    logger.debug(f"見出し要素を {len(release_headers)} 個検出しました。")
    
    if release_headers:
        current_date = None
        current_date_str = None
        current_product = None
        
        for i, header in enumerate(release_headers):
            header_text = header.get_text(strip=True)
            header_id = header.get('id', '')
            
            if header.name == 'h2' and re.search(r'\w+_\d+_\d{4}', header_id):
                # これは日付ヘッダー (例: "April 09, 2025")
                current_date_str = header_text
                try:
                    current_date = extract_date(current_date_str)
                    logger.debug(f"日付ヘッダーを検出: {current_date_str} (パース結果: {current_date})")
                except Exception as e:
                    logger.error(f"日付のパースに失敗: {current_date_str}, エラー: {e}")
                    current_date = datetime.datetime.now()
            
            elif header.name == 'h3':
                # これは製品ヘッダー (例: "Firebase Studio")
                current_product = header_text
                logger.debug(f"製品ヘッダーを検出: {current_product}")
                
                # 製品ヘッダーの次の要素から内容を取得（通常はul要素）
                next_elem = header.find_next_sibling()
                
                if next_elem and next_elem.name == 'ul':
                    # リリースアイテムのリストを処理
                    for list_item in next_elem.select('li'):
                        # リリースタイプ (feature, fixed, deprecated など)を検出
                        release_type_span = list_item.select_one('span[class*="release-"]')
                        
                        # クラス名を取得してカテゴリに変換
                        release_classes = []
                        if release_type_span:
                            release_classes = release_type_span.get('class', [])
                            release_type = extract_category_from_class(release_classes[0]) if release_classes else 'other'
                        else:
                            release_type = 'other'
                        
                        # リリース内容を取得
                        content = list_item.get_text(strip=True)
                        if release_type_span:
                            # リリースタイプのテキストを内容から削除
                            content = content.replace(release_type_span.get_text(strip=True), '', 1).strip()
                        
                        # アイテムのタイトルを作成
                        title = f"{current_product} - {release_type.capitalize()}"
                        
                        # 日付をフォーマット
                        if current_date:
                            formatted_pub_date = current_date.strftime('%a, %d %b %Y %H:%M:%S +0000')
                        else:
                            formatted_pub_date = "不明"
                        
                        # カテゴリを検出
                        categories = detect_categories(title, content, release_classes)
                        
                        # 項目を追加
                        item = {
                            'title': title,
                            'description': content,
                            'link': f"{url}#{header_id}",
                            'pubDate': formatted_pub_date,
                            'categories': categories,
                            'guid': f"{url}#{header_id}-{title}"
                        }
                        
                        items.append(item)
                        logger.debug(f"アイテムを追加しました: {title} (カテゴリ: {', '.join(categories)})")
    
    # 見出しが見つからない場合、別のアプローチを試す
    if not items:
        logger.warning("標準の見出し形式が見つかりませんでした。代替方法を試みます...")
        
        # リリースのセクションを直接探す
        release_sections = soup.select('.changelog > ul > li, .devsite-article-body ul > li')
        
        if release_sections:
            logger.debug(f"リリースセクションを {len(release_sections)} 個検出しました。")
            
            for section in release_sections:
                # リリースタイプ (feature, fixed, deprecated など)を検出
                release_type_span = section.select_one('span[class*="release-"]')
                
                # クラス名を取得してカテゴリに変換
                release_classes = []
                if release_type_span:
                    release_classes = release_type_span.get('class', [])
                    release_type = extract_category_from_class(release_classes[0]) if release_classes else 'other'
                else:
                    release_type = 'other'
                
                # リリース内容を取得
                content = section.get_text(strip=True)
                if release_type_span:
                    # リリースタイプのテキストを内容から削除
                    content = content.replace(release_type_span.get_text(strip=True), '', 1).strip()
                
                # アイテムのタイトルを作成
                title = f"Firebase Update - {release_type.capitalize()}"
                
                # 日付を検出（内容から）
                date_match = re.search(r'(\w+\s+\d+,\s+\d{4})', content)
                date_str = date_match.group(1) if date_match else "不明"
                
                try:
                    if date_str != "不明":
                        pub_date = extract_date(date_str)
                        formatted_pub_date = pub_date.strftime('%a, %d %b %Y %H:%M:%S +0000')
                    else:
                        formatted_pub_date = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
                except Exception:
                    formatted_pub_date = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
                
                # カテゴリを検出（クラス名を含む）
                categories = detect_categories(title, content, release_classes)
                
                # 項目を追加
                item = {
                    'title': title,
                    'description': content,
                    'link': url,
                    'pubDate': formatted_pub_date,
                    'categories': categories,
                    'guid': f"{url}#{content[:50]}"
                }
                
                items.append(item)
                logger.debug(f"代替方法でアイテムを追加しました: {title} (カテゴリ: {', '.join(categories)})")
    
    logger.info(f"合計 {len(items)} 個のアイテムを取得しました。")
    return items