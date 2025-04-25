# Web Announcement Feed Generator Python

指定したWebページからお知らせ情報をスクレイピングし、RSS 2.0形式のフィードとCSVファイルに変換するCLIツールです。

## 特徴

- 対応Webサイト：
  - Firebase リリースページ (`https://firebase.google.com/support/releases`)
  - Monaca お知らせページ (`https://ja.monaca.io/headline/`)
- RSS 2.0形式のフィード生成
- お知らせ情報のCSVエクスポート
- 日付範囲によるフィルタリング
- カテゴリによるフィルタリング
- 前回のフィード以降の差分のみを抽出する機能

## 必要条件

- Python 3.x
- Chrome ブラウザ（Seleniumを使用します）
- 必要なパッケージ:
  - requests
  - beautifulsoup4

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

- `<url>`: 対象WebページのURL。"all"を指定すると全てのサイトを処理

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

## ライセンス

詳細は[LICENSE](LICENSE)ファイルを参照してください。
