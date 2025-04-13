# ウェブページフィード抽出ツール

RSS/Atomフィードを提供していないウェブページからお知らせ情報を抽出し、RSSフィードとCSVとして出力するCLIツールです。

## 特徴

- 指定されたウェブページからお知らせ/ニュース情報を抽出
- 抽出した情報をRSS 2.0フィード形式に変換
- 日付範囲とカテゴリによるフィルタリングが可能
- RSSフィードファイルとCSVファイルの両方を出力
- コンテンツのキーワードに基づいて自動的にカテゴリを検出
- 差分モードをサポートし、前回実行時以降の新しい項目のみを抽出
- URLと現在の日付に基づいて自動的にファイル名を生成

## 要件

- Python 3.8以上
- 必要なパッケージ: requests, beautifulsoup4

## インストール方法

1. リポジトリをクローン:
```
git clone https://github.com/yourusername/get-info-from-no-feed-page.git
cd get-info-from-no-feed-page
```

2. 必要なパッケージをインストール:
```
pip install -r requirements.txt
```

## 使用方法

基本的な使用方法:
```
python src/main.py URL [オプション]
```

オプション:
- `--since YYYY-MM-DD`: この日付以降に公開された項目のみを抽出
- `--until YYYY-MM-DD`: この日付以前に公開された項目のみを抽出
- `--category CATEGORY`: 指定したカテゴリの項目のみを抽出
- `--feed-output PATH`: RSSフィードファイルの出力パスを指定 (デフォルト: URLと日付に基づいて自動生成)
- `--csv-output PATH`: CSVファイルの出力パスを指定 (デフォルト: URLと日付に基づいて自動生成)
- `--diff-mode`: 既存のフィードファイルに含まれる最新の日時以降の項目のみを抽出

## 使用例

Firebaseのリリースノートからフィードデータを抽出:
```
python src/main.py https://firebase.google.com/support/releases
```

2024年1月1日以降の重要な更新をフィルタリング:
```
python src/main.py https://firebase.google.com/support/releases --since 2024-01-01 --category Important
```

前回実行時以降の新しい項目のみを抽出:
```
python src/main.py https://firebase.google.com/support/releases --diff-mode
```

## 出力ファイル

デフォルトでは、ツールは2つの出力ファイルを生成します：
1. 抽出したすべての項目を含むRSSフィードファイル（XML形式）
2. 同じ項目を表形式で含むCSVファイル

デフォルトのファイル名はURLと現在の日付に基づいています（例：`firebase_google_com_support_releases_20250414.xml`とそれに対応する`.csv`ファイル）。

差分モードでは、既にファイルが存在する場合、ツールは連番を付加した新しいファイルを作成します（例：`firebase_google_com_support_releases_20250414_1.xml`）。

## 拡張方法

特定のウェブサイトのサポートを追加するには、`src/scrapers`ディレクトリに新しいPythonスクリプトを作成します。ファイル名は`ドメイン名.py`というパターンに従ってください（ドットはアンダースコアに置き換え）。

例えば、`example.com`のサポートを追加するには、`src/scrapers/example_com.py`というファイルを作成し、以下のキーを持つ辞書のリストを返す`scrape(url)`関数を実装します：
- `title`: お知らせのタイトル
- `description`: お知らせの内容
- `link`: お知らせのURL
- `pubDate`: 公開日
- `categories`: カテゴリのリスト
- `guid`: グローバルユニーク識別子