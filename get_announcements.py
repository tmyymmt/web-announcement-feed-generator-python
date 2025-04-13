#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import csv
import logging
import datetime
import re
import xml.dom.minidom
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
from typing import List, Dict, Optional, Tuple, Any

# 依存関係のインポート（存在しない場合は例外を捕捉する）
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    import urllib.request
    from urllib.error import URLError

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False

try:
    import click
    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False

try:
    from dateutil import parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AnnouncementItem:
    """お知らせ項目を表すクラス"""
    
    def __init__(self, title: str, link: str, content: str, published_date: datetime.datetime, 
                 categories: List[str] = None, updated_date: datetime.datetime = None):
        self.title = title
        self.link = link
        self.content = content
        self.published_date = published_date
        self.updated_date = updated_date or published_date
        self.categories = categories or []
    
    def __str__(self) -> str:
        return f"{self.published_date.strftime('%Y-%m-%d')} - {self.title}"
    
    def to_dict(self) -> Dict[str, Any]:
        """CSVレコード用の辞書を返す"""
        return {
            'title': self.title,
            'link': self.link,
            'published_date': self.published_date.strftime('%Y-%m-%d'),
            'updated_date': self.updated_date.strftime('%Y-%m-%d') if self.updated_date else '',
            'categories': ', '.join(self.categories),
            'content': self.content
        }


