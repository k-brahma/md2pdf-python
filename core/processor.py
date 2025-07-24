"""
File and directory processing functionality
"""

from pathlib import Path

from .converter import markdown_to_html
from .logger import logger
from .pdf import html_to_pdf, merge_pdfs


def process_file(input_path, output_path, driver, css_files=None, template_file=None, compact=False, font_size=16):
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
    for md_file in md_files:
        # 出力パスを相対パスで計算
        rel_path = md_file.relative_to(input_dir)
        pdf_path = output_dir / rel_path.with_suffix('.pdf')
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        
        if process_file(md_file, pdf_path, driver, css_files, template_file, compact, font_size):
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