"""
Markdown to HTML conversion functionality using markdown-it-py
"""

from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.footnote import footnote_plugin
from jinja2 import Template
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

from config.config import (
    DEFAULT_CSS,
    DEFAULT_HTML_TEMPLATE,
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


def highlight_code(code, lang=None, attrs=None):
    """コードのシンタックスハイライト"""
    if not lang:
        return f'<pre><code>{code}</code></pre>'
    
    try:
        lexer = get_lexer_by_name(lang, stripall=True)
        formatter = HtmlFormatter(
            noclasses=True,
            style='default',
            cssclass='highlight'
        )
        highlighted = highlight(code, lexer, formatter)
        return highlighted
    except ClassNotFound:
        return f'<pre><code class="language-{lang}">{code}</code></pre>'


def markdown_to_html(md_content, css_files=None, template_file=None, compact=False, font_size=16):
    """MarkdownをHTMLに変換（markdown-it-py使用）"""
    
    # markdown-it-pyの設定
    md = (
        MarkdownIt("commonmark", {
            "breaks": True,        # 改行を<br>に変換
            "html": True,         # HTMLタグを許可
            "linkify": True,      # URL自動リンク化
            "typographer": True   # 引用符等の自動変換
        })
        .use(front_matter_plugin)
        .use(footnote_plugin)
        .enable([
            'table',          # テーブル
            'strikethrough',  # 打ち消し線
        ])
    )
    
    # コードハイライト用のレンダラー設定
    def render_code_block(self, tokens, idx, options, env, renderer):
        token = tokens[idx]
        info = token.info.strip() if token.info else ""
        lang = info.split()[0] if info else None
        
        return highlight_code(token.content, lang)
    
    # レンダラーのオーバーライド
    md.renderer.rules["code_block"] = render_code_block
    md.renderer.rules["fence"] = render_code_block
    
    # HTML変換実行
    html_content = md.render(md_content)
    
    logger.debug(f"markdown-it-pyでHTML変換完了")
    
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