class WebPageParser:
    """Webページを解析してお知らせ情報を抽出するクラス"""
    
    def __init__(self, url: str):
        self.url = url
        self.page_title = ""
        self.page_description = ""
    
    def fetch_page(self) -> str:
        """URLからWebページを取得する"""
        try:
            if REQUESTS_AVAILABLE:
                logger.info(f"Fetching page from {self.url} using requests")
                response = requests.get(self.url, timeout=30)
                response.raise_for_status()
                return response.text
            else:
                logger.info(f"Fetching page from {self.url} using urllib")
                with urllib.request.urlopen(self.url) as response:
                    return response.read().decode('utf-8')
        except Exception as e:
            logger.error(f"Error fetching URL {self.url}: {e}")
            raise
    
    def parse_announcements(self) -> List[AnnouncementItem]:
        """Webページからお知らせ情報を抽出する"""
        html_content = self.fetch_page()
        
        # 依存関係に応じて解析方法を選択
        if BEAUTIFULSOUP_AVAILABLE:
            return self._parse_with_beautifulsoup(html_content)
        else:
            # BeautifulSoupが利用できない場合は正規表現による簡易パースを実行
            logger.warning("BeautifulSoup is not available. Using regex-based parsing instead.")
            return self._parse_with_regex(html_content)
    
    def _parse_with_beautifulsoup(self, html_content: str) -> List[AnnouncementItem]:
        """BeautifulSoupを使用したHTMLパース（高機能版）"""
        # lxmlの代わりにhtml.parserを使用
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # ページのタイトルと説明を取得
        self.page_title = soup.title.string.strip() if soup.title else "Unknown Page"
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        self.page_description = meta_desc.get('content', '') if meta_desc else ""
        
        # お知らせ情報の抽出方法はページ構造に依存します
        # 以下は一般的なパターンの例ですが、実際のWebページに合わせて調整が必要です
        
        announcements = []
        # 典型的なお知らせリスト（例：ブログ記事、リリースノートなど）の検出
        # 複数のパターンを試す
        announcement_patterns = [
            # パターン1: 日付と見出しを含む記事リスト
            {'container': 'article', 'date': 'time', 'title': 'h2,h3', 'content': 'p,div.content'},
            # パターン2: リストベースの更新情報
            {'container': 'div.release,div.announcement,li.release-item', 'date': 'time,span.date', 'title': 'h3,h4,strong', 'content': 'p,div.description'},
            # パターン3: テーブルベースの情報
            {'container': 'tr', 'date': 'td:first-child', 'title': 'td h3,td strong', 'content': 'td p'},
            # パターン4: カードスタイルのコンテンツ
            {'container': 'div.card,div.release-card', 'date': 'span.date,div.date', 'title': 'h3,div.title', 'content': 'div.content,p'},
        ]
        
        for pattern in announcement_patterns:
            containers = soup.select(pattern['container'])
            if containers:
                for container in containers:
                    try:
                        # 日付要素を探す
                        date_elem = container.select_one(pattern['date'])
                        published_date = None
                        
                        if date_elem:
                            date_text = date_elem.get_text().strip()
                            # 日付フォーマットを解析
                            try:
                                if DATEUTIL_AVAILABLE:
                                    published_date = parser.parse(date_text, fuzzy=True)
                                else:
                                    # dateutil.parserがない場合は正規表現で日付を抽出
                                    published_date = self._parse_date_with_regex(date_text)
                            except ValueError:
                                # 日付フォーマットが認識できない場合は正規表現で試みる
                                published_date = self._parse_date_with_regex(date_text)
                        
                        # 日付が見つからない場合はスキップ
                        if not published_date:
                            continue
                        
                        # タイトル要素を探す
                        title_elem = container.select_one(pattern['title'])
                        title = title_elem.get_text().strip() if title_elem else "不明"
                        
                        # リンクを探す
                        link_elem = title_elem.find_parent('a') if title_elem else None
                        if not link_elem:
                            link_elem = container.find('a')
                        
                        link = urljoin(self.url, link_elem['href']) if link_elem and 'href' in link_elem.attrs else self.url
                        
                        # コンテンツを探す
                        content_elem = container.select_one(pattern['content'])
                        content = content_elem.get_text().strip() if content_elem else "不明"
                        
                        # カテゴリ情報を探す（様々なパターン）
                        categories = []
                        category_elements = container.select('span.category,span.tag,div.category,a.category')
                        for cat_elem in category_elements:
                            cat_text = cat_elem.get_text().strip().lower()
                            if cat_text:
                                categories.append(cat_text)
                        
                        # 画像のalt属性からキーワードを検出
                        img_elements = container.find_all('img')
                        for img in img_elements:
                            alt_text = img.get('alt', '').lower()
                            for keyword in ['deprecated', 'important', 'shutdown']:
                                if keyword in alt_text and keyword not in categories:
                                    categories.append(keyword)
                        
                        # deprecated, important, shutdown関連のキーワードを検出
                        for keyword in ['deprecated', 'deprecation', 'important', 'critical', 'shutdown', 'end of life', 'eol']:
                            if keyword in title.lower() or keyword in content.lower():
                                if keyword not in categories:
                                    categories.append(keyword)
                        
                        # お知らせアイテムを作成
                        announcement = AnnouncementItem(
                            title=title,
                            link=link,
                            content=content,
                            published_date=published_date,
                            categories=categories
                        )
                        announcements.append(announcement)
                    except Exception as e:
                        logger.warning(f"Failed to parse announcement: {e}")
                
                # パターンが成功したらループを抜ける
                if announcements:
                    break
        
        if not announcements:
            logger.warning(f"No announcements found on {self.url}")
        
        return announcements
    
    def _parse_with_regex(self, html_content: str) -> List[AnnouncementItem]:
        """正規表現を使用したHTMLパース（簡易版）"""
        logger.info("Using regex-based parser to extract announcements")
        
        # タイトルを抽出
        title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
        self.page_title = title_match.group(1) if title_match else "Unknown Page"
        
        # メタディスクリプションを抽出
        meta_desc_match = re.search(r'<meta\s+name=["\'"]description["\'"][^>]*content=["\'](.*?)["\'][^>]*>', html_content, re.IGNORECASE)
        self.page_description = meta_desc_match.group(1) if meta_desc_match else ""
        
        # お知らせアイテムを抽出
        announcements = []
        
        # h2/h3見出しとその周辺のp要素を検出
        heading_pattern = r'<h[23][^>]*>(.*?)</h[23]>'
        for heading_match in re.finditer(heading_pattern, html_content, re.IGNORECASE):
            heading_text = heading_match.group(1)
            # HTMLタグを除去
            heading_text = re.sub(r'<[^>]+>', '', heading_text).strip()
            
            # 見出しの位置を特定
            pos = heading_match.start()
            
            # 前後500文字を取得してp要素を探す
            content_range = html_content[max(0, pos-200):min(len(html_content), pos+500)]
            
            # 日付のパターンを探す (YYYY-MM-DD または YYYY/MM/DD または YYYY年MM月DD日)
            date_pattern = r'(20\d{2}[-/\.年]\s*\d{1,2}[-/\.月]\s*\d{1,2}日?)'
            date_match = re.search(date_pattern, content_range)
            date_str = date_match.group(1) if date_match else None
            
            # 日付文字列からdatetimeオブジェクトを作成
            published_date = None
            if date_str:
                published_date = self._parse_date_with_regex(date_str)
            else:
                # 日付が見つからない場合は現在日付を使用
                published_date = None
            
            # 内容を取得
            content_match = re.search(r'<p[^>]*>(.*?)</p>', content_range, re.IGNORECASE | re.DOTALL)
            content_text = content_match.group(1) if content_match else ""
            content_text = re.sub(r'<[^>]+>', '', content_text).strip()
            
            # カテゴリ情報を探す
            categories = []
            category_pattern = r'<span[^>]*class=["\'](category|tag)["\'][^>]*>(.*?)</span>'
            for cat_match in re.finditer(category_pattern, content_range, re.IGNORECASE):
                cat_text = cat_match.group(2)
                cat_text = re.sub(r'<[^>]+>', '', cat_text).strip().lower()
                if cat_text and cat_text not in categories:
                    categories.append(cat_text)
            
            # 画像のalt属性からキーワードを検出
            img_pattern = r'<img[^>]*alt=["\']([^"\']*)["\'][^>]*>'
            for img_match in re.finditer(img_pattern, content_range, re.IGNORECASE):
                alt_text = img_match.group(1).lower()
                for keyword in ['deprecated', 'important', 'shutdown']:
                    if keyword in alt_text and keyword not in categories:
                        categories.append(keyword)
            
            # deprecated, important, shutdown関連のキーワードを検出
            for keyword in ['deprecated', 'deprecation', 'important', 'critical', 'shutdown', 'end of life', 'eol']:
                if (heading_text and keyword in heading_text.lower()) or (content_text and keyword in content_text.lower()):
                    if keyword not in categories:
                        categories.append(keyword)
            
            # お知らせアイテムを作成
            if heading_text:
                announcement = AnnouncementItem(
                    title=heading_text,
                    link=self.url,
                    content=content_text if content_text else "不明",
                    published_date=published_date if published_date else datetime.datetime.now(),
                    categories=categories
                )
                announcements.append(announcement)
        
        # 追加の抽出方法: 日付とタイトルの組み合わせがあるリスト項目などを検出
        list_item_pattern = r'<li[^>]*>.*?(20\d{2}[-/\.年]\s*\d{1,2}[-/\.月]\s*\d{1,2}日?).*?<(strong|b|span)[^>]*>(.*?)</(strong|b|span)>.*?</li>'
        for item_match in re.finditer(list_item_pattern, html_content, re.IGNORECASE | re.DOTALL):
            date_str = item_match.group(1)
            title_text = item_match.group(3)
            title_text = re.sub(r'<[^>]+>', '', title_text).strip()
            
            # 日付文字列からdatetimeオブジェクトを作成
            published_date = self._parse_date_with_regex(date_str)
            
            # 内容は同じli要素内のp要素から取得
            li_content = item_match.group(0)
            content_match = re.search(r'<p[^>]*>(.*?)</p>', li_content, re.IGNORECASE | re.DOTALL)
            content_text = content_match.group(1) if content_match else ""
            content_text = re.sub(r'<[^>]+>', '', content_text).strip()
            
            if title_text and published_date:
                announcement = AnnouncementItem(
                    title=title_text,
                    link=self.url,
                    content=content_text if content_text else "不明",
                    published_date=published_date,
                    categories=[]
                )
                announcements.append(announcement)
        
        if not announcements:
            logger.warning(f"No announcements found on {self.url} using regex parser")
        
        return announcements
    
    def _parse_date_with_regex(self, date_str: str) -> datetime.datetime:
        """正規表現を使用して日付文字列をパースする"""
        try:
            if DATEUTIL_AVAILABLE:
                return parser.parse(date_str, fuzzy=True)
            
            # 年/月/日パターンを解析
            date_match = re.search(r'(20\d{2})[-/\.年]?\s*(\d{1,2})[-/\.月]?\s*(\d{1,2})日?', date_str)
            if date_match:
                year = int(date_match.group(1))
                month = int(date_match.group(2))
                day = int(date_match.group(3))
                return datetime.datetime(year, month, day)
            
            # 現在の年＋月/日パターン
            date_match = re.search(r'(\d{1,2})[-/\.月]\s*(\d{1,2})日?', date_str)
            if date_match:
                year = datetime.datetime.now().year
                month = int(date_match.group(1))
                day = int(date_match.group(2))
                return datetime.datetime(year, month, day)
            
            # どのパターンにも一致しない場合は現在の日付を返す
            return datetime.datetime.now()
        except (ValueError, AttributeError):
            return datetime.datetime.now()


