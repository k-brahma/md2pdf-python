#!/usr/bin/env python3
"""
Markdown to PDF converter GUI interface
"""

import logging
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core import create_driver, process_directory, process_file, get_preset_config

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ファイルハンドラの設定
log_file = Path('pdf_converter.log')
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# コンソールハンドラの設定
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# フォーマッタの設定
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# ハンドラの追加
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class ConversionWorker(QThread):
    """変換処理を別スレッドで実行するためのワーカークラス"""
    progress = Signal(str)
    finished = Signal(bool, str)  # 成功/失敗とエラーメッセージを送信
    
    def __init__(self, input_path, output_path, css_files=None, template_file=None, compact=False, font_size=16, merge=False, merge_name=None, selected_files=None):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.css_files = css_files
        self.template_file = template_file
        self.compact = compact
        self.font_size = font_size
        self.merge = merge
        self.merge_name = merge_name
        self.selected_files = selected_files
        self.driver = None
    
    def run(self):
        error_occurred = False
        error_message = ""
        
        try:
            logger.info(f"変換処理を開始: 入力={self.input_path}, 出力={self.output_path}")
            logger.debug(f"設定: css_files={self.css_files}, compact={self.compact}, font_size={self.font_size}")
            
            # WebDriver作成
            logger.debug("WebDriver作成開始")
            self.driver = create_driver(False)
            logger.debug("WebDriver作成完了")
            
            success = False
            if self.selected_files:
                logger.info(f"選択されたファイルを処理: {self.selected_files}")
                success = process_directory(
                    Path(self.input_path), self.output_path, self.driver,
                    css_files=self.css_files,
                    template_file=self.template_file,
                    compact=self.compact,
                    font_size=self.font_size,
                    merge=self.merge,
                    merge_name=self.merge_name,
                    selected_files=[Path(f) for f in self.selected_files]
                )
            elif self.input_path.is_dir():
                logger.info(f"ディレクトリを処理: {self.input_path}")
                success = process_directory(
                    self.input_path, self.output_path, self.driver,
                    css_files=self.css_files,
                    template_file=self.template_file,
                    compact=self.compact,
                    font_size=self.font_size,
                    merge=self.merge,
                    merge_name=self.merge_name
                )
            else:
                logger.info(f"単一ファイルを処理: {self.input_path}")
                success = process_file(
                    self.input_path, self.output_path, self.driver,
                    css_files=self.css_files,
                    template_file=self.template_file,
                    compact=self.compact,
                    font_size=self.font_size
                )
            
            logger.debug(f"変換処理結果: success={success}")
            
            if success:
                logger.info("変換処理が正常に完了しました")
                self.finished.emit(True, "")
            else:
                error_message = "変換処理が失敗しました（詳細は上記のログを確認してください）"
                logger.error(error_message)
                error_occurred = True
                
        except Exception as e:
            import traceback
            error_message = f"変換処理中に予期せぬエラーが発生しました:\n\nエラー: {str(e)}\n\nスタックトレース:\n{traceback.format_exc()}"
            logger.error(error_message)
            error_occurred = True
            
        finally:
            # WebDriverのクリーンアップ
            if self.driver:
                try:
                    logger.debug("WebDriver終了開始")
                    self.driver.quit()
                    logger.debug("WebDriver終了完了")
                except Exception as e:
                    cleanup_error = f"WebDriverの終了中にエラーが発生しました: {str(e)}"
                    logger.error(cleanup_error, exc_info=True)
                    if not error_occurred:
                        error_message = cleanup_error
                        error_occurred = True
            
            # 結果をシグナルで送信
            if error_occurred:
                self.finished.emit(False, error_message)


