#!/usr/bin/env python3
"""
Markdown to PDF converter core functionality
"""

import base64
import logging
import os
import tempfile
from io import BytesIO
from pathlib import Path

import markdown
from jinja2 import Template
from markdown.extensions import codehilite, fenced_code, tables, toc
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from config.config import (
    CODEHILITE_CONFIG,
    DEFAULT_CSS,
    DEFAULT_HTML_TEMPLATE,
    MARKDOWN_EXTENSIONS,
    PDF_CONFIG,
    load_css_file,
)

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ファイルハンドラの設定（gui.pyと同じファイルに出力）
log_file = Path('pdf_converter.log')
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# フォーマッタの設定
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# ハンドラの追加（重複を避けるために既存のハンドラを確認）
if not logger.handlers:
    logger.addHandler(file_handler)

def load_template_file(file_path):
    """テンプレートファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Template file not found: {file_path}")
        return ""

def markdown_to_html(md_content, css_files=None, compact=False, font_size=16):
    """MarkdownをHTMLに変換"""
    # Markdown拡張機能の設定
    extensions = ['tables', 'codehilite', 'fenced_code', 'toc']
    logger.debug(f"Using extensions: {extensions}")
    
    # 拡張機能の設定
    extension_configs = {
        'codehilite': {
            'use_pygments': True,
            'noclasses': True,
            'pygments_style': 'default',
            'linenums': False,
            'guess_lang': True
        }
    }
    
    md = markdown.Markdown(extensions=extensions, extension_configs=extension_configs)
    html_content = md.convert(md_content)
    
    # CSSファイルを読み込み
    css_content = ""
    if css_files:
        for css_file in css_files:
            css_content += load_css_file(css_file) + "\n"
    
    # CSSファイルが指定されていない場合、デフォルトでsimple.cssとprism.cssを試す
    if not css_content.strip():
        for default_css in ['css/simple.css', 'css/prism.css']:
            css_content += load_css_file(default_css) + "\n"
    
    # それでもCSSが見つからない場合のfallback
    if not css_content.strip():
        css_content = DEFAULT_CSS
    
    # PDF用のCSSテンプレートを読み込んで適用
    pdf_css_template = load_template_file('css/pdf_styles.css')
    if pdf_css_template:
        pdf_css = Template(pdf_css_template).render(
            compact=compact,
            margin="0.3in" if compact else "0.5in",
            base_font_size=font_size
        )
        css_content += pdf_css
    
    # HTMLテンプレートを読み込んで適用
    html_template = load_template_file('templates/default.html')
    if not html_template:
        html_template = DEFAULT_HTML_TEMPLATE
    
    return Template(html_template).render(
        css_content=css_content,
        html_content=html_content
    )

def create_driver(headless=True):
    """WebDriverを作成"""
    options = Options()
    if headless:
        options.add_argument('--headless=new')
    
    # ブラウザ表示を完全に抑制するための追加オプション
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=TranslateUI')
    options.add_argument('--disable-ipc-flooding-protection')
    options.add_argument('--disable-component-update')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-sync')
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--window-position=-2000,-2000')  # 画面外に配置
    options.add_argument('--force-device-scale-factor=1')
    
    # ブラウザUIを完全に無効化
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Chromeのバージョンとプラットフォームを指定
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # ログレベルを抑制
    options.add_argument('--log-level=3')
    options.add_argument('--silent')
    
    # Chromeのサービスを明示的に指定（ログを抑制）
    service = webdriver.chrome.service.Service()
    
    # Windowsでコンソールウィンドウを非表示にする
    try:
        import platform
        if platform.system() == 'Windows':
            service.creation_flags = 0x08000000
    except:
        pass
    
    return webdriver.Chrome(service=service, options=options)

def html_to_pdf(driver, html_content, pdf_path, source_dir=None):
    """HTMLをPDFに変換"""
    logger.debug(f"html_to_pdf開始: pdf_path={pdf_path}")
    
    try:
        # 一時HTMLファイルを作成（source_dirが指定されている場合はそこに作成）
        logger.debug("一時HTMLファイル作成開始")
        if source_dir and Path(source_dir).exists():
            # 元のMarkdownファイルと同じディレクトリに一時ファイルを作成
            # これにより相対パスの画像参照が正しく解決される
            temp_html_path = Path(source_dir) / f"temp_{os.getpid()}_{id(html_content)}.html"
            with open(temp_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.debug(f"一時HTMLファイル作成完了（元ディレクトリ内）: {temp_html_path}")
        else:
            # フォールバック：システムの一時ディレクトリを使用
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_html_path = f.name
            logger.debug(f"一時HTMLファイル作成完了（システムtemp）: {temp_html_path}")
        
        # HTMLを読み込み
        file_url = f"file://{os.path.abspath(temp_html_path)}"
        logger.debug(f"HTMLファイル読み込み開始: {file_url}")
        
        try:
            driver.get(file_url)
            logger.debug("HTMLファイル読み込み完了")
        except Exception as e:
            logger.error(f"HTMLファイル読み込みエラー: {str(e)}", exc_info=True)
            return False
        
        # ページの読み込み完了を待つ
        try:
            logger.debug("ページ読み込み待機開始")
            driver.implicitly_wait(3)
            logger.debug("ページ読み込み待機完了")
        except Exception as e:
            logger.error(f"ページ読み込み待機エラー: {str(e)}", exc_info=True)
            return False
        
        # PDF生成オプション（フッターなし）
        pdf_options = {
            'landscape': False,
            'displayHeaderFooter': False,
            'printBackground': True,
            'preferCSSPageSize': True,
            'paperWidth': 9.00,
            'paperHeight': 13.5,
            'marginTop': 0.4,
            'marginBottom': 0.4,
            'marginLeft': 0.2,
            'marginRight': 0.2,
        }
        logger.debug(f"PDF生成オプション: {pdf_options}")
        
        try:
            logger.debug("PDF生成開始（execute_cdp_cmd）")
            result = driver.execute_cdp_cmd('Page.printToPDF', pdf_options)
            logger.debug(f"PDF生成完了: データサイズ={len(result.get('data', ''))} bytes")
            pdf_data = base64.b64decode(result['data'])
            logger.debug(f"base64デコード完了: {len(pdf_data)} bytes")
        except Exception as e:
            logger.error(f"PDF生成エラー: {str(e)}", exc_info=True)
            return False
        
        try:
            logger.debug(f"PDFファイル書き込み開始: {pdf_path}")
            with open(pdf_path, 'wb') as f:
                f.write(pdf_data)
            logger.debug("PDFファイル書き込み完了")
        except Exception as e:
            logger.error(f"PDFファイル書き込みエラー: {str(e)}", exc_info=True)
            return False
            
        logger.info(f"PDF saved: {pdf_path}")
        return True
        
    except Exception as e:
        logger.error(f"html_to_pdf で予期せぬエラー: {str(e)}", exc_info=True)
        return False
    finally:
        # 一時ファイルを削除
        if 'temp_html_path' in locals():
            try:
                logger.debug(f"一時ファイル削除: {temp_html_path}")
                if isinstance(temp_html_path, Path):
                    temp_html_path.unlink(missing_ok=True)
                else:
                    os.unlink(temp_html_path)
                logger.debug("一時ファイル削除完了")
            except Exception as e:
                logger.warning(f"一時ファイル削除エラー: {str(e)}", exc_info=True)

def add_footer_to_pdf(input_pdf_path, output_pdf_path, footer_text=None, start_page_number=1):
    """PDFにフッターとページ番号を追加"""
    try:
        reader = PdfReader(input_pdf_path)
        writer = PdfWriter()
        
        if footer_text is None:
            footer_text = PDF_CONFIG['CREDIT_STRING']
        
        total_pages = len(reader.pages)
        
        for page_num, page in enumerate(reader.pages):
            # 新しいPDFキャンバスを作成してフッターを描画
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            
            # ページサイズを取得
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            
            # フッター全体のテキストを作成
            page_text = f"Page {start_page_number + page_num} of {total_pages}"
            full_footer = f"{footer_text} - {page_text}"
            
            # フッターテキストを中央に配置
            can.setFont(PDF_CONFIG['FOOTER_FONT'], PDF_CONFIG['FOOTER_FONT_SIZE'])
            text_width = can.stringWidth(full_footer, PDF_CONFIG['FOOTER_FONT'], PDF_CONFIG['FOOTER_FONT_SIZE'])
            x_position = (page_width - text_width) / 2
            can.drawString(x_position, PDF_CONFIG['FOOTER_MARGIN'] - 8, full_footer)
            
            can.save()
            packet.seek(0)
            
            # フッター付きのページを作成
            footer_pdf = PdfReader(packet)
            page.merge_page(footer_pdf.pages[0])
            writer.add_page(page)
        
        # 結果を保存
        with open(output_pdf_path, 'wb') as output_file:
            writer.write(output_file)
        
        logger.debug(f"Footer added to PDF: {output_pdf_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding footer to PDF: {e}")
        return False

def process_file(input_path, output_path, driver, css_files=None, compact=False, font_size=16):
    """個別のファイルを処理する関数"""
    logger.info(f"Converting: {input_path} -> {output_path}")
    
    # ファイル存在確認
    if not input_path.exists():
        error_msg = f"入力ファイルが存在しません: {input_path}"
        logger.error(error_msg)
        return False
    
    # 出力パスの処理
    output_path = Path(output_path)
    
    # 出力パスに拡張子がない場合、ディレクトリとして扱い、入力ファイル名を基に.pdf拡張子のファイル名を作成
    if not output_path.suffix:
        pdf_filename = input_path.stem + '.pdf'
        output_path = output_path / pdf_filename
    
    logger.debug(f"最終的な出力パス: {output_path}")
    
    # ファイル読み込み
    logger.debug(f"ファイル読み込み開始: {input_path}")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        logger.debug(f"ファイル読み込み完了: {len(md_content)} 文字")
    except Exception as e:
        error_msg = f"ファイル読み込みエラー: {input_path} - {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False
    
    # Markdown -> HTML 変換
    logger.debug("Markdown -> HTML 変換開始")
    try:
        html_content = markdown_to_html(md_content, css_files=css_files, 
                                      compact=compact, font_size=font_size)
        logger.debug(f"HTML変換完了: {len(html_content)} 文字")
    except Exception as e:
        error_msg = f"Markdown -> HTML 変換エラー: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False
    
    # 出力ディレクトリ作成
    if not output_path.parent.exists():
        logger.debug(f"出力ディレクトリ作成: {output_path.parent}")
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            error_msg = f"出力ディレクトリ作成エラー: {output_path.parent} - {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False
    
    # PDF生成
    logger.debug(f"PDF生成開始: {output_path}")
    try:
        # 元のMarkdownファイルのディレクトリを source_dir として渡す
        source_dir = input_path.parent
        result = html_to_pdf(driver, html_content, str(output_path), source_dir=str(source_dir))
        if result:
            logger.info(f"PDF生成成功: {output_path}")
            return True
        else:
            error_msg = f"PDF生成失敗: html_to_pdf が False を返しました"
            logger.error(error_msg)
            return False
    except Exception as e:
        error_msg = f"PDF生成中に予期せぬエラー: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False

def merge_pdfs(pdf_files, output_path):
    """複数のPDFファイルを1つにマージし、連続したページ番号を付ける"""
    try:
        # 一時的なマージファイルを作成
        temp_merged_path = output_path.with_suffix('.temp.pdf')
        
        merger = PdfMerger()
        
        for pdf_file in pdf_files:
            logger.debug(f"Adding PDF to merge: {pdf_file}")
            merger.append(str(pdf_file))
        
        # 一時的にマージしたPDFを保存
        merger.write(str(temp_merged_path))
        merger.close()
        
        # マージしたPDFに連続したページ番号でフッターを追加
        logger.info(f"Adding continuous page numbers to merged PDF...")
        if add_footer_to_pdf(temp_merged_path, output_path, start_page_number=1):
            # 一時ファイルを削除
            temp_merged_path.unlink()
            logger.info(f"✓ Merged PDF with page numbers saved: {output_path}")
            return True
        else:
            # フッター追加に失敗した場合は、一時ファイルを最終ファイルとして使用
            temp_merged_path.rename(output_path)
            logger.warning(f"✓ Merged PDF saved (without page numbers): {output_path}")
            return True
            
    except Exception as e:
        logger.error(f"Error merging PDFs: {e}")
        return False

def process_directory(input_dir, output_dir, driver, css_files=None, compact=False, font_size=16, merge=False, merge_name=None, selected_files=None):
    """ディレクトリ内のすべてのMarkdownファイルを処理"""
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # 選択されたファイルがある場合はそれを使用、ない場合はディレクトリ内のすべてのMarkdownファイルを処理
    if selected_files:
        md_files = selected_files
    else:
        md_files = list(input_dir.glob('**/*.md'))
    
    if not md_files:
        logger.warning(f"No Markdown files found in {input_dir}")
        return False
    
    success_count = 0
    generated_pdfs = []
    for md_file in md_files:
        # 出力パスを相対パスで計算
        rel_path = md_file.relative_to(input_dir)
        pdf_path = output_dir / rel_path.with_suffix('.pdf')
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        
        if process_file(md_file, pdf_path, driver, css_files, compact, font_size):
            success_count += 1
            generated_pdfs.append(pdf_path)
    
    logger.info(f"\nConversion completed: {success_count}/{len(md_files)} files converted successfully")
    
    # PDFのマージ処理
    if merge and success_count > 0:
        merged_pdf_path = output_dir / merge_name
        if not merged_pdf_path.suffix == '.pdf':
            merged_pdf_path = merged_pdf_path.with_suffix('.pdf')
        
        if merge_pdfs(generated_pdfs, merged_pdf_path):
            logger.info(f"✓ All PDFs merged into: {merged_pdf_path}")
        else:
            logger.error("✗ PDF merge failed!")
            return False
    
    return success_count == len(md_files) 