class SimpleAtomFeedCreator:
    """お知らせ情報からATOMフィードを生成するクラス（標準ライブラリのみを使用）"""
    
    ATOM_NS = "http://www.w3.org/2005/Atom"
    
    def __init__(self, url: str, title: str, description: str):
        self.url = url
        self.title = title
        self.description = description
        self.root = self._create_feed_element()
    
    def _create_feed_element(self) -> ET.Element:
        """ATOMフィードのルート要素を作成する"""
        ET.register_namespace('', self.ATOM_NS)
        
        feed = ET.Element("{%s}feed" % self.ATOM_NS)
        
        # 必須要素
        id_elem = ET.SubElement(feed, "{%s}id" % self.ATOM_NS)
        id_elem.text = self.url
        
        title_elem = ET.SubElement(feed, "{%s}title" % self.ATOM_NS)
        title_elem.text = self.title
        
        # オプション要素
        subtitle = ET.SubElement(feed, "{%s}subtitle" % self.ATOM_NS)
        subtitle.text = self.description
        
        updated = ET.SubElement(feed, "{%s}updated" % self.ATOM_NS)
        updated.text = datetime.datetime.now().isoformat()
        
        author = ET.SubElement(feed, "{%s}author" % self.ATOM_NS)
        author_name = ET.SubElement(author, "{%s}name" % self.ATOM_NS)
        author_name.text = "Feed Generator"
        
        link = ET.SubElement(feed, "{%s}link" % self.ATOM_NS)
        link.set("href", self.url)
        link.set("rel", "alternate")
        
        return feed
    
    def add_entries(self, announcements: List[AnnouncementItem]) -> None:
        """お知らせアイテムをフィードに追加する"""
        for item in announcements:
            entry = ET.SubElement(self.root, "{%s}entry" % self.ATOM_NS)
            
            # 必須要素
            id_elem = ET.SubElement(entry, "{%s}id" % self.ATOM_NS)
            id_elem.text = item.link
            
            title_elem = ET.SubElement(entry, "{%s}title" % self.ATOM_NS)
            title_elem.text = item.title
            
            updated_elem = ET.SubElement(entry, "{%s}updated" % self.ATOM_NS)
            updated_elem.text = item.updated_date.isoformat()
            
            # オプション要素
            link_elem = ET.SubElement(entry, "{%s}link" % self.ATOM_NS)
            link_elem.set("href", item.link)
            
            published_elem = ET.SubElement(entry, "{%s}published" % self.ATOM_NS)
            published_elem.text = item.published_date.isoformat()
            
            content_elem = ET.SubElement(entry, "{%s}content" % self.ATOM_NS)
            content_elem.set("type", "text")
            content_elem.text = item.content
            
            # カテゴリの追加
            for category in item.categories:
                category_elem = ET.SubElement(entry, "{%s}category" % self.ATOM_NS)
                category_elem.set("term", category)
    
    def write_atom(self, output_path: str) -> None:
        """ATOMフィードをファイルに書き込む"""
        # XMLの整形
        xml_str = ET.tostring(self.root, encoding="utf-8")
        dom = xml.dom.minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8")
        
        with open(output_path, "wb") as f:
            f.write(pretty_xml)
        
        logger.info(f"ATOM feed written to {output_path}")


