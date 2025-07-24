"""
PDF generation and manipulation functions
"""

import base64
import os
import tempfile
from io import BytesIO
from pathlib import Path

from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from config.config import PDF_CONFIG
from core.logger import logger


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