class MainWindow(QMainWindow):
    """メインウィンドウ"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown to PDF Converter")
        self.setMinimumSize(800, 600)  # ウィンドウサイズを大きく
        
        # メインウィジェットとレイアウト
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 入力ファイル/ディレクトリ選択
        input_layout = QHBoxLayout()
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("入力ファイルまたはディレクトリを選択")
        input_button = QPushButton("参照...")
        input_button.clicked.connect(self.select_input)
        input_layout.addWidget(self.input_path)
        input_layout.addWidget(input_button)
        layout.addLayout(input_layout)
        
        # 出力ディレクトリ選択
        output_layout = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("出力ディレクトリを選択")
        output_button = QPushButton("参照...")
        output_button.clicked.connect(self.select_output)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(output_button)
        layout.addLayout(output_layout)
        
        # オプション設定
        options_layout = QVBoxLayout()
        
        # プリセット選択
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("プリセット:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("なし", None)
        self.preset_combo.addItem("デフォルト", "default")
        self.preset_combo.addItem("ビジネス文書", "business")
        self.preset_combo.addItem("シンプル", "simple")
        self.preset_combo.setCurrentIndex(1)  # デフォルトを選択
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        options_layout.addLayout(preset_layout)
        
        # CSSファイル選択
        css_layout = QHBoxLayout()
        self.css_path = QLineEdit()
        self.css_path.setPlaceholderText("CSSファイルを選択（オプション）")
        css_button = QPushButton("参照...")
        css_button.clicked.connect(self.select_css)
        css_layout.addWidget(self.css_path)
        css_layout.addWidget(css_button)
        options_layout.addLayout(css_layout)
        
        # コンパクトモード
        self.compact_check = QCheckBox("コンパクトモード")
        options_layout.addWidget(self.compact_check)
        
        # フォントサイズ
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("フォントサイズ:"))
        self.font_size = QSpinBox()
        self.font_size.setRange(10, 36)
        self.font_size.setValue(16)
        font_layout.addWidget(self.font_size)
        font_layout.addStretch()
        options_layout.addLayout(font_layout)
        
        # マージオプション
        merge_layout = QHBoxLayout()
        self.merge_check = QCheckBox("PDFをマージ")
        self.merge_name = QLineEdit()
        self.merge_name.setPlaceholderText("マージ後のファイル名")
        self.merge_name.setEnabled(False)
        self.merge_check.stateChanged.connect(self.toggle_merge_name)
        merge_layout.addWidget(self.merge_check)
        merge_layout.addWidget(self.merge_name)
        options_layout.addLayout(merge_layout)
        
        layout.addLayout(options_layout)
        
        # 変換ボタン
        self.convert_button = QPushButton("変換開始")
        self.convert_button.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_button)
        
        # 進捗バー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # ステータスラベル
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        # ログ表示エリア
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(150)
        layout.addWidget(self.log_area)
        
        # 余白を追加
        layout.addStretch()
    
    def select_input(self):
        """入力ファイル/ディレクトリを選択"""
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "入力ファイルを選択",
            "",
            "Markdown Files (*.md);;All Files (*.*)"
        )
        if paths:
            # 複数ファイルが選択された場合は、最初のファイルのディレクトリを入力パスとして使用
            input_path = Path(paths[0])
            if len(paths) > 1:
                # 複数ファイルが選択された場合は、そのディレクトリを入力パスとして使用
                self.input_path.setText(str(input_path.parent))
                # 選択されたファイルのリストを保存
                self.selected_files = paths
            else:
                self.input_path.setText(str(input_path))
                self.selected_files = None
    
    def select_output(self):
        """出力ディレクトリを選択"""
        path = QFileDialog.getExistingDirectory(
            self,
            "出力ディレクトリを選択"
        )
        if path:
            self.output_path.setText(path)
    
    def select_css(self):
        """CSSファイルを選択"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "CSSファイルを選択",
            "",
            "CSS Files (*.css);;All Files (*.*)"
        )
        if path:
            self.css_path.setText(path)
    
    def on_preset_changed(self):
        """プリセット選択が変更されたときの処理"""
        preset = self.preset_combo.currentData()
        if preset:
            # プリセットが選択されたら、CSSフィールドをクリア（プリセットの設定を使用）
            self.css_path.clear()
    
    def start_conversion(self):
        """変換処理を開始"""
        input_path = Path(self.input_path.text())
        output_path = Path(self.output_path.text())
        
        if not input_path.exists():
            QMessageBox.critical(self, "エラー", "入力パスが存在しません")
            return
        
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True)
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"出力ディレクトリの作成に失敗しました: {e}")
                return
        
        # マージオプションの検証
        if self.merge_check.isChecked() and not self.merge_name.text():
            QMessageBox.critical(self, "エラー", "マージオプションが有効な場合、マージ後のファイル名を指定してください")
            return
        
        # 変換処理を開始
        self.convert_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不確定プログレスバー
        self.status_label.setText("変換中...")
        
        # プリセット処理
        css_files = None
        template_file = None
        
        preset = self.preset_combo.currentData()
        if preset:
            preset_config = get_preset_config(preset)
            css_files = preset_config['css_files']
            template_file = preset_config['template_file']
        elif self.css_path.text():
            # プリセットが選択されていない場合は、手動で選択したCSSを使用
            css_files = [self.css_path.text()]
        
        # ワーカースレッドを作成して開始
        self.worker = ConversionWorker(
            input_path,
            output_path,
            css_files=css_files,
            template_file=template_file,
            compact=self.compact_check.isChecked(),
            font_size=self.font_size.value(),
            merge=self.merge_check.isChecked(),
            merge_name=self.merge_name.text() if self.merge_check.isChecked() else None,
            selected_files=getattr(self, 'selected_files', None)
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.start()
    
    def update_progress(self, message):
        """進捗状況を更新"""
        self.status_label.setText(message)
        self.log_area.append(message)
        logger.info(message)
    
    def conversion_finished(self, success, error_message):
        """変換処理が完了"""
        self.convert_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText("変換が完了しました")
            self.log_area.append("変換が完了しました")
            QMessageBox.information(self, "完了", "変換が正常に完了しました")
        else:
            error_text = f"変換に失敗しました\n\n{error_message}" if error_message else "変換に失敗しました"
            self.status_label.setText("変換に失敗しました")
            self.log_area.append(error_text)
            QMessageBox.critical(self, "エラー", error_text)

    def toggle_merge_name(self, state):
        """マージオプションの有効/無効に応じてファイル名入力フィールドを切り替え"""
        self.merge_name.setEnabled(state == Qt.CheckState.Checked.value)
        if state == Qt.CheckState.Checked.value:
            self.merge_name.setFocus()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main() 