"""
Markdown to HTML conversion functionality
"""

import markdown
from jinja2 import Template
from markdown.extensions import codehilite, fenced_code, tables, toc

from config.config import (
    CODEHILITE_CONFIG,
    DEFAULT_CSS,
    DEFAULT_HTML_TEMPLATE,
    MARKDOWN_EXTENSIONS,
    PDF_CONFIG,
    load_css_file,
)
from .logger import logger


def load_template_file(file_path):
    """テンプレートファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Template file not found: {file_path}")
        return ""


def markdown_to_html(md_content, css_files=None, template_file=None, compact=False, font_size=16):
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
    if template_file:
        html_template = load_template_file(template_file)
    else:
        html_template = load_template_file('templates/default.html')
    
    if not html_template:
        html_template = DEFAULT_HTML_TEMPLATE
    
    return Template(html_template).render(
        css_content=css_content,
        html_content=html_content
    )