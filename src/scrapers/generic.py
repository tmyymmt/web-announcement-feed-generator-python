# -*- coding: utf-8 -*-

import re
import datetime
import requests
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import urllib.parse

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
        'maintenance': 'Maintenance'
    }
    
    text_lower = text.lower()
    
    for keyword, category in keywords.items():
        if keyword.lower() in text_lower:
            categories.append(category)
    
    # カテゴリが検出されなかった場合は「その他」を追加
    if not categories:
        categories.append('Other')
    
    return list(set(categories))  # 重複を削除

def scrape(url: str) -> List[Dict[str, Any]]:
    """汎用的なスクレイピング関数"""
    # URLからHTMLを取得
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    logger.debug(f"汎用スクレイパーを使用してURLにアクセス: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"URLへのアクセス中にエラーが発生しました: {e}")
        raise
    
    # HTMLをパース
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # お知らせの項目を格納するリスト
    items = []
    
    # 一般的なお知らせセクションのパターン
    # 1. ニュース/お知らせリスト
    news_elements = soup.select('article, .news-item, .notice, .announcement, .post, .entry, div[class*="news"], div[class*="notice"], div[class*="announcement"]')
    logger.debug(f"ニュース項目パターン1で検出した要素数: {len(news_elements)}")
    
    # 2. 日付とタイトルのペアを含む要素
    if not news_elements:
        news_elements = soup.select('ul li, div.row, div.list-item')
        logger.debug(f"ニュース項目パターン2で検出した要素数: {len(news_elements)}")
    
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
        logger.debug(f"ニュース項目パターン3で検出した要素数: {len(news_elements)}")
    
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
        
        logger.debug(f"検出したお知らせ項目: タイトル={title[:30]}..., 日付={date_str}, カテゴリ={categories}")
        
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
    
    logger.info(f"汎用スクレイパーで{len(items)}件のお知らせ項目を検出しました")
    return items