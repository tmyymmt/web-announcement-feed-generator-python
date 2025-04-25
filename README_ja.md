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

- Node.js 14.0.0以上
- Chrome ブラウザ（Seleniumを使用します）

## 前提条件

- `package.json`の`dependencies`の`chromedriver`のバージョンと、Chromeのバージョンを合わせる必要があります
- 日本語フォントがインストールされていない場合は、日本語フォントをインストールして有効化する必要があります
- 必要に応じて`webdriver-manager start --detach`を実行してSeleniumの動作を確保してください

## 開発

### 開発環境のセットアップ

1. リポジトリをクローン：
```bash
git clone https://github.com/yourusername/web-announcement-feed-generator-python.git
cd web-announcement-feed-generator-python
```

2. 依存関係のインストール：
```bash
npm install
```

### ビルド方法

プロジェクトをビルドするには：
```bash
npm run build
```

これによりTypeScriptファイル(.ts)がJavaScriptファイル(.js)にコンパイルされます。コンパイル後のJavaScriptファイルは `dist` ディレクトリに出力されます。

### 開発中の実行方法

開発中にアプリケーションを実行する方法：
```bash
npm run dev -- <url> [options]
```

またはビルド後：
```bash
node dist/index.js <url> [options]
```

## インストール方法

### ローカルインストール

このツールは現在 npm レジストリには公開されていません。以下の方法でインストールしてください：

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/get-info-from-no-feed-page.git
cd get-info-from-no-feed-page

# 依存関係のインストール
npm install

# ビルド
npm run build

# ローカルでグローバルにインストール（開発中のパッケージをグローバルにリンク）
npm link
```

これにより `web-feed` コマンドがグローバルに使用できるようになります。

## 使用方法

### コマンドラインから実行

```bash
# グローバルインストール時
web-feed <url> [options]

# ローカルインストール時
npx web-feed <url> [options]
```

### 引数

- `<url>`: 対象WebページのURL。"all"を指定すると全てのサイトを処理

### オプション

- `-o, --output <path>`: 出力ファイルのパス
- `--with-date`: ファイル名に日付を付与する
- `-s, --start-date <date>`: 指定日以降のお知らせをフィルタ (YYYY-MM-DD)
- `-e, --end-date <date>`: 指定日以前のお知らせをフィルタ (YYYY-MM-DD)
- `-ic, --include-category <text>`: カテゴリが指定文字列を含むお知らせをフィルタ
- `-ec, --exclude-category <text>`: カテゴリが指定文字列を含まないお知らせをフィルタ
- `-d, --diff-mode`: 前回のフィード以降の差分のみを出力
- `--silent`: ログ出力を抑制
- `-h, --help`: ヘルプを表示
- `-V, --version`: バージョンを表示

## 使用例

### 特定のサイトのフィードを生成

```bash
web-feed https://ja.monaca.io/headline/ --with-date
```

### 全サイトのフィードを生成

```bash
web-feed all --with-date
```

### フィルタリング条件を指定してCSV出力

```bash
web-feed https://firebase.google.com/support/releases --start-date 2023-01-01 --include-category important
```

### 差分モードで実行

```bash
web-feed https://ja.monaca.io/headline/ -d
```

## 出力ファイル

プログラムは以下のファイルを出力します：

1. RSS 2.0形式のフィード (XMLファイル)
2. お知らせ一覧のCSVファイル

出力ファイル名は、デフォルトではWebページのドメインとパスに基づいて自動生成されます。
`--with-date`オプションを指定すると、ファイル名に日付が付与されます。

## ライセンス

このプロジェクトはMIT No Attribution License (MIT-0)の下でライセンスされています。詳細は[LICENSE](./LICENSE)ファイルをご参照ください。

MIT-0ライセンスでは、帰属表示の要件なしにソフトウェアの使用、コピー、変更、マージ、公開、配布、サブライセンス、および販売が許可されています。

## 問題点・改善点

- 新しいWebサイトへの対応を追加する場合は、`src/scrapers/`ディレクトリに新たなスクレイパークラスを作成し、`scraper-factory.ts`に登録する必要があります。
- ChromeDriverのバージョンとChromeブラウザのバージョンの不一致が発生した場合は、適切なバージョンのChromeDriverをインストールしてください。