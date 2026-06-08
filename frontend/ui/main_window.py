from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                             QMessageBox, QToolBar, QAction)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

from .upload_panel import UploadPanel
from .question_manager import QuestionManager
from .system_monitor import SystemMonitor
from .settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("错题管理系统")
        self.setMinimumSize(1200, 800)
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # 初始化各面板
        self.setup_tabs()
        
        # 创建工具栏
        self.setup_toolbar()
        
        # 设置状态栏
        self.statusBar().showMessage("就绪")
    
    def setup_tabs(self):
        """设置标签页"""
        # 上传处理面板
        self.upload_panel = UploadPanel()
        self.tab_widget.addTab(self.upload_panel, "📤 上传处理")
        
        # 错题管理面板
        self.question_manager = QuestionManager()
        self.tab_widget.addTab(self.question_manager, "📚 错题管理")
        
        # 系统监控面板
        self.system_monitor = SystemMonitor()
        self.tab_widget.addTab(self.system_monitor, "📊 系统监控")
    
    def setup_toolbar(self):
        """设置工具栏"""
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)
        
        # 设置按钮
        settings_action = QAction("⚙️ 设置", self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)
        
        # 刷新按钮
        refresh_action = QAction("🔄 刷新", self)
        refresh_action.triggered.connect(self.refresh_all)
        toolbar.addAction(refresh_action)
    
    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # 配置已更新,刷新界面
            self.refresh_all()
    
    def refresh_all(self):
        """刷新所有面板"""
        self.system_monitor.refresh_data()
        self.question_manager.refresh_questions()
        self.statusBar().showMessage("已刷新", 2000)
    
    def closeEvent(self, event):
        """关闭窗口事件"""
        reply = QMessageBox.question(
            self,
            '确认退出',
            '确定要退出程序吗?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
