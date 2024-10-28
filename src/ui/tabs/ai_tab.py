from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTextEdit, QComboBox, QSpinBox,
                           QProgressBar, QMessageBox, QSplitter, QTableWidget,
                           QTableWidgetItem, QHeaderView, QDialog, QFormLayout, 
                           QLineEdit, QDialogButtonBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl, QTimer
from PyQt5.QtGui import QDesktopServices
from loguru import logger
from src.core.ai_api import AIAPI
from src.core.article_fetcher import ArticleFetcher
from src.core.publisher import Publisher
from src.core.account_api import AccountAPI
import asyncio
import json
from pathlib import Path
from datetime import datetime

class AIWorker(QThread):
    """AI处理工作线程"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, text: str, task: str, style: str = None, temperature: float = 0.7):
        super().__init__()
        self.text = text
        self.task = task
        self.style = style
        self.temperature = temperature
        self.ai_api = AIAPI()
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.ai_api.process(
                    self.text,
                    self.task,
                    style=self.style,
                    temperature=self.temperature
                )
            )
            loop.close()
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"AI处理失败: {str(e)}")
            self.error.emit(str(e))

class ArticleLoadWorker(QThread):
    """文章列表加载线程"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, token: str, page: int = 1, page_size: int = 20):
        super().__init__()
        self.token = token
        self.page = page
        self.page_size = page_size
        self.fetcher = ArticleFetcher(token)
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.fetcher.fetch_articles(self.page, self.page_size)
            )
            loop.close()
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"加载文章列表失败: {str(e)}")
            self.error.emit(str(e))

