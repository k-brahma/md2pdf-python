"""
Preset configurations for PDF conversion
"""

# プリセット定義
PRESETS = {
    'default': {
        'css_files': ['css/simple.css', 'css/prism.css'],
        'template_file': None
    },
    'business': {
        'css_files': ['css/business.css'],
        'template_file': 'templates/business.html'
    },
    'simple': {
        'css_files': ['css/simple.css'],
        'template_file': None
    }
}

def get_preset_config(preset_name):
    """プリセット名から設定を取得"""
    return PRESETS.get(preset_name, PRESETS['default'])