class CSVExporter:
    """お知らせ情報をCSVファイルにエクスポートするクラス"""
    
    @staticmethod
    def export(announcements: List[AnnouncementItem], output_path: str) -> None:
        """お知らせアイテムをCSVファイルに出力する"""
        if not announcements:
            logger.warning(f"No announcements to export to {output_path}")
            return
        
        fieldnames = ['title', 'link', 'published_date', 'updated_date', 'categories', 'content']
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for item in announcements:
                    writer.writerow(item.to_dict())
            
            logger.info(f"CSV exported to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting CSV to {output_path}: {e}")
            raise


def filter_announcements(announcements: List[AnnouncementItem], 
                         date_after: Optional[datetime.datetime] = None,
                         date_before: Optional[datetime.datetime] = None,
                         categories: Optional[List[str]] = None) -> List[AnnouncementItem]:
    """お知らせアイテムをフィルタリングする"""
    filtered = []
    
    for item in announcements:
        # 日付フィルタ
        if date_after and item.published_date < date_after:
            continue
        
        if date_before and item.published_date > date_before:
            continue
        
        # カテゴリフィルタ
        if categories and not any(c.lower() in [cat.lower() for cat in item.categories] for c in categories):
            continue
        
        filtered.append(item)
    
    return filtered


def main_with_args(url: str, output_atom: str = 'feed.atom', output_csv: str = 'announcements.csv',
                  date_after: Optional[datetime.datetime] = None, date_before: Optional[datetime.datetime] = None,
                  category: Optional[List[str]] = None) -> int:
    """
    メイン処理（click依存なし）
    指定されたURLのWebページからお知らせ情報を抽出し、
    ATOMフィードとCSVファイルを生成します。
    """
    try:
        # Webページの解析
        parser = WebPageParser(url)
        announcements = parser.parse_announcements()
        
        if not announcements:
            logger.error("ページからお知らせ情報を抽出できませんでした。")
            return 1
        
        # ATOMフィードの生成（標準ライブラリのみ使用）
        feed_gen = SimpleAtomFeedCreator(url, parser.page_title, parser.page_description)
        feed_gen.add_entries(announcements)
        feed_gen.write_atom(output_atom)
        
        # フィルタリング
        filtered_announcements = filter_announcements(
            announcements, 
            date_after, 
            date_before, 
            category
        )
        
        # CSVの出力
        CSVExporter.export(filtered_announcements, output_csv)
        
        logger.info(f"処理が完了しました。合計 {len(announcements)} 件のお知らせから {len(filtered_announcements)} 件が出力されました。")
        
        return 0
    
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        return 1


