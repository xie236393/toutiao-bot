from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                           QPushButton, QLabel, QTableWidgetItem, QHeaderView,
                           QMessageBox, QDialog, QLineEdit, QFormLayout)
from PyQt5.QtCore import Qt
from loguru import logger
import json
from pathlib import Path
from datetime import datetime

class AddAccountDialog(QDialog):
    """添加账号对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("添加账号")
        self.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        # 账号名称
        self.name_input = QLineEdit()
        layout.addRow("账号名称:", self.name_input)
        
        # Token
        self.token_input = QLineEdit()
        layout.addRow("Token:", self.token_input)
        
        # 备注
        self.note_input = QLineEdit()
        layout.addRow("备注:", self.note_input)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addRow(btn_layout)
        
        self.setLayout(layout)
        
    def get_account_data(self) -> dict:
        """获取账号数据"""
        return {
            "name": self.name_input.text().strip(),
            "token": self.token_input.text().strip(),
            "note": self.note_input.text().strip(),
            "status": "未验证",
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

class AccountTab(QWidget):
    def __init__(self):
        super().__init__()
        self.accounts_file = Path("data/accounts.json")
        self.last_account_file = Path("data/last_account.json")
        self.current_account = self.load_last_account()  # 加载上次使用的账号
        self.init_ui()
        self.load_accounts()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 顶部说明
        tip_label = QLabel("提示：Token通常在cookie中,格式如: MS4wLjABAAAAxxx...")
        tip_label.setStyleSheet("color: gray;")
        layout.addWidget(tip_label)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("添加账号")
        self.add_btn.clicked.connect(self.add_account)
        
        self.delete_btn = QPushButton("删除账号")
        self.delete_btn.clicked.connect(self.delete_account)
        
        self.check_btn = QPushButton("检查Token")
        self.check_btn.clicked.connect(self.check_token)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.check_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 账号列表
        self.account_table = QTableWidget()
        self.account_table.setColumnCount(5)  # 增加一列用于操作按钮
        self.account_table.setHorizontalHeaderLabels(['账号名称', 'Token', '状态', '备注', '操作'])
        
        # 设置列宽
        header = self.account_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.account_table)
        
        # 当前账号显示
        self.current_account_label = QLabel("当前账号：未选择")
        self.current_account_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(self.current_account_label)
        
        # 底部状态
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)

    def load_accounts(self):
        """加载账号列表"""
        try:
            self.account_table.setRowCount(0)
            
            if not self.accounts_file.exists():
                return
                
            with open(self.accounts_file, "r", encoding="utf-8") as f:
                accounts = json.load(f)
                
            for account in accounts:
                row = self.account_table.rowCount()
                self.account_table.insertRow(row)
                
                # 账号名称
                name_item = QTableWidgetItem(account.get("name", ""))
                self.account_table.setItem(row, 0, name_item)
                
                # Token
                self.account_table.setItem(row, 1, QTableWidgetItem(account.get("token", "")))
                
                # 状态
                status = account.get("status", "未验证")
                status_item = QTableWidgetItem(status)
                if status == "有效":
                    status_item.setForeground(Qt.green)
                elif status == "无效":
                    status_item.setForeground(Qt.red)
                self.account_table.setItem(row, 2, status_item)
                
                # 备注
                self.account_table.setItem(row, 3, QTableWidgetItem(account.get("note", "")))
                
                # 操作按钮
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(2, 2, 2, 2)
                
                # 激活按钮
                activate_btn = QPushButton("激活")
                activate_btn.setFixedWidth(60)
                activate_btn.clicked.connect(lambda checked, a=account: self.activate_account(a))
                
                # 如果是当前账号，禁用激活按钮
                if self.current_account and account.get("token") == self.current_account.get("token"):
                    activate_btn.setEnabled(False)
                    name_item.setBackground(Qt.lightGray)
                
                btn_layout.addWidget(activate_btn)
                btn_layout.addStretch()
                
                self.account_table.setCellWidget(row, 4, btn_widget)
                
            self.status_label.setText(f"共 {len(accounts)} 个账号")
            
            # 更新当前账号显示
            if self.current_account:
                self.current_account_label.setText(f"当前账号：{self.current_account.get('name', '未知')}")
            
        except Exception as e:
            logger.error(f"加载账号列表失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载账号列表失败：{str(e)}")
            
    def add_account(self):
        """添加账号"""
        try:
            dialog = AddAccountDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                account = dialog.get_account_data()
                
                # 验证必填信息
                if not account["name"] or not account["token"]:
                    QMessageBox.warning(self, "警告", "账号名称和Token不能为空")
                    return
                    
                # 保存账号
                accounts = []
                if self.accounts_file.exists():
                    with open(self.accounts_file, "r", encoding="utf-8") as f:
                        accounts = json.load(f)
                        
                accounts.append(account)
                
                with open(self.accounts_file, "w", encoding="utf-8") as f:
                    json.dump(accounts, f, ensure_ascii=False, indent=2)
                    
                # 刷新列表
                self.load_accounts()
                
                QMessageBox.information(self, "成功", "添加账号成功")
                
        except Exception as e:
            logger.error(f"添加账号失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"添加账号失败：{str(e)}")
            
    def delete_account(self):
        """删除账号"""
        try:
            current_row = self.account_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "警告", "请先选择要删除的账号")
                return
                
            # 获取账号信息
            name = self.account_table.item(current_row, 0).text()
            token = self.account_table.item(current_row, 1).text()
            
            # 确认删除
            reply = QMessageBox.question(
                self, 
                "确认", 
                f"确定要删除账号 {name} 吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 读取账号列表
                with open(self.accounts_file, "r", encoding="utf-8") as f:
                    accounts = json.load(f)
                    
                # 删除账号
                accounts = [a for a in accounts if a.get("token") != token]
                
                # 保存更新后的账号列表
                with open(self.accounts_file, "w", encoding="utf-8") as f:
                    json.dump(accounts, f, ensure_ascii=False, indent=2)
                    
                # 如果删除的是当前账号，清除当前账号
                if self.current_account and self.current_account.get("token") == token:
                    self.current_account = None
                    if self.last_account_file.exists():
                        self.last_account_file.unlink()
                    
                # 刷新列表
                self.load_accounts()
                
                QMessageBox.information(self, "成功", "删除账号成功")
                
        except Exception as e:
            logger.error(f"删除账号失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"删除账号失败：{str(e)}")
            
    def check_token(self):
        """检查Token有效性"""
        try:
            current_row = self.account_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "警告", "请先选择要检查的账号")
                return
                
            # 获取Token
            token = self.account_table.item(current_row, 1).text()
            
            # TODO: 实现Token检查逻辑
            # 这里需要调用API检查Token是否有效
            
            QMessageBox.information(self, "提示", "Token检查功能开发中...")
            
        except Exception as e:
            logger.error(f"检查Token失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"检查Token失败：{str(e)}")
            
    def activate_account(self, account: dict):
        """激活账号"""
        try:
            # 更新当前账号
            self.current_account = account.copy()
            
            # 保存最后使用的账号
            with open(self.last_account_file, "w", encoding="utf-8") as f:
                json.dump(self.current_account, f, ensure_ascii=False, indent=2)
            
            # 刷新列表
            self.load_accounts()
            
            QMessageBox.information(self, "成功", f"已激活账号：{account['name']}")
            
        except Exception as e:
            logger.error(f"激活账号失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"激活账号失败：{str(e)}")
            
    def load_last_account(self) -> dict:
        """加载上次使用的账号"""
        try:
            if self.last_account_file.exists():
                with open(self.last_account_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"加载上次使用的账号失败: {str(e)}")
            return None