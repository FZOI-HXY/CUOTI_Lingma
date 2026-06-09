from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QMessageBox,
                             QSpinBox, QComboBox)
from PyQt6.QtCore import Qt

from config.settings import app_settings


class SettingsDialog(QDialog):
    """配置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统设置")
        self.setMinimumWidth(500)
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # 后端URL
        self.backend_url_input = QLineEdit()
        form_layout.addRow("后端地址:", self.backend_url_input)
        
        # API版本
        self.api_version_input = QLineEdit()
        form_layout.addRow("API版本:", self.api_version_input)
        
        # 最大文件大小
        self.max_file_size_input = QSpinBox()
        self.max_file_size_input.setRange(1, 100)
        self.max_file_size_input.setValue(10)
        self.max_file_size_input.setSuffix(" MB")
        form_layout.addRow("最大文件大小:", self.max_file_size_input)
        
        # 日志级别
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        form_layout.addRow("日志级别:", self.log_level_combo)
        
        layout.addLayout(form_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 保存")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def load_settings(self):
        """加载配置"""
        self.backend_url_input.setText(app_settings.get('backend_url', 'http://localhost:8001'))
        self.api_version_input.setText(app_settings.get('api_version', '/api/v1'))
        self.max_file_size_input.setValue(app_settings.get('max_file_size_mb', 10))
        self.log_level_combo.setCurrentText(app_settings.get('log_level', 'INFO'))
    
    def save_settings(self):
        """保存配置"""
        try:
            app_settings.set('backend_url', self.backend_url_input.text())
            app_settings.set('api_version', self.api_version_input.text())
            app_settings.set('max_file_size_mb', self.max_file_size_input.value())
            app_settings.set('log_level', self.log_level_combo.currentText())
            
            QMessageBox.information(self, "成功", "配置已保存!\n重启应用后生效。")
            self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")
