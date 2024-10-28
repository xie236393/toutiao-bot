from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTableWidget, QTableWidgetItem,
                           QHeaderView, QComboBox, QMessageBox, QTextEdit,
                           QSplitter, QTextBrowser)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from loguru import logger
from src.core.hot_api import HotAPI
import asyncio
import webbrowser
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

class HotWorker(QThread):
    """热榜获取工作线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    status = pyqtSignal(str)
    
    def __init__(self, platform, api_source='自动切换'):
        super().__init__()
        self.api = HotAPI()
        self.platform = platform
        self.api_source = api_source
        self.is_running = True
        
    def run(self):
        try:
            self.status.emit(f"正在获取{self.platform}热榜...")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if self.is_running:
                result = loop.run_until_complete(
                    self.api.get_hot_list(self.platform, self.api_source)
                )
                if result and self.is_running:
                    self.finished.emit(result)
                elif self.is_running:
                    self.error.emit("获取数据为空")
            
            loop.close()
            
        except Exception as e:
            if self.is_running:
                self.error.emit(str(e))
        finally:
            self.is_running = False
            
    def stop(self):
        """中断任务"""
        self.is_running = False
        self.status.emit("已中断获取")

class ContentFetcher(QThread):
    """文章内容获取线程"""
    content_ready = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, url: str, title: str = ""):
        super().__init__()
        self.url = url
        self.title = title
        self.is_running = True
        
    def run(self):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-gpu']
                )
                
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                page = context.new_page()
                page.set_default_timeout(20000)
                
                self.content_ready.emit("<h3>正在加载页面...</h3>")
                page.goto(self.url, wait_until='networkidle')
                
                domain = urlparse(self.url).netloc
                content = ""
                title = self.title
                
                if "toutiao.com" in domain:
                    content = self._extract_toutiao(page)
                elif "weibo.com" in domain:
                    content = self._extract_weibo(page)
                elif "zhihu.com" in domain:
                    content = self._extract_zhihu(page)
                elif "bilibili.com" in domain:
                    content = self._extract_bilibili(page)
                else:
                    content = self._extract_general(page)
                
                if not title:
                    title = page.title()
                
                content = self._clean_content(content)
                
                preview_html = f"""
                <h2 style='color: #333;'>{title}</h2>
                <hr>
                <div style='font-size: 14px; line-height: 1.6; color: #444; white-space: pre-wrap;'>
                    {content}
                </div>
                """
                
                self.content_ready.emit(preview_html)
                
                context.close()
                browser.close()
                
        except Exception as e:
            logger.error(f"获取文章内容失败: {str(e)}")
            self.error.emit(f"获取文章内容失败: {str(e)}")
            
    def _extract_toutiao(self, page):
        """提取今日头条文章内容"""
        try:
            page.wait_for_selector('.article-content', timeout=5000)
            content = page.evaluate('''() => {
                const article = document.querySelector('.article-content');
                return article ? article.innerText : '';
            }''')
            return content
        except Exception as e:
            logger.error(f"提取今日头条内容失败: {str(e)}")
            return self._extract_general(page)
            
    def _extract_weibo(self, page):
        """提取微博内容"""
        try:
            page.wait_for_selector('.detail_wbtext_4CRf9', timeout=5000)
            content = page.evaluate('''() => {
                const content = document.querySelector('.detail_wbtext_4CRf9');
                return content ? content.innerText : '';
            }''')
            return content
        except Exception as e:
            logger.error(f"提取微博内容失败: {str(e)}")
            return self._extract_general(page)
            
    def _extract_zhihu(self, page):
        """提取知乎内容"""
        try:
            page.wait_for_selector('.RichText', timeout=5000)
            content = page.evaluate('''() => {
                const contents = document.querySelectorAll('.RichText');
                return Array.from(contents).map(el => el.innerText).join('\\n\\n');
            }''')
            return content
        except Exception as e:
            logger.error(f"提取知乎内容失败: {str(e)}")
            return self._extract_general(page)
            
    def _extract_bilibili(self, page):
        """提取B站内容"""
        try:
            page.wait_for_selector('.video-description', timeout=5000)
            content = page.evaluate('''() => {
                const desc = document.querySelector('.video-description');
                return desc ? desc.innerText : '';
            }''')
            return content
        except Exception as e:
            logger.error(f"提取B站内容失败: {str(e)}")
            return self._extract_general(page)
            
    def _extract_general(self, page):
        """通用内容提取"""
        try:
            content = page.evaluate('''() => {
                const selectors = [
                    'article',
                    'main',
                    '.article',
                    '.content',
                    '.main-content',
                    '#content',
                    '#main'
                ];
                
                for (const selector of selectors) {
                    const element = document.querySelector(selector);
                    if (element) {
                        return element.innerText;
                    }
                }
                
                return document.body.innerText;
            }''')
            return content
        except Exception as e:
            logger.error(f"通用内容提取失败: {str(e)}")
            return ""
            
    def _clean_content(self, content: str) -> str:
        """清理内容"""
        try:
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = content.strip()
            content = content.replace('\n', '<br>')
            return content
        except Exception as e:
            logger.error(f"清理内容失败: {str(e)}")
            return content
            
    def stop(self):
        """停止任务"""
        self.is_running = False

class HotTab(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.content_fetcher = None
        self.refresh_timer = None
        self.current_url = None
        self.init_ui()
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 顶部控制区域
        control_layout = QHBoxLayout()
        
        # 平台选择
        platform_label = QLabel("平台:")
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(['头条', '微博', '知乎', 'B站'])
        self.platform_combo.currentTextChanged.connect(self.on_platform_changed)
        control_layout.addWidget(platform_label)
        control_layout.addWidget(self.platform_combo)
        
        # API源选择
        api_label = QLabel("API源:")
        self.api_combo = QComboBox()
        self.api_combo.addItems(['自动切换', 'vvhan', 'oioweb'])
        self.api_combo.currentTextChanged.connect(self.on_api_changed)
        control_layout.addWidget(api_label)
        control_layout.addWidget(self.api_combo)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_hot_list)
        control_layout.addWidget(self.refresh_btn)
        
        # 中断按钮
        self.stop_btn = QPushButton("中断")
        self.stop_btn.clicked.connect(self.stop_refresh)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        # 自动刷新选项
        self.auto_refresh_cb = QComboBox()
        self.auto_refresh_cb.addItems(['手动刷新', '1分钟', '5分钟', '10分钟'])
        self.auto_refresh_cb.currentTextChanged.connect(self.on_auto_refresh_changed)
        control_layout.addWidget(QLabel("自动刷新:"))
        control_layout.addWidget(self.auto_refresh_cb)
        
        # 状态信息
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: blue;")
        control_layout.addWidget(self.status_label)
        
        control_layout.addStretch()
        
        # 主界面分割布局
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧部分
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addLayout(control_layout)
        
        # 日志区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        left_layout.addWidget(self.log_text)
        
        # 热榜表格
        self.hot_table = QTableWidget()
        self.hot_table.setColumnCount(5)
        self.hot_table.setHorizontalHeaderLabels(['排名', '标题', '热度', '标签', '时间'])
        
        # 设置列宽
        header = self.hot_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        # 单击预览，双击打开
        self.hot_table.cellClicked.connect(self.on_cell_clicked)
        self.hot_table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        
        left_layout.addWidget(self.hot_table)
        
        # 右侧预览部分
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 预览控制栏
        preview_header = QHBoxLayout()
        self.preview_label = QLabel("文章预览")
        preview_header.addWidget(self.preview_label)
        
        self.preview_btn = QPushButton("打开原网页")
        self.preview_btn.clicked.connect(self.open_current_url)
        self.preview_btn.setEnabled(False)
        preview_header.addWidget(self.preview_btn)
        
        right_layout.addLayout(preview_header)
        
        # 预览区域
        self.preview_text = QTextBrowser()
        self.preview_text.setOpenExternalLinks(True)
        self.preview_text.setMinimumWidth(400)
        right_layout.addWidget(self.preview_text)
        
        # 添加左右两侧到分割器
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        
        # 设置分割器比例
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 1)
        
        layout.addWidget(main_splitter)
        self.setLayout(layout)
        
        # 自动刷新
        self.refresh_hot_list()
    def log(self, message: str):
        """添加日志"""
        current_time = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{current_time}] {message}")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        
    def refresh_hot_list(self):
        """刷新热榜"""
        try:
            if self.worker and self.worker.isRunning():
                self.stop_refresh()
                return
                
            self.refresh_btn.setText("停止")
            self.stop_btn.setEnabled(True)
            platform = self.platform_combo.currentText()
            api_source = self.api_combo.currentText()
            
            self.worker = HotWorker(platform, api_source)
            self.worker.finished.connect(self.handle_result)
            self.worker.error.connect(self.handle_error)
            self.worker.status.connect(self.handle_status)
            
            self.hot_table.setRowCount(0)
            
            self.worker.start()
            self.log(f"开始获取{platform}热榜 (使用 {api_source} API)...")
            
        except Exception as e:
            logger.error(f"刷新热榜失败: {str(e)}")
            self.log(f"刷新失败: {str(e)}")
            self.refresh_btn.setText("刷新")
            self.stop_btn.setEnabled(False)
            
    def stop_refresh(self):
        """中断刷新"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            self.refresh_btn.setText("刷新")
            self.stop_btn.setEnabled(False)
            self.log("已中断获取")
            
    def handle_status(self, status: str):
        """处理状态信息"""
        self.status_label.setText(status)
        self.log(status)
        
    def handle_result(self, hot_list):
        """处理获取到的热榜数据"""
        try:
            for item in hot_list:
                row = self.hot_table.rowCount()
                self.hot_table.insertRow(row)
                
                rank_item = QTableWidgetItem(str(item.get("rank", row + 1)))
                rank_item.setTextAlignment(Qt.AlignCenter)
                self.hot_table.setItem(row, 0, rank_item)
                
                title_item = QTableWidgetItem(item.get("title", ""))
                title_item.setData(Qt.UserRole, item.get("url", ""))
                self.hot_table.setItem(row, 1, title_item)
                
                hot_item = QTableWidgetItem(str(item.get("hot", 0)))
                hot_item.setTextAlignment(Qt.AlignCenter)
                self.hot_table.setItem(row, 2, hot_item)
                
                tag_item = QTableWidgetItem(item.get("tag", ""))
                tag_item.setTextAlignment(Qt.AlignCenter)
                self.hot_table.setItem(row, 3, tag_item)
                
                time_item = QTableWidgetItem(item.get("time", ""))
                time_item.setTextAlignment(Qt.AlignCenter)
                self.hot_table.setItem(row, 4, time_item)
                
            platform = self.platform_combo.currentText()
            status = f"{platform}热榜: {len(hot_list)} 条"
            self.status_label.setText(status)
            self.log(f"获取成功: {status}")
                
        except Exception as e:
            logger.error(f"处理热榜数据失败: {str(e)}")
            self.log(f"处理数据失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"处理热榜数据失败：{str(e)}")
            
        finally:
            self.refresh_btn.setText("刷新")
            self.stop_btn.setEnabled(False)
            
    def handle_error(self, error):
        """处理错误"""
        platform = self.platform_combo.currentText()
        error_msg = f"获取{platform}热榜失败：{error}"
        self.status_label.setText("获取失败")
        self.log(f"错误: {error_msg}")
        QMessageBox.critical(self, "错误", error_msg)
        self.refresh_btn.setText("刷新")
        self.stop_btn.setEnabled(False)
        
    def on_cell_clicked(self, row, column):
        """单击单元格预览文章"""
        try:
            title_item = self.hot_table.item(row, 1)
            if title_item:
                url = title_item.data(Qt.UserRole)
                title = title_item.text()
                if url:
                    self.current_url = url
                    self.preview_btn.setEnabled(True)
                    self.preview_label.setText("正在加载预览...")
                    self.preview_text.setHtml("<h3>正在加载文章内容，请稍候...</h3>")
                    
                    # 如果有正在进行的获取，先停止
                    if self.content_fetcher and self.content_fetcher.isRunning():
                        self.content_fetcher.stop()
                        self.content_fetcher.wait()
                    
                    # 开始新的获取
                    self.content_fetcher = ContentFetcher(url, title)
                    self.content_fetcher.content_ready.connect(self.update_preview)
                    self.content_fetcher.error.connect(self.handle_preview_error)
                    self.content_fetcher.start()
                    
        except Exception as e:
            logger.error(f"预览文章失败: {str(e)}")
            self.handle_preview_error(str(e))
            
    def update_preview(self, content: str):
        """更新预览内容"""
        self.preview_label.setText("文章预览")
        self.preview_text.setHtml(content)
        
    def handle_preview_error(self, error: str):
        """处理预览错误"""
        self.preview_label.setText("预览失败")
        self.preview_text.setHtml(f"""
        <div style='color: red;'>
            <h3>加载预览失败</h3>
            <p>{error}</p>
            <p>您可以点击"打开原网页"按钮在浏览器中查看</p>
        </div>
        """)
        
    def on_cell_double_clicked(self, row, column):
        """双击单元格打开链接"""
        try:
            title_item = self.hot_table.item(row, 1)
            if title_item:
                url = title_item.data(Qt.UserRole)
                if url:
                    webbrowser.open(url)
                    
        except Exception as e:
            logger.error(f"打开链接失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"打开链接失败：{str(e)}")
            
    def open_current_url(self):
        """打开当前预览文章的原网页"""
        if self.current_url:
            webbrowser.open(self.current_url)
            
    def on_platform_changed(self, platform):
        """平台切换处理"""
        self.refresh_hot_list()
        
    def on_api_changed(self, api_source):
        """API源切换处理"""
        self.refresh_hot_list()
        self.log(f"已切换到 {api_source} API")
        
    def on_auto_refresh_changed(self, interval):
        """自动刷新间隔改变"""
        try:
            # 清除原有定时器
            if self.refresh_timer:
                self.refresh_timer.stop()
                self.refresh_timer = None
            
            # 设置新的定时器
            if interval != '手动刷新':
                self.refresh_timer = QTimer()
                self.refresh_timer.timeout.connect(self.refresh_hot_list)
                
                # 转换时间间隔
                minutes = int(interval.replace('分钟', ''))
                self.refresh_timer.start(minutes * 60 * 1000)  # 转换为毫秒
                self.log(f"已设置{interval}自动刷新")
                
        except Exception as e:
            logger.error(f"设置自动刷新失败: {str(e)}")
            self.log(f"设置自动刷新失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"设置自动刷新失败：{str(e)}")
            
    def closeEvent(self, event):
        """窗口关闭时清理线程"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        if self.content_fetcher and self.content_fetcher.isRunning():
            self.content_fetcher.stop()
            self.content_fetcher.wait()
        if self.refresh_timer:
            self.refresh_timer.stop()
        event.accept()                