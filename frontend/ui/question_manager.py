from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QHBoxLayout, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt

from api.client import api_client


class QuestionManager(QWidget):
    """错题管理器"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_questions()
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.refresh_questions)
        btn_layout.addWidget(refresh_btn)
        
        delete_btn = QPushButton("🗑️ 删除选中")
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "状态", "科目", "创建时间", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
    
    def load_questions(self):
        """加载错题列表"""
        try:
            result = api_client.list_questions(page=1, page_size=50)
            questions = result.get('items', [])
            
            self.table.setRowCount(len(questions))
            
            for row, question in enumerate(questions):
                self.table.setItem(row, 0, QTableWidgetItem(str(question.get('id', ''))))
                self.table.setItem(row, 1, QTableWidgetItem(question.get('status', '')))
                self.table.setItem(row, 2, QTableWidgetItem(question.get('subject', '') or 'N/A'))
                self.table.setItem(row, 3, QTableWidgetItem(str(question.get('created_at', ''))[:19]))
                
                # 查看详情按钮
                detail_btn = QPushButton("查看")
                detail_btn.clicked.connect(lambda checked, qid=question.get('id'): self.view_question(qid))
                self.table.setCellWidget(row, 4, detail_btn)
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败:\n{str(e)}")
    
    def refresh_questions(self):
        """刷新列表"""
        self.load_questions()
    
    def view_question(self, question_id: int):
        """查看错题详情"""
        try:
            question = api_client.get_question(question_id)
            
            # 创建详情对话框
            from PyQt6.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QPushButton, QHBoxLayout
            from PyQt6.QtCore import Qt
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"错题详情 - ID: {question.get('id')}")
            dialog.resize(800, 600)
            
            layout = QVBoxLayout(dialog)
            
            # 基本信息
            info_text = f"ID: {question.get('id')}\n"
            info_text += f"状态: {question.get('status')}\n"
            info_text += f"科目: {question.get('subject') or 'N/A'}\n"
            info_text += f"创建时间: {str(question.get('created_at', ''))[:19]}\n"
            if question.get('processed_at'):
                info_text += f"处理时间: {str(question.get('processed_at', ''))[:19]}\n"
            info_text += f"\n原图路径: {question.get('original_image_path')}\n"
            if question.get('processed_image_path'):
                info_text += f"处理后图片: {question.get('processed_image_path')}\n"
            
            info_label = QTextEdit()
            info_label.setReadOnly(True)
            info_label.setPlainText(info_text)
            info_label.setMaximumHeight(150)
            layout.addWidget(info_label)
            
            # OCR结果标题
            from PyQt6.QtWidgets import QLabel
            ocr_title = QLabel("OCR识别结果:")
            ocr_title.setStyleSheet("font-weight: bold; font-size: 12pt;")
            layout.addWidget(ocr_title)
            
            ocr_text = question.get('ocr_result_md', '')
            if ocr_text:
                ocr_editor = QTextEdit()
                ocr_editor.setReadOnly(True)
                ocr_editor.setPlainText(ocr_text)
                layout.addWidget(ocr_editor)
            else:
                no_data = QTextEdit()
                no_data.setReadOnly(True)
                no_data.setPlainText("暂无OCR识别结果")
                no_data.setStyleSheet("color: gray;")
                layout.addWidget(no_data)
            
            # 关闭按钮
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(dialog.close)
            btn_layout.addWidget(close_btn)
            layout.addLayout(btn_layout)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取详情失败:\n{str(e)}")
    
    def delete_selected(self):
        """删除选中的错题"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的错题!")
            return
        
        reply = QMessageBox.question(
            self,
            '确认删除',
            f'确定要删除选中的 {len(selected_rows)} 条错题吗?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for index in selected_rows:
                row = index.row()
                question_id = int(self.table.item(row, 0).text())
                try:
                    api_client.delete_question(question_id)
                except Exception as e:
                    QMessageBox.warning(self, "警告", f"删除ID {question_id} 失败:\n{str(e)}")
            
            QMessageBox.information(self, "成功", "删除完成!")
            self.refresh_questions()
