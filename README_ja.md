# Web Announcement Feed Generator Python

指定されたウェブサイトからお知らせ情報をスクレイピングし、RSSフィードファイルを生成して、フィルタ条件に一致する項目のCSV一覧を出力するコマンドラインツールです。

## 機能

- 指定されたURLのウェブページからお知らせ情報をスクレイピング
- お知らせデータをRSS 2.0形式のフィードに変換
- 指定された条件でフィルタリングされた項目をCSVファイルとして出力
- 差分モードによる増分更新をサポート
- SeleniumによるJavaScriptで遅延読み込みされるコンテンツにも対応
- 日付フィルタリング、カテゴリフィルタリング、カスタマイズ可能な出力ファイル名など

## 前提条件

- Ubuntu（最新LTSバージョン）
- Python 3（最新LTSバージョン）
- Chromeブラウザ
- 以下のPythonパッケージ（requirements.txtでインストール）：
  - beautifulsoup4
  - requests
  - selenium
  - webdriver-manager

## インストール

1. リポジトリをクローン：
   ```bash
   git clone https://github.com/username/web-announcement-feed-generator-python.git
   cd web-announcement-feed-generator-python
   ```

2. 必要なPythonパッケージをインストール：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

基本的な使用方法：

```bash
python src/main.py <url> [オプション]
```

### 引数

- `url`: スクレイピング対象のWebページのURL、または「all」を指定して全ての対象URLに対して実行

### オプション

- `--since YYYY-MM-DD`: 指定した日付以降の項目のみを処理
- `--until YYYY-MM-DD`: 指定した日付以前の項目のみを処理
- `--category TEXT`: 指定したカテゴリテキストを含む項目のみを処理
- `--exclude-category TEXT`: 指定したカテゴリテキストを含まない項目のみを処理
- `--feed-output PATH`: RSSフィード出力ファイルのカスタムパス
- `--csv-output PATH`: CSV出力ファイルのカスタムパス
- `--diff-mode`: 差分更新モード（既存のフィードより新しい項目のみを処理）
- `--with-date`: 出力ファイル名に現在の日付を追加
- `--debug`: 詳細なデバッグログの有効化
- `--silent`: すべての出力を抑制
- `--selenium-wait 秒数`: Seleniumの待機時間を上書き（読み込みが遅いページに有用）
- `--post-load-wait 秒数`: ページロード後の追加待機時間
- `--lambda-optimized`: Lambda最適化Chromeセッティングを有効化
- `--debug-selenium`: Seleniumの詳細ログを有効化

### 使用例

特定のURLをスクレイピング：
```bash
python src/main.py https://firebase.google.com/support/releases
```

対応するすべてのURLをスクレイピング：
```bash
python src/main.py all
```

日付範囲でフィルタリング：
```bash
python src/main.py https://firebase.google.com/support/releases --since 2025-01-01 --until 2025-03-31
```

カテゴリでフィルタリング：
```bash
python src/main.py https://firebase.google.com/support/releases --category important
```

差分モードを使用して新しい項目のみを処理：
```bash
python src/main.py https://firebase.google.com/support/releases --diff-mode
```

Lambda最適化モードをテスト（AWS Lambdaデプロイ用）：
```bash
python src/main.py https://ja.monaca.io/headline/ --lambda-optimized --selenium-wait 30
```

## AWS Lambda デプロイメント

このツールはAWS Lambdaデプロイメント用に最適化されています。詳細については[LAMBDA_FIX_DOCUMENTATION.md](LAMBDA_FIX_DOCUMENTATION.md)を参照してください：

- Lambda環境の自動検出
- Lambda用に最適化されたChrome設定
- 信頼性の高いスクレイピングのためのフォールバックメカニズム
- サイト固有の設定
- トラブルシューティングのヒント

## 対応サイト

現在、以下のウェブサイトに対応しています：

- Firebase リリースノート: https://firebase.google.com/support/releases
- Monaca ヘッドライン: https://ja.monaca.io/headline/

## 開発

### プロジェクト構造

```
.
├── LICENSE
├── README.md
├── README_ja.md
├── requirements.txt
└── src/
    ├── main.py
    └── scrapers/
        ├── __init__.py
        ├── firebase_google_com_support_releases.py
        ├── generic.py
        └── ja_monaca_io_headline.py
```

### 新しいウェブサイトの対応追加

新しいウェブサイトに対応するには：

1. `src/scrapers/`ディレクトリに新しいスクレイパーファイルを作成
   - ファイル名はURLに基づいて命名（例：`example_com_news.py`）
2. `scrape(url, debug=False, silent=False)`関数を実装：
   - URLを入力として受け取る
   - お知らせ項目のリストを辞書形式で返す
   - 各辞書には以下の要素を含める：
     - `title`: お知らせのタイトル
     - `description`: お知らせの内容
     - `link`: お知らせの詳細ページへのURL
     - `pubDate`: 公開日（RFC 822形式）
     - `categories`: カテゴリの文字列リスト
     - `guid`: 項目のグローバルに一意な識別子

### テスト

対応するすべてのURLに対してスクレイパーをテストしデバッグ：

```bash
python src/main.py all --debug
```

## ライセンス

MIT-0 ライセンス。詳細は[LICENSE](LICENSE)ファイルを参照してください。

Copyright (c) 2025 Tomoya Yamamoto