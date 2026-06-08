from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QTextEdit, QProgressBar,
                             QMessageBox, QSplitter, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
import os
import time

from ..api.client import api_client


class UploadWorker(QThread):
    """上传和处理工作线程"""
    progress_updated = pyqtSignal(int, str)
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
    
    def run(self):
        try:
            # Step 1: 上传文件
            self.progress_updated.emit(10, "正在上传文件...")
            upload_result = api_client.upload_image(self.file_path)
            
            # Step 2: 启动OCR处理
            self.progress_updated.emit(30, "正在启动OCR处理...")
            ocr_result = api_client.process_ocr(upload_result['file_id'])
            task_id = ocr_result['task_id']
            
            # Step 3: 轮询任务状态
            self.progress_updated.emit(50, "正在处理中...")
            while True:
                status = api_client.get_task_status(task_id)
                
                if status.get('progress', 0) >= 100:
                    self.progress_updated.emit(100, "处理完成!")
                    self.result_ready.emit(status)
                    break
                
                elif status.get('progress', 0) == -1:
                    raise Exception(status.get('message', 'Processing failed'))
                
                else:
                    progress = status.get('progress', 50)
                    message = status.get('message', 'Processing...')
                    self.progress_updated.emit(progress, message)
                    time.sleep(1)  # 每秒查询一次
        
        except Exception as e:
            self.error_occurred.emit(str(e))


class UploadPanel(QWidget):
    """上传处理面板"""
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        main_layout = QVBoxLayout(self)
        
        # 文件选择区域
        file_group = QGroupBox("📁 文件选择")
        file_layout = QVBoxLayout()
        
        self.file_label = QLabel("未选择文件")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_layout.addWidget(self.file_label)
        
        select_btn = QPushButton("选择图片文件")
        select_btn.clicked.connect(self.select_file)
        file_layout.addWidget(select_btn)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 进度显示区域
        progress_group = QGroupBox("⚙️ 处理进度")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # 结果显示区域
        result_group = QGroupBox("📄 OCR结果")
        result_layout = QVBoxLayout()
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        result_layout.addWidget(self.result_text)
        
        # 保存按钮
        save_btn = QPushButton("💾 保存结果")
        save_btn.clicked.connect(self.save_result)
        result_layout.addWidget(save_btn)
        
        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group)
        
        # 处理按钮
        process_btn = QPushButton("🚀 开始处理")
        process_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; font-weight: bold; }")
        process_btn.clicked.connect(self.start_processing)
        main_layout.addWidget(process_btn)
    
    def select_file(self):
        """选择文件"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "选择图片文件",
            "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.webp)"
        )
        
        if file_path:
            self.current_file = file_path
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) / 1024  # KB
            self.file_label.setText(f"已选择: {filename}\n大小: {file_size:.2f} KB")
    
    def start_processing(self):
        """开始处理"""
        if not self.current_file:
            QMessageBox.warning(self, "警告", "请先选择文件!")
            return
        
        # 检查后端连接
        if not api_client.health_check():
            QMessageBox.critical(self, "错误", "无法连接到后端服务!\n请确保后端服务已启动。")
            return
        
        # 创建工作线程
        self.worker = UploadWorker(self.current_file)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.result_ready.connect(self.on_result_ready)
        self.worker.error_occurred.connect(self.on_error_occurred)
        self.worker.start()
    
    def on_progress_updated(self, progress: int, message: str):
        """进度更新"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
    
    def on_result_ready(self, result: dict):
        """处理完成"""
        self.result_text.setText("处理完成!\n\n请查看数据库获取完整结果。")
        QMessageBox.information(self, "成功", "OCR处理完成!")
    
    def on_error_occurred(self, error_message: str):
        """发生错误"""
        QMessageBox.critical(self, "错误", f"处理失败:\n{error_message}")
        self.progress_bar.setValue(0)
        self.status_label.setText("处理失败")
    
    def save_result(self):
        """保存结果"""
        if not self.result_text.toPlainText():
            QMessageBox.warning(self, "警告", "没有可保存的结果!")
            return
        
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self,
            "保存结果",
            "",
            "Markdown文件 (*.md);;文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.result_text.toPlainText())
                QMessageBox.information(self, "成功", "结果已保存!")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")
