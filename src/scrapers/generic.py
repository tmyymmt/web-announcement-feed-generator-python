# -*- coding: utf-8 -*-

import re
import datetime
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import urllib.parse
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

def extract_date(text: str) -> str:
    """テキストから日付パターンを抽出する"""
    # 様々な日付パターンを検出する正規表現
    patterns = [
        r'(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})',  # YYYY-MM-DD, YYYY/MM/DD
        r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4})',  # DD-MM-YYYY, DD/MM/YYYY
        r'(\w+\s+\d{1,2},?\s+\d{4})',          # Month DD, YYYY
        r'(\d{1,2}\s+\w+\s+\d{4})'             # DD Month YYYY
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]
    
    return "不明"

def detect_categories(text: str) -> List[str]:
    """テキスト内の特定のキーワードからカテゴリを検出する"""
    categories = []
    
    # 特定のキーワードに基づいてカテゴリを検出
    keywords = {
        'deprecated': 'Deprecated',
        'deprecation': 'Deprecated',
        'important': 'Important',
        'shutdown': 'Shutdown',
        'update': 'Update',
        'new': 'New',
        'feature': 'Feature',
        'release': 'Release',
        'beta': 'Beta',
        'alpha': 'Alpha',
        'preview': 'Preview',
        'bug': 'Bugfix',
        'fix': 'Bugfix',
        'security': 'Security',
        'notice': 'Notice',
        'announcement': 'Announcement',
        'maintenance': 'Maintenance',
        # 日本語のキーワード
        '重要': 'Important',
        '提供終了': 'Deprecated',
        '廃止': 'Deprecated',
        'サービス終了': 'Shutdown',
        '終了': 'Shutdown'
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
    """汎用的なスクレイピング関数"""
    if not silent:
        logger.info(f"汎用スクレイパーを使用して {url} をスクレイピングします。")
    
    # URLからHTMLを取得
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        if debug:
            logger.debug(f"ページの取得に成功しました。ステータスコード: {response.status_code}")
    except Exception as e:
        logger.error(f"ページの取得中にエラーが発生しました: {e}")
        raise
    
    # HTMLをパース
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # お知らせの項目を格納するリスト
    items = []
    
    # 一般的なお知らせセクションのパターン
    # 1. ニュース/お知らせリスト
    news_elements = soup.select('article, .news-item, .notice, .announcement, .post, .entry, div[class*="news"], div[class*="notice"], div[class*="announcement"]')
    
    if debug:
        logger.debug(f"ニュース要素を {len(news_elements)} 個検出しました。")
    
    # 2. 日付とタイトルのペアを含む要素
    if not news_elements:
        news_elements = soup.select('ul li, div.row, div.list-item')
        if debug:
            logger.debug(f"リスト要素を {len(news_elements)} 個検出しました。")
    
    # 3. 要素が見つからない場合は、テキスト内容で判断
    if not news_elements:
        # すべての段落要素を取得
        paragraphs = soup.select('p')
        
        temp_elements = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            
            # 日付パターンを含み、最低限の長さがある段落を取得
            if extract_date(text) != "不明" and len(text) > 50:
                temp_elements.append(p)
        
        news_elements = temp_elements
        if debug:
            logger.debug(f"日付を含む段落要素を {len(news_elements)} 個検出しました。")
    
    # ベースURLの取得
    parsed_url = urllib.parse.urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # 検出された要素からお知らせ情報を抽出
    for element in news_elements:
        # タイトル取得
        title_element = element.select_one('h1, h2, h3, h4, .title, [class*="title"]')
        title = title_element.get_text(strip=True) if title_element else element.get_text(strip=True)[:100]
        
        # 内容取得
        content = element.get_text(strip=True)
        
        # 日付取得
        date_element = element.select_one('time, .date, [class*="date"], .time, [class*="time"]')
        date_str = date_element.get_text(strip=True) if date_element else extract_date(content)
        
        # リンク取得
        link_element = element.select_one('a')
        link = urllib.parse.urljoin(base_url, link_element['href']) if link_element and 'href' in link_element.attrs else url
        
        # カテゴリを検出
        categories = detect_categories(title + ' ' + content)
        
        # 項目を追加
        item = {
            'title': title,
            'description': content,
            'link': link,
            'pubDate': date_str,
            'categories': categories,
            'guid': f"{link}#{title}"
        }
        
        items.append(item)
        if debug:
            logger.debug(f"アイテムを追加しました: {title} (日付: {date_str}, カテゴリ: {', '.join(categories)})")
    
    if not silent:
        logger.info(f"合計 {len(items)} 個のアイテムを取得しました。")
    
    return items