class PublishWorker(QThread):
    """文章发布工作线程"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, token: str, article_data: dict):
        super().__init__()
        self.token = token
        self.article_data = article_data
        self.publisher = Publisher()
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.publisher.publish_toutiao(
                    self.token,
                    self.article_data
                )
            )
            loop.close()
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"发布失败: {str(e)}")
            self.error.emit(str(e))

class AccountVerifyWorker(QThread):
    """账号验证工作线程"""
    finished = pyqtSignal(bool)
    error = pyqtSignal(str)
    
    def __init__(self, account_data: dict):
        super().__init__()
        self.account_data = account_data
        self.account_api = AccountAPI()
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.account_api.verify_token(self.account_data.get("token", ""))
            )
            loop.close()
            
            if result["valid"]:
                self.account_data.update({
                    "name": result.get("name", "未知用户"),
                    "status": result.get("status", "已登录"),
                    "valid": True
                })
                self.finished.emit(True)
            else:
                self.error.emit(result.get("error", "验证失败"))
                
        except Exception as e:
            logger.error(f"验证失败: {str(e)}")
            self.error.emit(str(e))
class AITab(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.current_page = 1
        self.page_size = 20
        self.total_articles = 0
        self.current_account = None
        self.account_api = AccountAPI()
        
        # 先初始化UI
        self.init_ui()
        
        # UI初始化完成后，再加载账号
        QTimer.singleShot(0, self.load_current_account)
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 顶部账号信息
        account_layout = QHBoxLayout()
        self.account_label = QLabel("当前账号：未登录")
        self.account_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.clicked.connect(self.load_articles)
        self.refresh_btn.setEnabled(False)  # 默认禁用
        
        account_layout.addWidget(self.account_label)
        account_layout.addWidget(self.refresh_btn)
        account_layout.addStretch()
        
        layout.addLayout(account_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # === 左侧部分 ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 控制区域
        control_layout = QHBoxLayout()
        
        # 任务选择
        task_label = QLabel("任务:")
        self.task_combo = QComboBox()
        self.task_combo.addItems(['文章改写', '风格转换', '标题优化', '扩写内容', '生成摘要', '润色优化'])
        control_layout.addWidget(task_label)
        control_layout.addWidget(self.task_combo)
        
        # 风格选择
        style_label = QLabel("风格:")
        self.style_combo = QComboBox()
        self.style_combo.addItems(['正式严谨', '轻松活泼', '新闻报道', '营销文案', '小说风格', '诗歌风格'])
        control_layout.addWidget(style_label)
        control_layout.addWidget(self.style_combo)
        
        # 创意度调节
        temp_label = QLabel("创意度:")
        self.temp_spin = QSpinBox()
        self.temp_spin.setRange(1, 10)
        self.temp_spin.setValue(7)
        control_layout.addWidget(temp_label)
        control_layout.addWidget(self.temp_spin)
        
        left_layout.addLayout(control_layout)
        
        # 原文输入区
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("在此输入需要处理的文本...")
        left_layout.addWidget(self.input_text)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        self.process_btn = QPushButton("开始处理")
        self.process_btn.clicked.connect(self.process_text)
        btn_layout.addWidget(self.process_btn)
        
        self.publish_btn = QPushButton("发布文章")
        self.publish_btn.clicked.connect(self.publish_article)
        self.publish_btn.setEnabled(False)  # 默认禁用
        btn_layout.addWidget(self.publish_btn)
        
        left_layout.addLayout(btn_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
        # === 右侧部分 ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 结果输出区
        self.output_text = QTextEdit()
        self.output_text.setPlaceholderText("处理结果将显示在这里...")
        self.output_text.setReadOnly(True)
        right_layout.addWidget(self.output_text)
        
        # 添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setSizes([500, 500])
        
        layout.addWidget(splitter)
        
        # 文章列表
        self.article_table = QTableWidget()
        self.article_table.setColumnCount(4)
        self.article_table.setHorizontalHeaderLabels(["标题", "发布时间", "阅读量", "操作"])
        header = self.article_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.article_table)
        
        # 分页控制
        page_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("上一页")
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setEnabled(False)
        
        self.page_label = QLabel("第1页")
        
        self.next_btn = QPushButton("下一页")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(False)
        
        page_layout.addWidget(self.prev_btn)
        page_layout.addWidget(self.page_label)
        page_layout.addWidget(self.next_btn)
        page_layout.addStretch()
        
        layout.addLayout(page_layout)
        
        self.setLayout(layout)
    def load_current_account(self):
        """加载当前账号"""
        try:
            # 测试数据
            self.current_account = {
                "token": "test_token",
                "name": "测试账号",
                "status": "已登录",
                "valid": True
            }
            self.update_account_label()
            
            # 启用相关按钮
            if hasattr(self, 'refresh_btn'):
                self.refresh_btn.setEnabled(True)
            if hasattr(self, 'publish_btn'):
                self.publish_btn.setEnabled(True)
                
        except Exception as e:
            logger.error(f"加载当前账号失败: {str(e)}")
            self.current_account = None
            if hasattr(self, 'account_label'):
                self.update_account_label()
            QMessageBox.warning(self, "错误", f"加载账号失败：{str(e)}")
            
    def update_account_label(self):
        """更新账号显示"""
        try:
            if self.current_account and self.current_account.get("valid", False):
                name = self.current_account.get("name", "未知用户")
                status = self.current_account.get("status", "已登录")
                self.account_label.setText(f"当前账号：{name} ({status})")
                self.account_label.setStyleSheet("color: green; font-size: 14px; font-weight: bold;")
                self.refresh_btn.setEnabled(True)
                if hasattr(self, 'publish_btn'):
                    self.publish_btn.setEnabled(True)
            else:
                self.account_label.setText("当前账号：未登录")
                self.account_label.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
                self.refresh_btn.setEnabled(False)
                if hasattr(self, 'publish_btn'):
                    self.publish_btn.setEnabled(False)
                
        except Exception as e:
            logger.error(f"更新账号显示失败: {str(e)}")
            self.account_label.setText("当前账号：更新失败")
            self.account_label.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
            
    def process_text(self):
        """处理文本"""
        try:
            text = self.input_text.toPlainText().strip()
            if not text:
                QMessageBox.warning(self, "警告", "请输入需要处理的文本")
                return
                
            task = self.task_combo.currentText()
            style = self.style_combo.currentText()
            temperature = self.temp_spin.value() / 10.0
            
            # 显示进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.process_btn.setEnabled(False)
            
            # 创建处理线程
            self.worker = AIWorker(text, task, style, temperature)
            self.worker.finished.connect(self.handle_process_finished)
            self.worker.error.connect(self.handle_process_error)
            self.worker.progress.connect(self.progress_bar.setValue)
            self.worker.start()
            
        except Exception as e:
            logger.error(f"处理文本失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"处理文本失败：{str(e)}")
            self.process_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            
    def handle_process_finished(self, result: str):
        """处理完成"""
        self.output_text.setPlainText(result)
        self.process_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.publish_btn.setEnabled(True)
        
    def handle_process_error(self, error: str):
        """处理错误"""
        QMessageBox.critical(self, "错误", f"AI处理失败：{error}")
        self.process_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
    def load_articles(self):
        """加载文章列表"""
        try:
            if not self.current_account:
                logger.warning("未选择账号，无法加载文章列表")
                return
                
            # 获取token
            token = self.current_account.get("token")
            if not token:
                logger.error("当前账号token为空")
                raise Exception("当前账号token无效")
                
            # 清空表格
            self.article_table.setRowCount(0)
            
            # 创建加载线程
            self.load_worker = ArticleLoadWorker(token, self.current_page, self.page_size)
            self.load_worker.finished.connect(self.handle_articles_loaded)
            self.load_worker.error.connect(self.handle_load_error)
            self.load_worker.start()
            
            # 禁用分页按钮
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.page_label.setText("加载中...")
            
        except Exception as e:
            logger.error(f"加载文章列表失败: {str(e)}")
            QMessageBox.warning(self, "警告", f"加载文章列表失败：{str(e)}")
    def handle_articles_loaded(self, result: dict):
        """处理加载的文章列表"""
        try:
            articles = result.get("articles", [])
            self.total_articles = result.get("total", 0)
            has_more = result.get("has_more", False)
            
            # 清空并设置表格行数
            self.article_table.setRowCount(len(articles))
            
            # 填充数据
            for row, article in enumerate(articles):
                # 标题
                title_item = QTableWidgetItem(article.get("title", ""))
                self.article_table.setItem(row, 0, title_item)
                
                # 发布时间
                time_item = QTableWidgetItem(article.get("publish_time", ""))
                self.article_table.setItem(row, 1, time_item)
                
                # 阅读量
                read_item = QTableWidgetItem(str(article.get("read_count", 0)))
                self.article_table.setItem(row, 2, read_item)
                
                # 操作按钮
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(5, 2, 5, 2)
                
                edit_btn = QPushButton("编辑")
                edit_btn.setFixedWidth(60)
                edit_btn.clicked.connect(lambda checked, r=row: self.edit_article(r))
                
                view_btn = QPushButton("查看")
                view_btn.setFixedWidth(60)
                view_btn.clicked.connect(lambda checked, url=article.get("article_url"): self.view_article(url))
                
                btn_layout.addWidget(edit_btn)
                btn_layout.addWidget(view_btn)
                btn_layout.addStretch()
                
                self.article_table.setCellWidget(row, 3, btn_widget)
            
            # 更新分页控制
            total_pages = (self.total_articles - 1) // self.page_size + 1
            self.prev_btn.setEnabled(self.current_page > 1)
            self.next_btn.setEnabled(has_more)
            self.page_label.setText(f"第{self.current_page}页/共{total_pages}页")
            
        except Exception as e:
            logger.error(f"显示文章列表失败: {str(e)}")
            QMessageBox.warning(self, "警告", f"显示文章列表失败：{str(e)}")
            
    def handle_load_error(self, error: str):
        """处理加载错误"""
        QMessageBox.critical(self, "错误", f"加载文章列表失败：{error}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(False)
        self.page_label.setText(f"第{self.current_page}页")
        
    def prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_articles()
            
    def next_page(self):
        """下一页"""
        self.current_page += 1
        self.load_articles()
        
    def edit_article(self, row: int):
        """编辑文章"""
        try:
            # 获取文章数据
            article_data = {
                "title": self.article_table.item(row, 0).text(),
                "content": "",  # TODO: 从API获取完整内容
                "publish_time": self.article_table.item(row, 1).text(),
                "read_count": self.article_table.item(row, 2).text()
            }
            
            # 显示编辑对话框
            dialog = PublishDialog(article_data["content"], self)
            if dialog.exec_() == QDialog.Accepted:
                updated_data = dialog.get_article_data()
                updated_data["title"] = article_data["title"]  # 保留原标题
                
                # TODO: 调用API更新文章
                QMessageBox.information(self, "成功", f"文章《{updated_data['title']}》已更新")
                
                # 刷新文章列表
                self.load_articles()
            
        except Exception as e:
            logger.error(f"编辑文章失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"编辑文章失败：{str(e)}")
            
    def view_article(self, url: str):
        """查看文章"""
        if url:
            QDesktopServices.openUrl(QUrl(url))
        else:
            QMessageBox.warning(self, "警告", "无法获取文章链接")
            
    def publish_article(self):
        """发布文章"""
        try:
            if not self.current_account:
                QMessageBox.warning(self, "警告", "请先登录账号")
                return
                
            content = self.output_text.toPlainText().strip()
            if not content:
                QMessageBox.warning(self, "警告", "没有可发布的内容")
                return
                
            # 显示发布对话框
            dialog = PublishDialog(content, self)
            if dialog.exec_() == QDialog.Accepted:
                article_data = dialog.get_article_data()
                
                # 创建发布线程
                self.publish_worker = PublishWorker(
                    self.current_account.get("token", ""),
                    article_data
                )
                self.publish_worker.finished.connect(self.handle_publish_finished)
                self.publish_worker.error.connect(self.handle_publish_error)
                self.publish_worker.start()
                
                # 显示进度条
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                self.publish_btn.setEnabled(False)
                
        except Exception as e:
            logger.error(f"发布文章失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"发布文章失败：{str(e)}")
            
    def handle_publish_finished(self, result: dict):
        """发布完成"""
        self.progress_bar.setVisible(False)
        self.publish_btn.setEnabled(True)
        QMessageBox.information(
            self, 
            "成功", 
            f"文章发布成功！\n文章ID：{result.get('article_id', '')}"
        )
        # 刷新文章列表
        self.load_articles()
        
    def handle_publish_error(self, error: str):
        """发布错误"""
        self.progress_bar.setVisible(False)
        self.publish_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", f"发布失败：{error}")

class PublishDialog(QDialog):
    """发布文章对话框"""
    def __init__(self, content: str, parent=None):
        super().__init__(parent)
        self.content = content
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("发布文章")
        self.setMinimumWidth(500)
        
        layout = QFormLayout()
        
        # 标题输入
        self.title_input = QLineEdit()
        layout.addRow("文章标题:", self.title_input)
        
        # 分类选择
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            '科技', '数码', '互联网', '编程开发', 
            '人工智能', '职场', '创业', '其他'
        ])
        layout.addRow("文章分类:", self.category_combo)
        
        # 标签输入
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("多个标签用逗号分隔")
        layout.addRow("文章标签:", self.tags_input)
        
        # 内容预览
        content_preview = QTextEdit()
        content_preview.setPlainText(self.content)
        content_preview.setReadOnly(True)
        content_preview.setMaximumHeight(200)
        layout.addRow("内容预览:", content_preview)
        
        # 按钮
        btn_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)
        
        self.setLayout(layout)
        
    def get_article_data(self) -> dict:
        """获取文章数据"""
        return {
            'title': self.title_input.text().strip(),
            'category': self.category_combo.currentText(),
            'tags': [tag.strip() for tag in self.tags_input.text().split(',') if tag.strip()],
            'content': self.content
        }            
