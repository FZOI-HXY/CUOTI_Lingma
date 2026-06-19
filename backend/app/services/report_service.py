"""
报告生成服务
支持 Markdown (.md) 和 PDF (.pdf) 两种格式
支持单题导出和批量打包导出

PDF 生成流程：
  1. markdown 库将 Markdown 转为 HTML
  2. matplotlib 将 LaTeX 公式渲染为 PNG 图片
  3. fpdf2.write_html() 将 HTML 组装为 PDF
"""

import os
import re
import zipfile
import tempfile
import base64
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..config import settings
from ..utils.logger import logger


class ReportService:
    """报告生成服务"""

    def __init__(self):
        self.reports_dir = os.path.join(settings.PROCESSED_DIR, 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)
        self._img_counter = 0
        self._tmp_images: List[str] = []

    # ─────────────────────────────────────────
    # Markdown 报告
    # ─────────────────────────────────────────

    def generate_markdown(self, question: Dict[str, Any]) -> str:
        """为单道错题生成结构化 Markdown 报告，返回 .md 文件路径"""
        qid = question.get('id', 0)
        subject = question.get('subject') or '未分类'
        status = question.get('status', 'pending')
        tags = question.get('tags') or []
        created_at = str(question.get('created_at', ''))[:19]
        processed_at = str(question.get('processed_at', ''))[:19] if question.get('processed_at') else '未处理'

        original_image = question.get('original_image_path', '')
        layout_images = question.get('layout_images') or []
        extracted_images = question.get('extracted_images') or []
        ocr_text = question.get('ocr_result_md') or '暂无 OCR 识别结果'

        lines = []
        lines.append(f"# 错题报告 - ID {qid}\n")
        lines.append("## 基本信息\n")
        lines.append("| 字段 | 内容 |")
        lines.append("|------|------|")
        lines.append(f"| 题目 ID | {qid} |")
        lines.append(f"| 科目 | {subject} |")
        lines.append(f"| 标签 | {', '.join(tags) if tags else '无'} |")
        lines.append(f"| 状态 | {status} |")
        lines.append(f"| 创建时间 | {created_at} |")
        lines.append(f"| 处理时间 | {processed_at} |")
        lines.append("")

        if original_image and os.path.isfile(original_image):
            lines.append("## 原始图片\n")
            lines.append(f"![原始图片]({original_image})\n")

        if layout_images:
            lines.append("## 版面分析结果\n")
            for i, img_path in enumerate(layout_images, 1):
                lines.append(f"### 版面 {i}\n")
                lines.append(f"![版面 {i}]({img_path})\n")

        if extracted_images:
            lines.append("## 提取内容\n")
            for i, img_path in enumerate(extracted_images, 1):
                lines.append(f"### 提取 {i}\n")
                lines.append(f"![提取 {i}]({img_path})\n")

        lines.append("## OCR 识别结果\n")
        lines.append(ocr_text)
        lines.append("")

        lines.append("---\n")
        lines.append(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

        md_content = "\n".join(lines)

        md_dir = os.path.join(self.reports_dir, 'markdown')
        os.makedirs(md_dir, exist_ok=True)
        md_path = os.path.join(md_dir, f"question_{qid}.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.info(f"Markdown report generated: {md_path}")
        return md_path

    # ─────────────────────────────────────────
    # PDF 报告  (markdown → HTML → fpdf2)
    # ─────────────────────────────────────────

    def generate_pdf(self, question: Dict[str, Any]) -> str:
        """为单道错题生成 PDF 报告，返回 .pdf 文件路径"""
        import markdown as md_lib
        from fpdf import FPDF

        qid = question.get('id', 0)
        subject = question.get('subject') or '未分类'
        status = question.get('status', 'pending')
        tags = question.get('tags') or []
        created_at = str(question.get('created_at', ''))[:19]
        processed_at = str(question.get('processed_at', ''))[:19] if question.get('processed_at') else '未处理'
        original_image = question.get('original_image_path', '')
        layout_images = question.get('layout_images') or []
        extracted_images = question.get('extracted_images') or []
        ocr_text = question.get('ocr_result_md') or '暂无 OCR 识别结果'

        self._img_counter = 0
        self._tmp_images = []

        try:
            # ── Step 1: 构建 HTML ──
            html_parts = []

            # 标题 + 基本信息
            html_parts.append(f'<h1 style="text-align:center">错题报告 - ID {qid}</h1>')
            html_parts.append('<hr/>')
            html_parts.append('<h2>基本信息</h2>')
            html_parts.append('<table border="1" cellpadding="4" cellspacing="0">')
            info_rows = [
                ('题目 ID', str(qid)),
                ('科目', subject),
                ('标签', ', '.join(tags) if tags else '无'),
                ('状态', status),
                ('创建时间', created_at),
                ('处理时间', processed_at),
            ]
            for label, value in info_rows:
                html_parts.append(f'<tr><td><b>{label}</b></td><td>{value}</td></tr>')
            html_parts.append('</table>')

            # 原始图片
            if original_image and os.path.isfile(original_image):
                html_parts.append('<h2>原始图片</h2>')
                img_tag = self._img_to_html(original_image)
                if img_tag:
                    html_parts.append(img_tag)

            # 版面分析图片
            if layout_images:
                html_parts.append('<h2>版面分析结果</h2>')
                for i, img_path in enumerate(layout_images, 1):
                    html_parts.append(f'<h3>版面 {i}</h3>')
                    img_tag = self._img_to_html(img_path)
                    if img_tag:
                        html_parts.append(img_tag)

            # 提取内容
            if extracted_images:
                html_parts.append('<h2>提取内容</h2>')
                for i, img_path in enumerate(extracted_images, 1):
                    html_parts.append(f'<h3>提取 {i}</h3>')
                    img_tag = self._img_to_html(img_path)
                    if img_tag:
                        html_parts.append(img_tag)

            # OCR 文本 — 用 markdown 库转 HTML
            html_parts.append('<h2>OCR 识别结果</h2>')

            # 先把 LaTeX 公式替换为图片占位，再转 Markdown→HTML
            ocr_html = self._convert_latex_to_images(ocr_text)

            # markdown 库转换
            ocr_html = md_lib.markdown(ocr_html, extensions=['tables', 'fenced_code'])
            html_parts.append(ocr_html)

            # 页脚
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            html_parts.append('<hr/>')
            html_parts.append(f'<p style="text-align:center;color:gray"><i>报告生成时间: {now}</i></p>')

            full_html = '\n'.join(html_parts)

            # ── Step 2: HTML → PDF ──
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=True, margin=20)
            pdf.add_font("CN", "", r"C:\Windows\Fonts\simhei.ttf")
            pdf.add_font("CN", "B", r"C:\Windows\Fonts\simhei.ttf")
            pdf.add_font("CN", "I", r"C:\Windows\Fonts\simhei.ttf")
            pdf.add_page()
            pdf.set_font("CN", "", 10)
            pdf.write_html(full_html)

            # 写入文件
            pdf_dir = os.path.join(self.reports_dir, 'pdf')
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(pdf_dir, f"question_{qid}.pdf")
            pdf.output(pdf_path)

            logger.info(f"PDF report generated: {pdf_path}")
            return pdf_path

        finally:
            # 清理临时图片
            for tmp in self._tmp_images:
                try:
                    os.remove(tmp)
                except OSError:
                    pass

    # ─────────────────────────────────────────
    # LaTeX 公式 → PNG 图片（matplotlib 渲染）
    # ─────────────────────────────────────────

    def _render_latex_to_png(self, latex: str, display: bool = False) -> Optional[str]:
        """
        用 matplotlib 将 LaTeX 公式渲染为 PNG，返回文件路径
        display=True 为块级公式（更大字号），False 为行内公式
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            fontsize = 18 if display else 13
            fig_w = 10 if display else 6
            fig_h = 1.2 if display else 0.6

            fig, ax = plt.subplots(figsize=(fig_w, fig_h))
            ax.text(0.02 if not display else 0.5, 0.5,
                    f'${latex}$',
                    fontsize=fontsize, va='center',
                    ha='center' if display else 'left',
                    usetex=False)
            ax.axis('off')

            self._img_counter += 1
            tmp_path = os.path.join(
                tempfile.gettempdir(),
                f'_cuoti_latex_{os.getpid()}_{self._img_counter}.png'
            )
            fig.savefig(tmp_path, bbox_inches='tight', dpi=150,
                        transparent=False, facecolor='white', pad_inches=0.05)
            plt.close(fig)

            self._tmp_images.append(tmp_path)
            return tmp_path

        except Exception as e:
            logger.warning(f"LaTeX render failed: {e}")
            return None

    def _convert_latex_to_images(self, text: str) -> str:
        """
        将文本中的 LaTeX 公式替换为 <img> 标签
        $$...$$ → 块级图片，$...$ → 行内图片
        """
        # 块级公式 $$...$$
        def replace_display(m):
            latex = m.group(1).strip()
            img_path = self._render_latex_to_png(latex, display=True)
            if img_path:
                return f'\n<img src="{img_path}" width="500"/>\n'
            return f'<p><code>{latex}</code></p>'

        text = re.sub(r'\$\$(.+?)\$\$', replace_display, text, flags=re.DOTALL)

        # 行内公式 $...$
        def replace_inline(m):
            latex = m.group(1).strip()
            if not latex:
                return ''
            img_path = self._render_latex_to_png(latex, display=False)
            if img_path:
                # 用固定高度模拟行内图片
                return f'<img src="{img_path}" height="20"/>'
            return f'<code>{latex}</code>'

        text = re.sub(r'\$(.+?)\$', replace_inline, text, flags=re.DOTALL)

        return text

    def _img_to_html(self, img_path: str) -> Optional[str]:
        """将图片路径转为 HTML <img> 标签"""
        if not img_path or not os.path.isfile(img_path):
            return None
        try:
            from PIL import Image
            img = Image.open(img_path)
            w, h = img.size
            # 限制最大宽度 600px
            max_w = 600
            if w > max_w:
                ratio = max_w / w
                w = max_w
                h = int(h * ratio)
            return f'<img src="{img_path}" width="{w}" height="{h}"/>'
        except Exception as e:
            logger.warning(f"Image load failed: {e}")
            return None

    # ─────────────────────────────────────────
    # 批量打包
    # ─────────────────────────────────────────

    def generate_batch_zip(
        self,
        questions: List[Dict[str, Any]],
        formats: List[str] = None
    ) -> str:
        """批量生成报告并打包为 ZIP，返回 .zip 文件路径"""
        if formats is None:
            formats = ['markdown', 'pdf']

        zip_dir = os.path.join(self.reports_dir, 'batch')
        os.makedirs(zip_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_path = os.path.join(zip_dir, f"cuoti_reports_{timestamp}.zip")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for q in questions:
                qid = q.get('id', 0)

                if 'markdown' in formats:
                    try:
                        md_path = self.generate_markdown(q)
                        if os.path.isfile(md_path):
                            zf.write(md_path, f"question_{qid}/report.md")
                    except Exception as e:
                        logger.warning(f"Batch: skip markdown for Q{qid}: {e}")

                if 'pdf' in formats:
                    try:
                        pdf_path = self.generate_pdf(q)
                        if os.path.isfile(pdf_path):
                            zf.write(pdf_path, f"question_{qid}/report.pdf")
                    except Exception as e:
                        logger.warning(f"Batch: skip pdf for Q{qid}: {e}")

                self._add_images_to_zip(zf, q, qid)

        logger.info(f"Batch ZIP generated: {zip_path} ({len(questions)} questions)")
        return zip_path

    # ─────────────────────────────────────────
    # 辅助方法
    # ─────────────────────────────────────────

    def _add_images_to_zip(self, zf: zipfile.ZipFile, question: Dict[str, Any], qid: int):
        """将题目相关图片添加到 ZIP 中"""
        original = question.get('original_image_path', '')
        if original and os.path.isfile(original):
            ext = os.path.splitext(original)[1]
            zf.write(original, f"question_{qid}/images/original{ext}")

        for i, img_path in enumerate(question.get('layout_images') or [], 1):
            if img_path and os.path.isfile(img_path):
                ext = os.path.splitext(img_path)[1]
                zf.write(img_path, f"question_{qid}/images/layout_{i}{ext}")

        for i, img_path in enumerate(question.get('extracted_images') or [], 1):
            if img_path and os.path.isfile(img_path):
                ext = os.path.splitext(img_path)[1]
                zf.write(img_path, f"question_{qid}/images/extracted_{i}{ext}")


# 全局报告服务实例
report_service = ReportService()
