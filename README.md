# Markdown to PDF Converter

MarkdownファイルをPDFに変換するPythonアプリケーション

## 概要

このツールは、MarkdownファイルをPDFに変換するためのアプリケーションです。コマンドライン（CLI）とグラフィカルユーザーインターフェース（GUI）の両方を提供し、高品質なPDF出力を実現します。

### 主な機能

- **高品質PDF生成**: SeleniumとChromeヘッドレスブラウザを使用した正確なHTML→PDF変換
- **2つのインターフェース**: CLI（`main.py`）とGUI（`gui.py`）の両方に対応
- **複数ファイル処理**: ディレクトリ内のすべてのMarkdownファイルを一括変換
- **PDFマージ**: 複数のPDFを1つのファイルに結合し、連続したページ番号を追加
- **カスタマイズ可能**: CSSスタイル、フォントサイズ、レイアウトの調整が可能
- **日本語対応**: 完全な日本語サポート

## 必要な環境

- Python 3.7以上
- Google Chrome ブラウザ
- ChromeDriver（自動でダウンロードされる場合があります）

## インストール

1. **リポジトリをクローンまたはダウンロード**:
```bash
git clone https://github.com/k-brahma/md2pdf-python.git
cd md2pdf-python
```

2. **必要なパッケージをインストール**:
```bash
pip install -r requirements.txt
```

3. **設定ファイルの準備**:
```bash
cp config/config_sample.py config/config.py
```

## 使用方法

### CLI（コマンドライン）

#### 基本的な使用方法

```bash
# 単一ファイルの変換
python main.py input.md output.pdf

# 出力ファイル名を省略（自動で.pdfが付与）
python main.py input.md
```

#### ディレクトリの一括処理

```bash
# ディレクトリ内のすべてのMarkdownファイルを変換
python main.py -d input_directory output_directory

# PDFをマージして1つのファイルに
python main.py -d input_directory -m -n merged_document

# コンパクトレイアウトで変換
python main.py -d input_directory --compact
```

#### カスタムスタイルの適用

```bash
# 特定のCSSファイルを適用
python main.py input.md --css css/simple.css css/prism.css

# フォントサイズを変更
python main.py input.md --font-size 14
```

### GUI（グラフィカルインターフェース）

```bash
python gui.py
```

GUIでは以下の操作が可能です：

1. **ファイル選択**: 単一ファイルまたは複数ファイルの選択
2. **出力先指定**: 出力ディレクトリの選択
3. **オプション設定**: 
   - CSSファイルの選択
   - コンパクトモード
   - フォントサイズ調整
   - PDFマージオプション
4. **リアルタイム進捗表示**: 変換状況とログの確認

## コマンドラインオプション

| オプション | 説明 |
|-----------|------|
| `input` | 入力Markdownファイルまたはディレクトリのパス |
| `output` | 出力PDFファイルまたはディレクトリのパス（省略可能） |
| `-d, --directory` | ディレクトリ内のすべてのMarkdownファイルを処理 |
| `-m, --merge` | 生成されたPDFを1つのファイルにマージ |
| `-n, --name` | マージされたPDFファイルの名前（-mオプション使用時必須） |
| `--css` | 適用するCSSファイル（複数指定可能） |
| `--compact` | より多くのコンテンツを1ページに収めるコンパクトレイアウト |
| `--font-size` | PDFの基本フォントサイズ（デフォルト: 16px） |
| `--no-headless` | ブラウザを表示モードで実行（デバッグ用） |

## 使用例

### 1. 単一ファイルの変換
```bash
python main.py README.md
# → README.pdf が生成される
```

### 2. カスタムスタイルでの変換
```bash
python main.py document.md --css css/simple.css --font-size 14
```

### 3. プロジェクト全体の変換とマージ
```bash
python main.py -d docs/ -m -n project_documentation --compact
```

### 4. GUI での使用
```bash
python gui.py
# → GUIが起動し、ファイル選択から変換まで視覚的に操作可能
```

## ファイル構成

```
├── main.py              # CLIインターフェース
├── gui.py               # GUIインターフェース  
├── core.py              # コア機能（変換ロジック）
├── requirements.txt     # 依存パッケージ
├── config/
│   ├── config.py        # 設定ファイル
│   └── config_sample.py # 設定ファイルサンプル
├── css/                 # CSSスタイルシート
│   ├── simple.css       # シンプルなスタイル
│   ├── prism.css        # コードハイライト用
│   ├── default.css      # デフォルトスタイル
│   └── pdf_styles.css   # PDF専用スタイル
└── templates/           # HTMLテンプレート
    └── default.html     # デフォルトHTMLテンプレート
```

## カスタマイズ

### CSSスタイルの追加

新しいCSSファイルを`css/`ディレクトリに追加して、`--css`オプションで指定できます。

### 設定の変更

`config/config.py`ファイルを編集することで、以下の設定を変更できます：

- Markdown拡張機能
- PDF出力設定
- デフォルトCSS
- フッター設定

## トラブルシューティング

### よくある問題

1. **ChromeDriverが見つからない**
   - Google Chromeが最新バージョンであることを確認
   - ChromeDriverが自動ダウンロードされない場合は手動でインストール

2. **日本語フォントが表示されない**
   - `css/pdf_styles.css`でフォント設定を調整

3. **変換が失敗する**
   - `--no-headless`オプションでブラウザを表示し、エラーを確認

### ログファイル

GUIモードでは`pdf_converter.log`にログが保存されます。問題が発生した場合はこのファイルを確認してください。

## クレジット

### CSSスタイルについて

- `css/simple.css`: Chrome Extension の Markdown Viewer の "SIMPLE" テーマにインスパイアされています
- `css/prism.css`: Chrome Extension の Markdown Viewer から借用したコードハイライト用CSSです

これらのスタイルファイルは、より良いPDF出力のために使用させていただいています。元の作成者に感謝いたします。

## ライセンス

このプロジェクトは [LICENSE] の下で公開されています。

**注意**: `css/simple.css` および `css/prism.css` については、それぞれ元のライセンス条項が適用される可能性があります。商用利用の際は元のソースのライセンスをご確認ください。

## 貢献

バグ報告や機能要望は、GitHubのIssueで受け付けています。プルリクエストも歓迎します。 