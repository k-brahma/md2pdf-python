"""
WebDriver management for PDF conversion
"""

import platform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .logger import logger


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
        if platform.system() == 'Windows':
            service.creation_flags = 0x08000000
    except:
        pass
    
    return webdriver.Chrome(service=service, options=options)