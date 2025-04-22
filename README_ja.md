# Webお知らせフィード生成ツール

指定されたWebページからお知らせ情報をスクレイピングし、RSSフィードファイルを出力し、フィルタ条件に該当する項目のCSV一覧を生成するCLIツールです。

## 機能

- **RSSフィードが存在しないWebページからお知らせ情報を取得**
- **指定されたWebページにある情報のみを使用**
- お知らせの日付、タイトル、内容、カテゴリ情報を抽出
- JavaScriptの遅延読み込みにも対応（Seleniumを使用）
- RSS 2.0形式のフィードファイルとCSV一覧を出力
- 日付、カテゴリの含む/含まないによるフィルタリング
- 複数のウェブサイトに対応した専用スクレイパー
- 差分モードで新しい項目のみを処理

## 必要条件

- Ubuntu LTS（最新版）
- Python 3.x（最新LTS版）
- 必要なパッケージ（requirements.txtから自動的にインストール）:
  - requests
  - beautifulsoup4
  - selenium
  - webdriver-manager

## インストール

1. リポジトリをクローン
2. 必要なパッケージをインストール:

```sh
pip install -r requirements.txt
```

## 使い方

```
python src/main.py [URL] [オプション]
```

### 引数

- `URL`: スクレイピング対象のWebページURL、または「all」を指定して全ての対応URLをスクレイピング

### オプション

- `--since YYYY-MM-DD`: 指定した日付以降に公開された項目のみを含める
- `--until YYYY-MM-DD`: 指定した日付以前に公開された項目のみを含める
- `--category CATEGORY`: 指定したカテゴリを含む項目のみを含める
- `--exclude-category CATEGORY`: 指定したカテゴリを含む項目を除外する
- `--feed-output PATH`: RSSフィードファイルの出力パスを指定
- `--csv-output PATH`: CSVファイルの出力パスを指定
- `--diff-mode`: 既存のフィードファイルの最新項目よりも新しい項目のみを出力
- `--with-date`: 出力ファイル名に現在の日付を付加する (_YYYYMMDD形式)
- `--debug`: 詳細なデバッグ出力を有効にする

### コマンド例

```sh
# Firebaseのリリースページからお知らせをスクレイピング
python src/main.py https://firebase.google.com/support/releases

# サポートされている全てのウェブサイトをスクレイピング
python src/main.py all --with-date

# Firebaseの重要なお知らせのみを取得
python src/main.py https://firebase.google.com/support/releases --category important

# 非推奨(deprecated)以外の全てのお知らせを取得
python src/main.py https://firebase.google.com/support/releases --exclude-category deprecated

# 2025年1月1日以降に公開されたお知らせを取得
python src/main.py https://firebase.google.com/support/releases --since 2025-01-01

# 差分モード: 前回の実行以降の新しい項目のみを取得
python src/main.py https://firebase.google.com/support/releases --diff-mode
```

## 対応ウェブサイト

- Firebase リリースノート: https://firebase.google.com/support/releases
  - release-* クラス指定を持つお知らせを抽出
  - クラス名とコンテンツのキーワードに基づいてカテゴリ化
- Monaca ヘッドライン: https://ja.monaca.io/headline/
  - 日本語コンテンツに対応
  - headline-entryクラスからお知らせを抽出

## 実装の詳細

- URLごとにスクレイピングのコードは異なる実装になるため、URLごとに異なるスクレイピングのロジックのソースコードはファイルに分離
  - `src/scrapers/` ディレクトリ内にドメイン名とパスに基づくファイル名でスクレイパーを格納
  - ターゲットのURLごとに、適切なスクレイピングのロジックのソースコードが動的に実行される
  - スクレイパーのファイル名の命名規則：
    - URLのドメインとパスを元にする（例：firebase_google_com.py）
    - 全てのOSとURLで扱えるファイル名に変換（ドットをアンダースコアに置換など）
  - 未対応のURLには汎用スクレイパーを使用
- JavaScriptレンダリングコンテンツのためにはSeleniumをヘッドレスモードで使用
  - AWS Lambda環境では chrome-aws-lambda-layer を使用
- 最新のChromeのUser-Agentを使用
- CSV日付形式は「YYYY/MM/DD」
- デフォルトの出力ファイル名はURLに基づき、オプションで現在の日付を含む

## ライセンス

このプロジェクトはMIT-0ライセンスの下で公開されています - 詳細は[LICENSE](LICENSE)ファイルを参照してください。