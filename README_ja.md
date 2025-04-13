# ウェブページフィード抽出ツール

RSS/Atomフィードを提供していないウェブページからお知らせ情報を抽出し、RSSフィードとCSVとして出力するCLIツールです。

## 特徴

- 指定されたウェブページからお知らせ/ニュース情報を抽出
- 抽出した情報をRSS 2.0フィード形式に変換
- 日付範囲とカテゴリによるフィルタリングが可能
- RSSフィードファイルとCSVファイルの両方を出力
- コンテンツのキーワードに基づいて自動的にカテゴリを検出

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
- `--feed-output PATH`: RSSフィードファイルの出力パスを指定 (デフォルト: feed.xml)
- `--csv-output PATH`: CSVファイルの出力パスを指定 (デフォルト: data.csv)

## 使用例

Firebaseのリリースノートからフィードデータを抽出:
```
python src/main.py https://firebase.google.com/support/releases
```

2024年1月1日以降の重要な更新をフィルタリング:
```
python src/main.py https://firebase.google.com/support/releases --since 2024-01-01 --category Important
```

## 拡張方法

特定のウェブサイトのサポートを追加するには、`src/scrapers`ディレクトリに新しいPythonスクリプトを作成します。ファイル名は`ドメイン名.py`というパターンに従ってください（ドットはアンダースコアに置き換え）。

例えば、`example.com`のサポートを追加するには、`src/scrapers/example_com.py`というファイルを作成し、以下のキーを持つ辞書のリストを返す`scrape(url)`関数を実装します：
- `title`: お知らせのタイトル
- `description`: お知らせの内容
- `link`: お知らせのURL
- `pubDate`: 公開日
- `categories`: カテゴリのリスト
- `guid`: グローバルユニーク識別子