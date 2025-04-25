#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import datetime
import os
import importlib
import urllib.parse
import xml.etree.ElementTree as ET
import re
from typing import Optional, List, Dict, Any

def parse_args():
    """コマンドライン引数を解析する"""
    parser = argparse.ArgumentParser(description='指定されたURLのWebページからお知らせ情報を取得し、フィードデータとCSVを出力します')
    parser.add_argument('url', help='スクレイピング対象のURL、または"all"を指定して全ての対象URLに対して実行')
    parser.add_argument('--since', help='指定した日付以降の情報のみを抽出 (YYYY-MM-DD形式)')
    parser.add_argument('--until', help='指定した日付以前の情報のみを抽出 (YYYY-MM-DD形式)')
    parser.add_argument('--category', help='指定したカテゴリを含む情報のみを抽出')
    parser.add_argument('--exclude-category', help='指定したカテゴリを含まない情報のみを抽出')
    parser.add_argument('--feed-output', help='フィードデータの出力ファイルパス')
    parser.add_argument('--csv-output', help='CSVデータの出力ファイルパス')
    parser.add_argument('--diff-mode', action='store_true', help='差分モード: 既存フィードデータの最新日時以降の項目のみを出力')
    parser.add_argument('--with-date', action='store_true', help='出力ファイル名に日付を付加する')
    parser.add_argument('--debug', action='store_true', help='デバッグモード: 詳細なログを出力')
    
    return parser.parse_args()

def get_scraper_module_name(url: str) -> str:
    """URLからスクレイパーのモジュール名を取得する"""
    parsed_url = urllib.parse.urlparse(url)
    hostname = parsed_url.netloc
    
    # ドメイン名をスネークケースに変換してモジュール名として使用
    module_name = hostname.replace('.', '_').replace('-', '_')
    return module_name

def filter_items(items: List[Dict[str, Any]], since: Optional[str], until: Optional[str], 
                category: Optional[str], exclude_category: Optional[str]) -> List[Dict[str, Any]]:
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
        
        # カテゴリを含むフィルタリング
        if include and category and 'categories' in item:
            if category.lower() not in [c.lower() for c in item['categories']]:
                include = False
        
        # カテゴリを除外するフィルタリング
        if include and exclude_category and 'categories' in item:
            if exclude_category.lower() in [c.lower() for c in item['categories']]:
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
                date = item['pubDate'].strftime('%Y/%m/%d')
            else:
                try:
                    # RFC822形式の日付文字列をパース
                    parsed_date = datetime.datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S %z')
                    date = parsed_date.strftime('%Y/%m/%d')
                except ValueError:
                    # 他の形式の場合はそのまま使用
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

def generate_default_filename(url: str, extension: str, with_date: bool = False) -> str:
    """URLと日付に基づくデフォルトのファイル名を生成する"""
    # URLの無効な文字を削除し、ファイル名に適した形式に変換
    parsed_url = urllib.parse.urlparse(url)
    hostname = parsed_url.netloc
    path = parsed_url.path.replace('/', '_')
    if path and path.startswith('_'):
        path = path[1:]
    if path and path.endswith('_'):
        path = path[:-1]
    
    # ファイル名の基本部分を作成
    base_name = f"{hostname}{('_' + path) if path else ''}"
    
    # ファイル名に無効な文字が含まれている場合は置換
    base_name = re.sub(r'[<>:"/\\|?*]', '_', base_name)
    
    # 現在の日付を追加
    today = datetime.datetime.now().strftime('%Y%m%d')
    
    # --with-dateオプションが指定された場合のみ日付を付加
    if with_date:
        return f"{base_name}_{today}.{extension}"
    else:
        return f"{base_name}.{extension}"

def get_next_available_filename(filename: str) -> str:
    """ファイル名が既に存在する場合、連番を付加した新しいファイル名を返す"""
    if not os.path.exists(filename):
        return filename
    
    base_name, extension = os.path.splitext(filename)
    counter = 1
    
    while True:
        new_filename = f"{base_name}_{counter}{extension}"
        if not os.path.exists(new_filename):
            return new_filename
        counter += 1

