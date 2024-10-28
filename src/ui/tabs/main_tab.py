from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                           QPushButton, QLabel, QProgressBar, QMessageBox,
                           QSplitter, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QSize
from loguru import logger
import re

class MainTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 1. 顶部说明
        tip_label = QLabel("请输入文章链接，每行一个")
        tip_label.setStyleSheet("color: gray;")
        left_layout.addWidget(tip_label)
        
        # 2. 文章链接输入区
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("支持以下格式：\n"
                                         "- 今日头条：https://www.toutiao.com/article/...\n"
                                         "- 微信文章：https://mp.weixin.qq.com/s/...\n"
                                         "- 新浪微博：https://weibo.com/...\n"
                                         "- 知乎文章：https://zhuanlan.zhihu.com/p/...")
        self.url_input.setMinimumHeight(200)
        left_layout.addWidget(self.url_input)
        
        # 3. 按钮区域
        btn_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("导入文章")
        self.import_btn.setMinimumWidth(120)
        self.import_btn.clicked.connect(self.import_articles)
        
        self.clear_btn = QPushButton("清空")
        self.clear_btn.setMinimumWidth(80)
        self.clear_btn.clicked.connect(self.clear_input)
        
        btn_layout.addWidget(self.import_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        
        left_layout.addLayout(btn_layout)
        
        # 4. 进度条
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        left_layout.addLayout(progress_layout)
        
        # 5. 状态区域
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: gray;")
        left_layout.addWidget(self.status_label)
        
        # 添加左侧面板到分割器
        splitter.addWidget(left_widget)
        
        # 右侧面板 - 文章列表
        self.article_table = QTableWidget()
        self.article_table.setColumnCount(4)
        self.article_table.setHorizontalHeaderLabels(['标题', '来源', '状态', '操作'])
        self.article_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.article_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.article_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.article_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        splitter.addWidget(self.article_table)
        
        # 设置分割器比例
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
    def import_articles(self):
        """导入文章"""
        try:
            # 获取输入的链接
            text = self.url_input.toPlainText().strip()
            if not text:
                QMessageBox.warning(self, "提示", "请输入文章链接！")
                return
                
            # 分割成单独的链接
            urls = [url.strip() for url in text.split('\n') if url.strip()]
            
            # 显示进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(len(urls))
            self.progress_bar.setValue(0)
            
            self.status_label.setText(f"正在处理 {len(urls)} 个链接...")
            
            # 处理每个链接
            for i, url in enumerate(urls):
                # 1. 识别链接类型
                platform = self.identify_platform(url)
                if not platform:
                    logger.warning(f"无法识别的链接格式: {url}")
                    continue
                    
                # 2. 添加到文章列表
                row = self.article_table.rowCount()
                self.article_table.insertRow(row)
                
                # 设置标题列
                title_item = QTableWidgetItem("获取中...")
                self.article_table.setItem(row, 0, title_item)
                
                # 设置来源列
                platform_item = QTableWidgetItem(platform)
                self.article_table.setItem(row, 1, platform_item)
                
                # 设置状态列
                status_item = QTableWidgetItem("待处理")
                self.article_table.setItem(row, 2, status_item)
                
                # 设置操作列
                preview_btn = QPushButton("预览")
                self.article_table.setCellWidget(row, 3, preview_btn)
                
                # 更新进度条
                self.progress_bar.setValue(i + 1)
                
            self.status_label.setText(f"成功导入 {len(urls)} 篇文章")
            
        except Exception as e:
            logger.error(f"导入文章失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"导入失败：{str(e)}")
            
        finally:
            self.progress_bar.setVisible(False)
            
    def clear_input(self):
        """清空输入"""
        self.url_input.clear()
        self.status_label.clear()
        
    def identify_platform(self, url):
        """识别链接来源平台"""
        patterns = {
            r'toutiao\.com': '今日头条',
            r'mp\.weixin\.qq\.com': '微信公众号',
            r'weibo\.com': '新浪微博',
            r'zhihu\.com': '知乎'
        }
        
        for pattern, platform in patterns.items():
            if re.search(pattern, url):
                return platform
                
        return None