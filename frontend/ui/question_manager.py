import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QHBoxLayout, QMessageBox, QHeaderView,
                             QFileDialog, QDialog, QTextEdit, QLabel, QCheckBox,
                             QGroupBox, QProgressDialog, QApplication, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from api.client import api_client


class DownloadThread(QThread):
    """后台下载线程，避免阻塞 UI"""
    finished = pyqtSignal(str)      # 成功，返回路径
    error = pyqtSignal(str)         # 失败，返回错误信息

    def __init__(self, download_fn, *args, **kwargs):
        super().__init__()
        self.download_fn = download_fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.download_fn(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class QuestionManager(QWidget):
    """错题管理器"""

    def __init__(self):
        super().__init__()
        self._download_thread = None
        self.setup_ui()
        self.load_questions()

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)

        # ── 按钮区域 ──
        btn_layout = QHBoxLayout()

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_questions)
        btn_layout.addWidget(refresh_btn)

        delete_btn = QPushButton("删除选中")
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(delete_btn)

        # 批量导出按钮
        export_btn = QPushButton("批量导出报告")
        export_btn.setStyleSheet("font-weight: bold;")
        export_btn.clicked.connect(self.batch_export)
        btn_layout.addWidget(export_btn)

        # 导出格式选择
        btn_layout.addWidget(QLabel("格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Markdown + PDF", "仅 Markdown", "仅 PDF"])
        self.format_combo.setFixedWidth(130)
        btn_layout.addWidget(self.format_combo)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # ── 表格 ──
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["选择", "ID", "状态", "科目", "创建时间", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # ── 全选/取消全选 ──
        select_layout = QHBoxLayout()
        self.select_all_cb = QCheckBox("全选 / 取消全选")
        self.select_all_cb.stateChanged.connect(self._toggle_select_all)
        select_layout.addWidget(self.select_all_cb)
        select_layout.addStretch()

        self.selected_count_label = QLabel("已选: 0 题")
        select_layout.addWidget(self.selected_count_label)
        layout.addLayout(select_layout)

    # ─────────────────────────────────────────
    # 数据加载
    # ─────────────────────────────────────────

    def load_questions(self):
        """加载错题列表"""
        try:
            result = api_client.list_questions(page=1, page_size=50)
            questions = result.get('items', [])

            self.table.setRowCount(len(questions))

            for row, question in enumerate(questions):
                # 勾选框
                cb = QCheckBox()
                cb.stateChanged.connect(self._update_selected_count)
                self.table.setCellWidget(row, 0, cb)

                self.table.setItem(row, 1, QTableWidgetItem(str(question.get('id', ''))))
                self.table.setItem(row, 2, QTableWidgetItem(question.get('status', '')))
                self.table.setItem(row, 3, QTableWidgetItem(question.get('subject', '') or 'N/A'))
                self.table.setItem(row, 4, QTableWidgetItem(str(question.get('created_at', ''))[:19]))

                # 查看详情按钮
                detail_btn = QPushButton("查看")
                detail_btn.clicked.connect(
                    lambda checked, qid=question.get('id'): self.view_question(qid)
                )
                self.table.setCellWidget(row, 5, detail_btn)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败:\n{str(e)}")

    def refresh_questions(self):
        """刷新列表"""
        self.load_questions()

    # ─────────────────────────────────────────
    # 选择相关
    # ─────────────────────────────────────────

    def _toggle_select_all(self, state):
        """全选/取消全选"""
        checked = state == Qt.CheckState.Checked.value
        for row in range(self.table.rowCount()):
            cb = self.table.cellWidget(row, 0)
            if cb:
                cb.setChecked(checked)

    def _update_selected_count(self):
        """更新已选数量"""
        count = sum(
            1 for row in range(self.table.rowCount())
            if self.table.cellWidget(row, 0) and self.table.cellWidget(row, 0).isChecked()
        )
        self.selected_count_label.setText(f"已选: {count} 题")

    def _get_selected_ids(self) -> list:
        """获取所有勾选的题目 ID"""
        ids = []
        for row in range(self.table.rowCount()):
            cb = self.table.cellWidget(row, 0)
            if cb and cb.isChecked():
                id_item = self.table.item(row, 1)
                if id_item:
                    ids.append(int(id_item.text()))
        return ids

    # ─────────────────────────────────────────
    # 查看详情（含下载按钮）
    # ─────────────────────────────────────────

    def view_question(self, question_id: int):
        """查看错题详情"""
        try:
            question = api_client.get_question(question_id)

            dialog = QDialog(self)
            dialog.setWindowTitle(f"错题详情 - ID: {question.get('id')}")
            dialog.resize(850, 650)

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

            # OCR 结果
            ocr_title = QLabel("OCR识别结果:")
            ocr_title.setStyleSheet("font-weight: bold; font-size: 12pt;")
            layout.addWidget(ocr_title)

            ocr_text = question.get('ocr_result_md', '')
            ocr_editor = QTextEdit()
            ocr_editor.setReadOnly(True)
            if ocr_text:
                ocr_editor.setPlainText(ocr_text)
            else:
                ocr_editor.setPlainText("暂无OCR识别结果")
                ocr_editor.setStyleSheet("color: gray;")
            layout.addWidget(ocr_editor)

            # ── 下载按钮区 ──
            dl_group = QGroupBox("下载报告")
            dl_layout = QHBoxLayout(dl_group)

            md_btn = QPushButton("下载 Markdown")
            md_btn.setMinimumHeight(32)
            md_btn.clicked.connect(
                lambda: self._download_single(dialog, question_id, 'markdown')
            )
            dl_layout.addWidget(md_btn)

            pdf_btn = QPushButton("下载 PDF")
            pdf_btn.setMinimumHeight(32)
            pdf_btn.clicked.connect(
                lambda: self._download_single(dialog, question_id, 'pdf')
            )
            dl_layout.addWidget(pdf_btn)

            dl_layout.addStretch()
            layout.addWidget(dl_group)

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

    # ─────────────────────────────────────────
    # 单题下载
    # ─────────────────────────────────────────

    def _download_single(self, parent_widget, question_id: int, fmt: str):
        """单题下载报告"""
        if fmt == 'markdown':
            ext = "Markdown 文件 (*.md)"
            default_name = f"cuoti_{question_id}.md"
        else:
            ext = "PDF 文件 (*.pdf)"
            default_name = f"cuoti_{question_id}.pdf"

        save_path, _ = QFileDialog.getSaveFileName(
            parent_widget, "保存报告", default_name, ext
        )
        if not save_path:
            return

        # 显示等待提示
        progress = QProgressDialog("正在生成报告...", None, 0, 0, parent_widget)
        progress.setWindowTitle("下载中")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()

        def on_finished(path):
            progress.close()
            QMessageBox.information(
                parent_widget, "下载完成",
                f"报告已保存到:\n{path}"
            )

        def on_error(err):
            progress.close()
            QMessageBox.critical(
                parent_widget, "下载失败",
                f"下载报告时出错:\n{err}"
            )

        if fmt == 'markdown':
            self._download_thread = DownloadThread(
                api_client.download_markdown, question_id, save_path
            )
        else:
            self._download_thread = DownloadThread(
                api_client.download_pdf, question_id, save_path
            )

        self._download_thread.finished.connect(on_finished)
        self._download_thread.error.connect(on_error)
        self._download_thread.start()

    # ─────────────────────────────────────────
    # 批量导出
    # ─────────────────────────────────────────

    def batch_export(self):
        """批量导出选中题目的报告"""
        ids = self._get_selected_ids()
        if not ids:
            QMessageBox.warning(self, "提示", "请先勾选要导出的题目!")
            return

        # 确定导出格式
        fmt_idx = self.format_combo.currentIndex()
        if fmt_idx == 0:
            formats = ['markdown', 'pdf']
        elif fmt_idx == 1:
            formats = ['markdown']
        else:
            formats = ['pdf']

        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存报告包",
            f"cuoti_reports_{len(ids)}questions.zip",
            "ZIP 压缩包 (*.zip)"
        )
        if not save_path:
            return

        # 显示进度
        progress = QProgressDialog(
            f"正在生成 {len(ids)} 道题的报告...", None, 0, 0, self
        )
        progress.setWindowTitle("批量导出")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()

        def on_finished(path):
            progress.close()
            QMessageBox.information(
                self, "导出完成",
                f"已导出 {len(ids)} 道题的报告:\n{path}"
            )

        def on_error(err):
            progress.close()
            QMessageBox.critical(
                self, "导出失败",
                f"批量导出时出错:\n{err}"
            )

        self._download_thread = DownloadThread(
            api_client.download_batch_zip, ids, formats, save_path
        )
        self._download_thread.finished.connect(on_finished)
        self._download_thread.error.connect(on_error)
        self._download_thread.start()

    # ─────────────────────────────────────────
    # 删除
    # ─────────────────────────────────────────

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
                question_id = int(self.table.item(row, 1).text())
                try:
                    api_client.delete_question(question_id)
                except Exception as e:
                    QMessageBox.warning(self, "警告", f"删除ID {question_id} 失败:\n{str(e)}")

            QMessageBox.information(self, "成功", "删除完成!")
            self.refresh_questions()
