#!/usr/bin/env python3
"""
Markdown to PDF converter CLI interface
"""

import argparse
import sys
import logging
from pathlib import Path
from core import create_driver, process_file, process_directory

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# コンソールハンドラの設定
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# フォーマッタの設定
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# ハンドラの追加
logger.addHandler(console_handler)

def main():
    parser = argparse.ArgumentParser(description='Convert Markdown to PDF (Pure Python approach)')
    parser.add_argument('input', help='Input Markdown file path or directory with -d option')
    parser.add_argument('output', nargs='?', help='Output PDF file path or directory (optional)')
    parser.add_argument('--no-headless', action='store_true', help='Run in non-headless mode')
    parser.add_argument('--css', nargs='+', help='CSS files to apply (e.g., --css simple.css prism.css)')
    parser.add_argument('--compact', action='store_true', help='Use compact layout for more content per page')
    parser.add_argument('--font-size', type=int, default=16, help='Base font size for PDF (default: 16px)')
    parser.add_argument('-d', '--directory', action='store_true', help='Process all Markdown files in the input directory')
    parser.add_argument('-m', '--merge', action='store_true', help='Merge all generated PDFs into a single file')
    parser.add_argument('-n', '--name', help='Name for the merged PDF file (required with -m option)')
    
    args = parser.parse_args()
    
    # マージオプションの検証
    if args.merge and not args.name:
        logger.error("Error: -n/--name option is required when using -m/--merge")
        sys.exit(1)
    
    # 入力パスの確認
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Error: Input path not found: {input_path}")
        sys.exit(1)
    
    # 出力パスを決定
    if args.output:
        output_path = Path(args.output)
    else:
        if args.directory:
            output_path = input_path
        else:
            output_path = input_path.with_suffix('.pdf')
    
    # WebDriverを起動
    driver = None
    try:
        driver = create_driver(not args.no_headless)
        
        if args.directory:
            # ディレクトリ内のすべてのMarkdownファイルを処理
            selected_files = list(input_path.glob('**/*.md'))
            if not selected_files:
                logger.error(f"No Markdown files found in {input_path}")
                sys.exit(1)
            
            logger.info(f"Found {len(selected_files)} Markdown files to process")
            success = process_directory(
                input_path, output_path, driver,
                css_files=args.css,
                compact=args.compact,
                font_size=args.font_size,
                merge=args.merge,
                merge_name=args.name,
                selected_files=selected_files
            )
            
            if not success:
                sys.exit(1)
        else:
            # 単一ファイルの処理
            if not output_path.parent.exists():
                output_path.parent.mkdir(parents=True, exist_ok=True)
            
            success = process_file(
                input_path, output_path, driver,
                css_files=args.css,
                compact=args.compact,
                font_size=args.font_size
            )
            
            if success:
                logger.info("✓ Conversion completed successfully!")
            else:
                logger.error("✗ Conversion failed!")
                sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Error: {e}")
        sys.exit(1)
    finally:
        if driver:
            driver.quit()


if __name__ == '__main__':
    main()