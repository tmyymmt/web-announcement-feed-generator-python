# get-info-from-no-feed-page

Webページ上のお知らせ情報を抽出し、ATOMフィードとCSVファイルに変換するCLIツール

## 概要

このツールは、フィード機能を持たないWebページからお知らせ情報を抽出し、以下の形式で出力します：

1. **ATOMフィード** - Webページの全お知らせ情報をRSSリーダーで購読可能な形式に変換
2. **CSVエクスポート** - フィルタリング条件に基づいてお知らせ情報を表形式で出力

このツールは特に以下のような用途に適しています：
- 更新情報の定期的な監視
- 重要な通知（deprecated、important、shutdownなど）の抽出
- お知らせ情報の整理と分析

## インストール

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/get-info-from-no-feed-page.git
cd get-info-from-no-feed-page

# 依存パッケージのインストール
pip install -r requirements.txt
```

## 使い方

### 基本的な使用方法

```bash
# 基本的な使用方法（ATOMフィードとCSVの両方を生成）
python get_announcements.py --url https://example.com/announcements

# 出力ファイル名を指定
python get_announcements.py --url https://example.com/announcements --output-atom custom_feed.atom --output-csv custom_report.csv
```

### 詳細なオプション

```bash
# ヘルプを表示
python get_announcements.py --help

# 出力ファイル名を指定
python get_announcements.py --url https://example.com/announcements --output-atom custom_feed.atom --output-csv custom_report.csv

# 日付でフィルタリング
python get_announcements.py --url https://example.com/announcements --date-after 2024-01-01 --date-before 2024-12-31

# カテゴリでフィルタリング
python get_announcements.py --url https://example.com/announcements --category api --category feature
```

## 機能詳細

### お知らせ情報の検出

このツールは様々なWebページ構造に対応するため、複数のHTMLパターンを試行し、お知らせ情報を抽出します：

- 記事形式のコンテンツ
- リスト形式の更新情報
- テーブル形式の情報
- カードスタイルのコンテンツ

### 日付検出

日付情報は以下の方法で検出されます：

- 標準的な日付表記の解析
- 和暦形式（年月日）の解析
- さまざまな区切り文字（/、-、.）に対応

### カテゴリ検出

カテゴリ情報は以下の方法で検出されます：

- 明示的なカテゴリ/タグ要素の解析
- 重要なキーワード（deprecated、important、shutdown、end of life、eolなど）の自動検出
- 画像のalt属性からのキーワード（deprecated、important、shutdown）の検出

## 要件

- Ubuntu LTS最新版
- Python LTS最新版
- 依存パッケージ（requirements.txtに記載）:
  - requests
  - beautifulsoup4
  - python-dateutil
  - click

## ライセンス

[LICENSE](LICENSE)ファイルを参照してください。

## 更新履歴

- 2025-04-13: 初期バージョンリリース