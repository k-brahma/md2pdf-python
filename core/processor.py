"""
File and directory processing functionality
"""

import os
import time
import uuid
from pathlib import Path

from PyPDF2 import PdfReader

from .converter import markdown_to_html
from .logger import logger
from .pdf import html_to_pdf, merge_pdfs


def process_file(input_path, output_path, driver, css_files=None, template_file=None, compact=False, font_size=16):
    """個別のファイルを処理する関数"""
    started_at = time.monotonic()
    input_path = Path(input_path).resolve()
    logger.info("START input=%s output=%s", input_path, Path(output_path).resolve())
    
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
                                      template_file=template_file,
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
    
    # 同じディレクトリの一時ファイルへ生成し、成功後に既存PDFと置き換える。
    # 変換に失敗しても、以前のPDFは失われない。
    temp_pdf_path = output_path.with_name(
        f".{output_path.stem}.{uuid.uuid4().hex}.tmp.pdf"
    )
    logger.debug("PDF生成開始: temporary=%s final=%s", temp_pdf_path, output_path)
    try:
        # 元のMarkdownファイルのディレクトリを source_dir として渡す
        source_dir = input_path.parent
        result = html_to_pdf(
            driver,
            html_content,
            str(temp_pdf_path),
            source_dir=str(source_dir),
        )
        if not result:
            logger.error("PDF生成失敗: html_to_pdf が False を返しました input=%s", input_path)
            return False

        if not temp_pdf_path.exists() or temp_pdf_path.stat().st_size == 0:
            logger.error("PDF検証失敗: 一時PDFが存在しないか空です: %s", temp_pdf_path)
            return False

        try:
            page_count = len(PdfReader(temp_pdf_path).pages)
        except Exception:
            logger.error("PDF検証失敗: PDFを読み込めません: %s", temp_pdf_path, exc_info=True)
            return False

        if page_count == 0:
            logger.error("PDF検証失敗: ページがありません: %s", temp_pdf_path)
            return False

        os.replace(temp_pdf_path, output_path)
        elapsed = time.monotonic() - started_at
        logger.info(
            "SUCCESS input=%s output=%s pages=%d size=%d elapsed=%.2fs",
            input_path,
            output_path.resolve(),
            page_count,
            output_path.stat().st_size,
            elapsed,
        )
        return True
    except Exception as e:
        elapsed = time.monotonic() - started_at
        logger.error(
            "FAILED input=%s output=%s elapsed=%.2fs error=%s",
            input_path,
            output_path.resolve(),
            elapsed,
            e,
            exc_info=True,
        )
        return False
    finally:
        if temp_pdf_path.exists():
            try:
                temp_pdf_path.unlink()
                logger.debug("一時PDFを削除: %s", temp_pdf_path)
            except Exception:
                logger.warning("一時PDFを削除できません: %s", temp_pdf_path, exc_info=True)


def process_directory(input_dir, output_dir, driver, css_files=None, template_file=None, compact=False, font_size=16, merge=False, merge_name=None, selected_files=None):
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
    failed_files = []
    for md_file in md_files:
        # 出力パスを相対パスで計算
        rel_path = md_file.relative_to(input_dir)
        pdf_path = output_dir / rel_path.with_suffix('.pdf')
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        
        if process_file(md_file, pdf_path, driver, css_files, template_file, compact, font_size):
            success_count += 1
            generated_pdfs.append(pdf_path)
        else:
            failed_files.append(md_file)
    
    logger.info(f"\nConversion completed: {success_count}/{len(md_files)} files converted successfully")
    if failed_files:
        logger.error("変換失敗ファイル (%d件):", len(failed_files))
        for failed_file in failed_files:
            logger.error("  - %s", failed_file.resolve())
    
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
