#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import datetime
import os
import importlib
import urllib.parse
from typing import Optional, List, Dict, Any

def parse_args():
    """コマンドライン引数を解析する"""
    parser = argparse.ArgumentParser(description='指定されたURLのWebページからお知らせ情報を取得し、フィードデータとCSVを出力します')
    parser.add_argument('url', help='スクレイピング対象のURL')
    parser.add_argument('--since', help='指定した日付以降の情報のみを抽出 (YYYY-MM-DD形式)')
    parser.add_argument('--until', help='指定した日付以前の情報のみを抽出 (YYYY-MM-DD形式)')
    parser.add_argument('--category', help='指定したカテゴリの情報のみを抽出')
    parser.add_argument('--feed-output', help='フィードデータの出力ファイルパス')
    parser.add_argument('--csv-output', help='CSVデータの出力ファイルパス')
    
    return parser.parse_args()

def get_scraper_module_name(url: str) -> str:
    """URLからスクレイパーのモジュール名を取得する"""
    parsed_url = urllib.parse.urlparse(url)
    hostname = parsed_url.netloc
    
    # ドメイン名をスネークケースに変換してモジュール名として使用
    module_name = hostname.replace('.', '_').replace('-', '_')
    return module_name

def filter_items(items: List[Dict[str, Any]], since: Optional[str], until: Optional[str], category: Optional[str]) -> List[Dict[str, Any]]:
    """フィルタ条件に基づいてアイテムをフィルタリングする"""
    filtered_items = []
    
    for item in items:
        # 日付フィルタリング
        include = True
        if 'pubDate' in item and item['pubDate']:
            item_date = item['pubDate']
            # datetimeオブジェクトに変換
            if isinstance(item_date, str):
                try:
                    item_date = datetime.datetime.strptime(item_date, '%a, %d %b %Y %H:%M:%S %z')
                except ValueError:
                    try:
                        item_date = datetime.datetime.strptime(item_date, '%Y-%m-%d')
                    except ValueError:
                        include = False
            
            if include and since:
                since_date = datetime.datetime.strptime(since, '%Y-%m-%d')
                if item_date.date() < since_date.date():
                    include = False
            
            if include and until:
                until_date = datetime.datetime.strptime(until, '%Y-%m-%d')
                if item_date.date() > until_date.date():
                    include = False
        
        # カテゴリフィルタリング
        if include and category and 'categories' in item:
            if category.lower() not in [c.lower() for c in item['categories']]:
                include = False
        
        if include:
            filtered_items.append(item)
    
    return filtered_items

def generate_rss(items: List[Dict[str, Any]], url: str, title: str = "お知らせフィード") -> str:
    """RSSフィードを生成する"""
    rss_template = f'''<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>{title}</title>
  <link>{url}</link>
  <description>お知らせ情報のフィード</description>
  <language>ja</language>
  <lastBuildDate>{datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>
'''
    
    for item in items:
        rss_item = '  <item>\n'
        if 'title' in item and item['title']:
            rss_item += f'    <title>{item["title"]}</title>\n'
        else:
            rss_item += '    <title>不明</title>\n'
        
        if 'link' in item and item['link']:
            rss_item += f'    <link>{item["link"]}</link>\n'
        
        if 'description' in item and item['description']:
            rss_item += f'    <description><![CDATA[{item["description"]}]]></description>\n'
        else:
            rss_item += '    <description>不明</description>\n'
        
        if 'pubDate' in item and item['pubDate']:
            if isinstance(item['pubDate'], datetime.datetime):
                rss_item += f'    <pubDate>{item["pubDate"].strftime("%a, %d %b %Y %H:%M:%S %z")}</pubDate>\n'
            else:
                rss_item += f'    <pubDate>{item["pubDate"]}</pubDate>\n'
        else:
            rss_item += '    <pubDate>不明</pubDate>\n'
        
        if 'categories' in item and item['categories']:
            for category in item['categories']:
                rss_item += f'    <category>{category}</category>\n'
        
        if 'guid' in item and item['guid']:
            rss_item += f'    <guid isPermaLink="false">{item["guid"]}</guid>\n'
        
        rss_item += '  </item>\n'
        rss_template += rss_item
    
    rss_template += '</channel>\n</rss>'
    return rss_template

def generate_csv(items: List[Dict[str, Any]]) -> str:
    """CSVデータを生成する"""
    csv_data = "Date,Title,Category,Description\n"
    
    for item in items:
        date = "不明"
        if 'pubDate' in item and item['pubDate']:
            if isinstance(item['pubDate'], datetime.datetime):
                date = item['pubDate'].strftime('%Y-%m-%d')
            else:
                date = item['pubDate']
        
        title = "不明"
        if 'title' in item and item['title']:
            title = item['title'].replace('"', '""')
        
        category = "不明"
        if 'categories' in item and item['categories']:
            category = ", ".join(item['categories']).replace('"', '""')
        
        description = "不明"
        if 'description' in item and item['description']:
            description = item['description'].replace('"', '""')
        
        csv_data += f'"{date}","{title}","{category}","{description}"\n'
    
    return csv_data

def main():
    args = parse_args()
    
    # URLからスクレイパーモジュール名を取得
    scraper_module_name = get_scraper_module_name(args.url)
    
    try:
        # スクレイパーモジュールを動的にインポート
        scraper_module = importlib.import_module(f'scrapers.{scraper_module_name}')
    except ImportError:
        # 特定のURLに対応するスクレイパーが見つからない場合は汎用スクレイパーを使用
        try:
            scraper_module = importlib.import_module('scrapers.generic')
        except ImportError:
            print(f"エラー: '{args.url}'に対応するスクレイパーが見つかりません。")
            return 1
    
    # スクレイピングを実行
    try:
        items = scraper_module.scrape(args.url)
    except Exception as e:
        print(f"スクレイピング中にエラーが発生しました: {e}")
        return 1
    
    # フィルタリング
    filtered_items = filter_items(
        items,
        args.since,
        args.until,
        args.category
    )
    
    # RSSフィードの生成
    rss_data = generate_rss(filtered_items, args.url)
    
    # CSVデータの生成
    csv_data = generate_csv(filtered_items)
    
    # デフォルトのファイル名
    feed_output = args.feed_output or "feed.xml"
    csv_output = args.csv_output or "data.csv"
    
    # ファイルに書き込み
    with open(feed_output, 'w', encoding='utf-8') as f:
        f.write(rss_data)
    print(f"フィードデータを '{feed_output}' に出力しました。")
    
    with open(csv_output, 'w', encoding='utf-8') as f:
        f.write(csv_data)
    print(f"CSVデータを '{csv_output}' に出力しました。")
    
    return 0

if __name__ == "__main__":
    exit(main())