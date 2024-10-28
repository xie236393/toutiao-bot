from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class ArticleTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 临时的提示标签
        label = QLabel("文章管理功能开发中...")
        layout.addWidget(label)
        
        self.setLayout(layout)