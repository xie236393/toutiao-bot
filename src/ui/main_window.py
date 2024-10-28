from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QMessageBox, 
                           QMenuBar, QMenu, QAction, QStatusBar)
from PyQt5.QtCore import Qt
from loguru import logger
from .tabs.main_tab import MainTab
from .tabs.account_tab import AccountTab
from .tabs.ai_tab import AITab
from .tabs.article_tab import ArticleTab
from .tabs.hot_tab import HotTab
from .tabs.settings_tab import SettingsTab
import webbrowser

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 设置窗口标题和大小
        self.setWindowTitle('头条号助手')
        self.resize(1200, 800)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('就绪')
        
        # 创建标签页
        self.tabs = QTabWidget()
        self.main_tab = MainTab()
        self.account_tab = AccountTab()
        self.ai_tab = AITab()
        self.article_tab = ArticleTab()
        self.hot_tab = HotTab()
        self.settings_tab = SettingsTab()
        
        # 添加标签页
        self.tabs.addTab(self.main_tab, "主页")
        self.tabs.addTab(self.account_tab, "账号管理")
        self.tabs.addTab(self.ai_tab, "AI改写")
        self.tabs.addTab(self.article_tab, "文章管理")
        self.tabs.addTab(self.hot_tab, "热点获取")
        self.tabs.addTab(self.settings_tab, "设置")
        
        # 监听标签页切换
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        self.setCentralWidget(self.tabs)
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        # 导入配置
        import_action = QAction('导入配置', self)
        import_action.setStatusTip('导入配置文件')
        import_action.triggered.connect(self.import_config)
        file_menu.addAction(import_action)
        
        # 导出配置
        export_action = QAction('导出配置', self)
        export_action.setStatusTip('导出配置文件')
        export_action.triggered.connect(self.export_config)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction('退出', self)
        exit_action.setStatusTip('退出应用')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        # 使用说明
        guide_action = QAction('使用说明', self)
        guide_action.setStatusTip('查看使用说明')
        guide_action.triggered.connect(self.show_guide)
        help_menu.addAction(guide_action)
        
        # 关于
        about_action = QAction('关于', self)
        about_action.setStatusTip('关于本软件')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def on_tab_changed(self, index):
        """标签页切换时刷新数据"""
        try:
            current_tab = self.tabs.widget(index)
            
            # 如果切换到 AI 改写标签页，刷新账号状态
            if isinstance(current_tab, AITab):
                logger.info("切换到 AI 改写标签页，刷新账号状态")
                current_tab.load_current_account()
                
        except Exception as e:
            logger.error(f"标签页切换处理失败: {str(e)}")
            
    def import_config(self):
        """导入配置"""
        try:
            # TODO: 实现配置导入功能
            QMessageBox.information(self, "提示", "配置导入功能开发中...")
        except Exception as e:
            logger.error(f"导入配置失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"导入配置失败：{str(e)}")
            
    def export_config(self):
        """导出配置"""
        try:
            # TODO: 实现配置导出功能
            QMessageBox.information(self, "提示", "配置导出功能开发中...")
        except Exception as e:
            logger.error(f"导出配置失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"导出配置失败：{str(e)}")
            
    def show_guide(self):
        """显示使用说明"""
        try:
            # TODO: 打开使用说明网页或文档
            webbrowser.open('https://github.com/your-repo/toutiao-bot/wiki')
        except Exception as e:
            logger.error(f"打开使用说明失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"打开使用说明失败：{str(e)}")
            
    def show_about(self):
        """显示关于对话框"""
        try:
            QMessageBox.about(
                self,
                "关于头条号助手",
                """
                <h3>头条号助手 v1.0</h3>
                <p>一个帮助头条号运营的自动化工具</p>
                <p>
                    <b>功能特点：</b>
                    <ul>
                        <li>AI文章改写</li>
                        <li>文章批量发布</li>
                        <li>热点内容获取</li>
                        <li>多账号管理</li>
                    </ul>
                </p>
                <p>Copyright © 2024</p>
                """
            )
        except Exception as e:
            logger.error(f"显示关于对话框失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"显示关于对话框失败：{str(e)}")
            
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            reply = QMessageBox.question(
                self, 
                '确认', 
                "确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
                
        except Exception as e:
            logger.error(f"处理关闭事件失败: {str(e)}")
            event.accept()