from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTextEdit, QComboBox, QSpinBox,
                           QProgressBar, QMessageBox, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from loguru import logger
import time
from src.core.ai_rewrite import AIRewriter  # 我们待会儿创建这个类

class RewriteWorker(QThread):
    """AI改写工作线程"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, text: str, style: str, temp: float = 0.7):
        super().__init__()
        self.text = text
        self.style = style
        self.temp = temp
        self.rewriter = AIRewriter()
        
    def run(self):
        try:
            result = self.rewriter.rewrite(
                text=self.text,
                style=self.style,
                temperature=self.temp
            )
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"AI改写失败: {str(e)}")
            self.error.emit(str(e))

class RewriteTab(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 控制区域
        control_layout = QHBoxLayout()
        
        # 风格选择
        style_label = QLabel("改写风格:")
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            '正式严谨', '轻松活泼', '新闻报道', 
            '营销文案', '小说风格', '诗歌风格'
        ])
        control_layout.addWidget(style_label)
        control_layout.addWidget(self.style_combo)
        
        # 创意度调节
        temp_label = QLabel("创意程度:")
        self.temp_spin = QSpinBox()
        self.temp_spin.setRange(1, 10)
        self.temp_spin.setValue(7)
        self.temp_spin.setToolTip("值越大，改写结果越有创意性")
        control_layout.addWidget(temp_label)
        control_layout.addWidget(self.temp_spin)
        
        # 改写按钮
        self.rewrite_btn = QPushButton("开始改写")
        self.rewrite_btn.clicked.connect(self.start_rewrite)
        control_layout.addWidget(self.rewrite_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 主要编辑区域
        splitter = QSplitter(Qt.Horizontal)
        
        # 原文编辑框
        self.source_text = QTextEdit()
        self.source_text.setPlaceholderText("在此输入需要改写的文本...")
        splitter.addWidget(self.source_text)
        
        # 结果显示框
        self.result_text = QTextEdit()
        self.result_text.setPlaceholderText("改写结果将在这里显示...")
        self.result_text.setReadOnly(True)
        splitter.addWidget(self.result_text)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        
    def start_rewrite(self):
        """开始改写"""
        try:
            text = self.source_text.toPlainText().strip()
            if not text:
                QMessageBox.warning(self, "警告", "请输入需要改写的文本")
                return
                
            self.rewrite_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.result_text.clear()
            
            style = self.style_combo.currentText()
            temp = self.temp_spin.value() / 10
            
            self.worker = RewriteWorker(text, style, temp)
            self.worker.finished.connect(self.handle_result)
            self.worker.error.connect(self.handle_error)
            self.worker.progress.connect(self.progress_bar.setValue)
            self.worker.start()
            
        except Exception as e:
            logger.error(f"启动改写失败: {str(e)}")
            self.handle_error(str(e))
            
    def handle_result(self, result: str):
        """处理改写结果"""
        self.result_text.setPlainText(result)
        self.rewrite_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
    def handle_error(self, error: str):
        """处理错误"""
        QMessageBox.critical(self, "错误", f"改写失败：{error}")
        self.rewrite_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
    def closeEvent(self, event):
        """窗口关闭时清理"""
        if self.worker and self.worker.isRunning():
            self.worker.wait()
        event.accept()