if CLICK_AVAILABLE:
    @click.command()
    @click.option('--url', help='ウェブページのURL', required=True)
    @click.option('--output-atom', help='ATOMフィードの出力ファイルパス', default='feed.atom')
    @click.option('--output-csv', help='CSVの出力ファイルパス', default='announcements.csv')
    @click.option('--date-after', help='指定日付以降の項目をフィルタ (YYYY-MM-DD)', type=click.DateTime(formats=['%Y-%m-%d']))
    @click.option('--date-before', help='指定日付以前の項目をフィルタ (YYYY-MM-DD)', type=click.DateTime(formats=['%Y-%m-%d']))
    @click.option('--category', help='特定のカテゴリをフィルタ (複数指定可)', multiple=True)
    def main(url: str, output_atom: str, output_csv: str, 
            date_after: Optional[datetime.datetime], date_before: Optional[datetime.datetime],
            category: Optional[List[str]]) -> None:
        """
        指定されたURLのWebページからお知らせ情報を抽出し、
        ATOMフィードとCSVファイルを生成します。
        """
        sys.exit(main_with_args(url, output_atom, output_csv, date_after, date_before, category))
else:
    def main():
        """
        click非依存版のメイン関数
        コマンドライン引数を直接パースします
        """
        import argparse
        
        parser = argparse.ArgumentParser(
            description='指定されたURLのWebページからお知らせ情報を抽出し、ATOMフィードとCSVファイルを生成します。'
        )
        parser.add_argument('--url', required=True, help='ウェブページのURL')
        parser.add_argument('--output-atom', default='feed.atom', help='ATOMフィードの出力ファイルパス')
        parser.add_argument('--output-csv', default='announcements.csv', help='CSVの出力ファイルパス')
        parser.add_argument('--date-after', help='指定日付以降の項目をフィルタ (YYYY-MM-DD)')
        parser.add_argument('--date-before', help='指定日付以前の項目をフィルタ (YYYY-MM-DD)')
        parser.add_argument('--category', nargs='*', help='特定のカテゴリをフィルタ (複数指定可)')
        
        args = parser.parse_args()
        
        # 日付文字列をdatetimeオブジェクトに変換
        date_after = None
        if args.date_after:
            try:
                date_after = datetime.datetime.strptime(args.date_after, '%Y-%m-%d')
            except ValueError:
                logger.error(f"日付形式が不正です: {args.date_after}、YYYY-MM-DDで指定してください")
                sys.exit(1)
        
        date_before = None
        if args.date_before:
            try:
                date_before = datetime.datetime.strptime(args.date_before, '%Y-%m-%d')
            except ValueError:
                logger.error(f"日付形式が不正です: {args.date_before}、YYYY-MM-DDで指定してください")
                sys.exit(1)
        
        sys.exit(main_with_args(
            args.url, 
            args.output_atom, 
            args.output_csv, 
            date_after, 
            date_before, 
            args.category
        ))


if __name__ == '__main__':
    main()