# -*- coding: utf-8 -*-

import datetime
import requests
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import re
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ロガーの設定
logger = logging.getLogger(__name__)

def parse_date(date_text: str) -> datetime.datetime:
    """日付テキストを解析してdatetimeオブジェクトに変換する"""
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
        'サービス終了': 'End of Service'
    }
    
    text_lower = text.lower()
    
    for keyword, category in keywords.items():
        if keyword.lower() in text_lower:
            categories.append(category)
    
    # カテゴリが検出されなかった場合は「その他」を追加
    if not categories:
        categories.append('Other')
    
    return list(set(categories))  # 重複を削除

def get_latest_chrome_user_agent():
    """最新のChromeのUser-Agentを返す"""
    return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def scrape(url: str) -> List[Dict[str, Any]]:
    """Monacaのヘッドラインページからお知らせをスクレイピングする"""
    logger.info(f"Monaca ヘッドラインスクレイパーを実行中: {url}")
    
    # JavaScriptの遅延読み込みに対応するためSeleniumを使用
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f"--user-agent={get_latest_chrome_user_agent()}")
    
    try:
        # WebDriverを初期化
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # ページが完全に読み込まれるまで待機
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "headline-entry"))
        )
        
        # ページのHTMLを取得
        html = driver.page_source
        logger.debug("Seleniumでページの取得に成功しました。")
    except Exception as e:
        logger.error(f"Seleniumでのページ取得中にエラーが発生: {e}")
        logger.info("代替方法としてrequestsを使用します")
        
        # 失敗した場合は通常のrequestsでの取得を試みる
        headers = {
            'User-Agent': get_latest_chrome_user_agent()
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        html = response.text
    finally:
        if 'driver' in locals():
            driver.quit()
    
    # HTMLをパース
    soup = BeautifulSoup(html, 'html.parser')
    
    # お知らせの項目を格納するリスト
    items = []
    
    # headline-entryクラスを持つ要素を検索（お知らせの項目）
    headline_entries = soup.select('.headline-entry')
    logger.debug(f"{len(headline_entries)}件のヘッドラインエントリーを検出しました")
    
    for entry in headline_entries:
        # 日付を取得
        date_element = entry.select_one('.headline-entry-date')
        date_str = date_element.get_text(strip=True) if date_element else "不明"
        
        # 日付をパース
        if date_str != "不明":
            try:
                date_obj = parse_date(date_str)
                formatted_pub_date = date_obj.strftime('%a, %d %b %Y %H:%M:%S +0000')
            except Exception as e:
                logger.error(f"日付のパースに失敗: {date_str}, エラー: {e}")
                formatted_pub_date = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
        else:
            formatted_pub_date = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        # カテゴリを取得
        category_element = entry.select_one('.headline-entry-type-badge')
        category_text = category_element.get_text(strip=True) if category_element else "その他"
        
        # 内容を取得
        content_element = entry.select_one('.headline-entry-content')
        content = content_element.get_text(strip=True) if content_element else ""
        
        # リンクを取得
        a_tag = entry.select_one('a')
        if a_tag and 'href' in a_tag.attrs:
            link = urllib.parse.urljoin(url, a_tag['href'])
        else:
            link = url
        
        # カテゴリを検出
        categories = [category_text] if category_text else []
        categories.extend(detect_categories(content))
        categories = list(set(categories))  # 重複を削除
        
        # タイトルがない場合は内容の最初の部分をタイトルとして使用
        title = content[:50] + ('...' if len(content) > 50 else '')
        
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
        logger.debug(f"アイテムを追加しました: {title} (カテゴリ: {', '.join(categories)})")
    
    # お知らせが見つからない場合の代替処理
    if not items:
        logger.warning("headline-entryクラスが見つかりませんでした。代替方法で検索します...")
        
        # 他の可能性のあるセレクタで検索
        alternative_entries = soup.select('div.news-item, article, .entry, .post')
        
        for entry in alternative_entries:
            # 内容を取得
            content = entry.get_text(strip=True)
            
            # 日付を検出
            date_pattern = r'(\d{4}年\d{1,2}月\d{1,2}日|\d{4}[./]\d{1,2}[./]\d{1,2})'
            date_match = re.search(date_pattern, content)
            date_str = date_match.group(0) if date_match else "不明"
            
            # 日付をパース
            if date_str != "不明":
                try:
                    date_obj = parse_date(date_str)
                    formatted_pub_date = date_obj.strftime('%a, %d %b %Y %H:%M:%S +0000')
                except Exception:
                    formatted_pub_date = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
            else:
                formatted_pub_date = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
            
            # リンクを取得
            a_tag = entry.select_one('a')
            if a_tag and 'href' in a_tag.attrs:
                link = urllib.parse.urljoin(url, a_tag['href'])
            else:
                link = url
            
            # カテゴリを検出
            categories = detect_categories(content)
            
            # タイトルを検出
            title_element = entry.select_one('h1, h2, h3, h4, .title')
            title = title_element.get_text(strip=True) if title_element else content[:50] + ('...' if len(content) > 50 else '')
            
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
            logger.debug(f"代替方法でアイテムを追加しました: {title} (カテゴリ: {', '.join(categories)})")
    
    logger.info(f"合計 {len(items)} 個のアイテムを取得しました。")
    return items