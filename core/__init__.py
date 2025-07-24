"""
Core package for Markdown to PDF converter
"""

from .converter import markdown_to_html, load_template_file
from .driver import create_driver
from .pdf import html_to_pdf, add_footer_to_pdf, merge_pdfs
from .presets import PRESETS, get_preset_config
from .processor import process_file, process_directory

__all__ = [
    'markdown_to_html',
    'load_template_file',
    'create_driver',
    'html_to_pdf',
    'add_footer_to_pdf',
    'merge_pdfs',
    'PRESETS',
    'get_preset_config',
    'process_file',
    'process_directory',
]