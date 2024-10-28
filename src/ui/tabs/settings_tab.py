from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QGroupBox, QFormLayout,
                           QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from loguru import logger
import json
import os
import openai
import aiohttp
import asyncio

class APITestWorker(QThread):
    """API测试工作线程"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, openai_key: str = "", openai_base: str = "",
                 moonshot_key: str = "", moonshot_base: str = ""):
        super().__init__()
        self.openai_key = openai_key
        self.openai_base = openai_base
        self.moonshot_key = moonshot_key
        self.moonshot_base = moonshot_base
        
    def run(self):
        try:
            results = {}
            
            # 测试 OpenAI API
            if self.openai_key:
                openai_result = self.test_openai()
                if openai_result:
                    results['openai'] = openai_result
                    
            # 测试 Moonshot API
            if self.moonshot_key:
                moonshot_result = self.test_moonshot()
                if moonshot_result:
                    results['moonshot'] = moonshot_result
                    
            self.finished.emit(results)
            
        except Exception as e:
            logger.error(f"API测试失败: {str(e)}")
            self.error.emit(str(e))
            
    def test_openai(self) -> dict:
        """测试 OpenAI API"""
        try:
            openai.api_key = self.openai_key
            if self.openai_base:
                openai.api_base = self.openai_base
                
            # 发送测试请求
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Hello, this is a test message."}
                ],
                max_tokens=10
            )
            
            return {
                'model': response.model,
                'credits': 'Available'  # OpenAI API 不直接提供额度信息
            }
            
        except Exception as e:
            logger.error(f"OpenAI API测试失败: {str(e)}")
            return None
            
    def test_moonshot(self) -> dict:
        """测试 Moonshot API"""
        try:
            async def test_request():
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.moonshot_key}"
                }
                
                base_url = self.moonshot_base or "https://api.moonshot.cn/v1"
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{base_url}/chat/completions",
                        headers=headers,
                        json={
                            "model": "moonshot-v1-8k",
                            "messages": [
                                {"role": "user", "content": "Hello, this is a test message."}
                            ]
                        }
                    ) as response:
                        result = await response.json()
                        return result
                        
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(test_request())
            loop.close()
            
            return {
                'model': result['model'],
                'credits': 'Available'  # Moonshot API 也不直接提供额度信息
            }
            
        except Exception as e:
            logger.error(f"Moonshot API测试失败: {str(e)}")
            return None

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.config_file = "config/api_config.json"
        self.test_worker = None
        self.init_ui()
        self.load_config()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # API设置组
        api_group = QGroupBox("API 设置")
        form_layout = QFormLayout()
        
        # OpenAI API设置
        self.openai_key = QLineEdit()
        self.openai_key.setEchoMode(QLineEdit.Password)  # 密码模式显示
        self.openai_base = QLineEdit()
        self.openai_base.setPlaceholderText("https://api.openai.com/v1")
        self.openai_model = QLineEdit()
        self.openai_model.setPlaceholderText("gpt-3.5-turbo")
        
        form_layout.addRow("OpenAI API Key:", self.openai_key)
        form_layout.addRow("OpenAI API Base:", self.openai_base)
        form_layout.addRow("OpenAI Model:", self.openai_model)
        
        # Moonshot API设置
        self.moonshot_key = QLineEdit()
        self.moonshot_key.setEchoMode(QLineEdit.Password)
        self.moonshot_base = QLineEdit()
        self.moonshot_base.setPlaceholderText("https://api.moonshot.cn/v1")
        self.moonshot_model = QLineEdit()
        self.moonshot_model.setPlaceholderText("moonshot-v1-8k")
        
        form_layout.addRow("Moonshot API Key:", self.moonshot_key)
        form_layout.addRow("Moonshot API Base:", self.moonshot_base)
        form_layout.addRow("Moonshot Model:", self.moonshot_model)
        
        api_group.setLayout(form_layout)
        layout.addWidget(api_group)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("保存设置")
        self.save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(self.save_btn)
        
        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self.test_connection)
        btn_layout.addWidget(self.test_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 添加说明文本
        note_label = QLabel("""
        <p style='color: #666;'>
        注意事项：
        <ul>
            <li>API Key 会以加密形式保存在本地配置文件中</li>
            <li>如果不填写 API Base，将使用默认地址</li>
            <li>如果不填写 Model，将使用默认模型</li>
            <li>OpenAI 和 Moonshot 可以只配置其中一个</li>
        </ul>
        </p>
        """)
        note_label.setTextFormat(Qt.RichText)
        layout.addWidget(note_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_config(self):
        """加载配置"""
        try:
            if not os.path.exists("config"):
                os.makedirs("config")
                
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # OpenAI配置
                self.openai_key.setText(config.get('openai', {}).get('api_key', ''))
                self.openai_base.setText(config.get('openai', {}).get('api_base', ''))
                self.openai_model.setText(config.get('openai', {}).get('model', ''))
                
                # Moonshot配置
                self.moonshot_key.setText(config.get('moonshot', {}).get('api_key', ''))
                self.moonshot_base.setText(config.get('moonshot', {}).get('api_base', ''))
                self.moonshot_model.setText(config.get('moonshot', {}).get('model', ''))
                
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}")
            QMessageBox.warning(self, "警告", f"加载配置失败：{str(e)}")
            
    def save_config(self):
        """保存配置"""
        try:
            config = {
                'openai': {
                    'api_key': self.openai_key.text().strip(),
                    'api_base': self.openai_base.text().strip(),
                    'model': self.openai_model.text().strip()
                },
                'moonshot': {
                    'api_key': self.moonshot_key.text().strip(),
                    'api_base': self.moonshot_base.text().strip(),
                    'model': self.moonshot_model.text().strip()
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
            QMessageBox.information(self, "成功", "配置已保存")
            
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"保存配置失败：{str(e)}")
            
    def test_connection(self):
        """测试API连接"""
        try:
            # 禁用按钮，防止重复点击
            self.test_btn.setEnabled(False)
            self.test_btn.setText("测试中...")
            
            # 创建测试线程
            self.test_worker = APITestWorker(
                openai_key=self.openai_key.text().strip(),
                openai_base=self.openai_base.text().strip(),
                moonshot_key=self.moonshot_key.text().strip(),
                moonshot_base=self.moonshot_base.text().strip()
            )
            self.test_worker.finished.connect(self.handle_test_result)
            self.test_worker.error.connect(self.handle_test_error)
            self.test_worker.start()
            
        except Exception as e:
            logger.error(f"启动API测试失败: {str(e)}")
            self.handle_test_error(str(e))
            
    def handle_test_result(self, results: dict):
        """处理测试结果"""
        try:
            message = "API 测试结果:\n\n"
            
            # OpenAI 测试结果
            if results.get('openai'):
                message += "✅ OpenAI API 连接成功\n"
                message += f"- 模型: {results['openai'].get('model', 'unknown')}\n"
                message += f"- 剩余额度: {results['openai'].get('credits', 'unknown')}\n\n"
            
            # Moonshot 测试结果
            if results.get('moonshot'):
                message += "✅ Moonshot API 连接成功\n"
                message += f"- 模型: {results['moonshot'].get('model', 'unknown')}\n"
                message += f"- 剩余额度: {results['moonshot'].get('credits', 'unknown')}\n"
                
            if not (results.get('openai') or results.get('moonshot')):
                message = "❌ 未配置任何可用的 API"
                
            QMessageBox.information(self, "测试结果", message)
            
        except Exception as e:
            logger.error(f"处理测试结果失败: {str(e)}")
            self.handle_test_error(str(e))
            
        finally:
            self.test_btn.setEnabled(True)
            self.test_btn.setText("测试连接")
            
    def handle_test_error(self, error: str):
        """处理测试错误"""
        QMessageBox.critical(self, "测试失败", f"API 测试失败：{error}")
        self.test_btn.setEnabled(True)
        self.test_btn.setText("测试连接")