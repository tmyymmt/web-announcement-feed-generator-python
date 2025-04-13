#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
簡易テスト用スクリプト
依存関係に問題がある場合にも、最小限の機能でテストできるようにします。
"""

import sys
import json
import urllib.request
from urllib.error import URLError
import re
from datetime import datetime

def fetch_page(url):
    """URLからWebページの内容を取得する簡易関数"""
    print(f"取得中: {url}")
    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')
    except URLError as e:
        print(f"エラー: URLの取得に失敗しました - {e}")
        sys.exit(1)

def simple_extract_info(html_content, url):
    """
    HTMLコンテンツから基本的な情報を抽出する簡易版パーサー
    正規表現を使用して、一般的なパターンを検出します
    """
    # タイトルを抽出
    title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
    page_title = title_match.group(1) if title_match else "Unknown Page"
    
    print(f"ページタイトル: {page_title}")
    
    # お知らせアイテムを抽出（非常に簡易的なアプローチ）
    # 実際の実装では、BeautifulSoup等を使った詳細な解析が必要です
    announcements = []
    
    # h2/h3見出しとその周辺のp要素を検出
    heading_pattern = r'<h[23][^>]*>(.*?)</h[23]>'
    for heading_match in re.finditer(heading_pattern, html_content, re.IGNORECASE):
        heading_text = heading_match.group(1)
        # HTMLタグを除去
        heading_text = re.sub(r'<[^>]+>', '', heading_text).strip()
        
        # 見出しの位置を特定
        pos = heading_match.start()
        
        # 前後200文字を取得してp要素を探す
        content_range = html_content[max(0, pos-100):min(len(html_content), pos+500)]
        
        # 日付のパターンを探す (YYYY-MM-DD または YYYY/MM/DD または YYYY年MM月DD日)
        date_pattern = r'(20\d{2}[-/\.年]\s*\d{1,2}[-/\.月]\s*\d{1,2}日?)'
        date_match = re.search(date_pattern, content_range)
        date_str = date_match.group(1) if date_match else None
        
        # 内容を取得
        content_match = re.search(r'<p[^>]*>(.*?)</p>', content_range, re.IGNORECASE | re.DOTALL)
        content_text = content_match.group(1) if content_match else ""
        content_text = re.sub(r'<[^>]+>', '', content_text).strip()
        
        # お知らせアイテムを作成
        if heading_text and (date_str or content_text):
            announcements.append({
                'title': heading_text,
                'link': url,
                'date': date_str or datetime.now().strftime('%Y-%m-%d'),
                'content': content_text[:100] + '...' if len(content_text) > 100 else content_text
            })
    
    return announcements

def main():
    if len(sys.argv) < 2:
        print("使用方法: ./test_parser.py <URL>")
        sys.exit(1)
    
    url = sys.argv[1]
    html_content = fetch_page(url)
    announcements = simple_extract_info(html_content, url)
    
    if not announcements:
        print("お知らせ情報が見つかりませんでした。")
        sys.exit(1)
    
    print(f"合計 {len(announcements)} 件のお知らせを検出しました:")
    for i, item in enumerate(announcements, 1):
        print(f"\n{i}. {item['title']}")
        print(f"   日付: {item['date']}")
        print(f"   内容: {item['content']}")
    
    # 結果をJSONとして出力
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump(announcements, f, ensure_ascii=False, indent=2)
    
    print(f"\n結果は test_results.json に保存されました。")

if __name__ == '__main__':
    main()