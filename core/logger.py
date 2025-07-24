"""
Logger configuration for the core package
"""

import logging
from pathlib import Path

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