def get_latest_date_from_feed(feed_file: str) -> Optional[datetime.datetime]:
    """既存のフィードファイルから最新の日付を取得する"""
    if not os.path.exists(feed_file):
        return None
    
    try:
        tree = ET.parse(feed_file)
        root = tree.getroot()
        
        # すべてのitem要素を取得
        items = root.findall('.//item')
        
        # 日付を格納するリスト
        dates = []
        
        for item in items:
            pub_date = item.find('pubDate')
            if pub_date is not None and pub_date.text:
                try:
                    # RFC822形式の日付文字列をパース
                    date = datetime.datetime.strptime(pub_date.text, '%a, %d %b %Y %H:%M:%S %z')
                    dates.append(date)
                except ValueError:
                    pass
        
        # 日付が見つかった場合は最新の日付を返す
        if dates:
            return max(dates)
        
        return None
    except Exception as e:
        print(f"フィードファイルの解析中にエラーが発生しました: {e}")
        return None

def get_target_urls() -> List[str]:
    """サポートされている対象ページのURLリストを返す"""
    return [
        'https://firebase.google.com/support/releases',
        'https://ja.monaca.io/headline/'
    ]

def main():
    args = parse_args()
    
    # デバッグモードのログ設定
    debug = args.debug
    
    # 「all」が指定された場合は、全ての対象URLに対して実行
    if args.url.lower() == 'all':
        target_urls = get_target_urls()
        if debug:
            print(f"全対象URL ({len(target_urls)}件) に対して実行します")
    else:
        target_urls = [args.url]
    
    # 各URLに対して処理を実行
    for url in target_urls:
        if debug:
            print(f"\n=== URLの処理を開始: {url} ===")
        
        # URLからスクレイパーモジュール名を取得
        scraper_module_name = get_scraper_module_name(url)
        
        try:
            # スクレイパーモジュールを動的にインポート
            scraper_module = importlib.import_module(f'scrapers.{scraper_module_name}')
            if debug:
                print(f"スクレイパーモジュール '{scraper_module_name}' を読み込みました")
        except ImportError:
            # 特定のURLに対応するスクレイパーが見つからない場合は汎用スクレイパーを使用
            try:
                scraper_module = importlib.import_module('scrapers.generic')
                if debug:
                    print(f"'{url}'に対応するスクレイパーが見つからないため、汎用スクレイパーを使用します")
            except ImportError:
                print(f"エラー: '{url}'に対応するスクレイパーが見つかりません。")
                continue
        
        # スクレイピングを実行
        try:
            items = scraper_module.scrape(url)
            if debug:
                print(f"スクレイピングが完了しました。{len(items)}件のアイテムを取得しました")
        except Exception as e:
            print(f"スクレイピング中にエラーが発生しました: {e}")
            continue
        
        # デフォルトのファイル名を生成
        default_feed_output = generate_default_filename(url, "xml", args.with_date)
        default_csv_output = default_feed_output.replace(".xml", ".csv")
        
        # 出力ファイルのパスを決定
        feed_output = args.feed_output or default_feed_output
        csv_output = args.csv_output or default_csv_output
        
        # 複数URLの場合でユーザー指定の出力ファイル名がある場合、URLごとに異なるファイル名を生成
        if len(target_urls) > 1 and args.feed_output:
            base_name, extension = os.path.splitext(args.feed_output)
            parsed_url = urllib.parse.urlparse(url)
            hostname = parsed_url.netloc.replace('.', '_')
            feed_output = f"{base_name}_{hostname}{extension}"
            csv_output = feed_output.replace(extension, ".csv")
        
        # 差分モードの処理
        since_date = None
        if args.diff_mode:
            # 既存のフィードファイルが存在する場合
            if os.path.exists(feed_output):
                latest_date = get_latest_date_from_feed(feed_output)
                if latest_date:
                    # 最新の日付をフィルタの条件に設定
                    since_date = latest_date.strftime('%Y-%m-%d')
                    if debug:
                        print(f"差分モード: {since_date} 以降の項目のみを取得します")
                    
                    # 出力ファイル名を変更（重複しないようにする）
                    feed_output = get_next_available_filename(feed_output)
                    csv_output = feed_output.replace(".xml", ".csv")
        
        # フィルタリング
        filtered_items = filter_items(
            items,
            args.since or since_date,  # 差分モードの場合は最新日付を使用
            args.until,
            args.category,
            args.exclude_category
        )
        
        if debug:
            print(f"フィルタリング後のアイテム数: {len(filtered_items)}")
        
        # RSSフィードの生成
        rss_data = generate_rss(filtered_items, url)
        
        # CSVデータの生成
        csv_data = generate_csv(filtered_items)
        
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