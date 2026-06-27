"""
归档存储服务 - 将处理产物归档到 storage 目录

归档目录结构:
  storage/
    questions/{id}/
      original.{ext}          - 原始上传文件
      result.md               - OCR/VL 识别结果 Markdown
      metadata.json           - 处理元数据
      layout/                 - 版面分析可视化图片
        layout_det_res.png
        layout_order_res.png
        overall_ocr_res.png
        region_det_res.png
      extracted/              - 文档内嵌提取图片
        extracted_01_image.jpg
        ...
    exports/                  - 报告导出文件（由报告服务生成）
      markdown/question_{id}.md
      pdf/question_{id}.pdf
      batch/...
"""

import os
import json
import shutil
import zipfile
import time
from pathlib import Path
from typing import Dict, List, Optional

from ..config import settings
from ..utils.logger import logger


class ArchiveService:
    """归档存储服务"""

    @staticmethod
    def _question_dir(question_id: int) -> Path:
        """获取题目归档目录"""
        d = Path(settings.STORAGE_DIR) / "questions" / str(question_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    @staticmethod
    def archive_question(
        question_id: int,
        original_image_path: str,
        ocr_result_md: str,
        layout_images: List[str],
        extracted_images: List[str],
        metadata: Optional[Dict] = None,
    ) -> Dict[str, str]:
        """
        将一道题目的全部处理产物归档到 storage 目录。

        Returns:
            归档后的相对路径映射 (相对于 STORAGE_DIR)
        """
        qdir = ArchiveService._question_dir(question_id)
        archived: Dict[str, str] = {}

        # 1. 归档原始图片
        if original_image_path:
            src = ArchiveService._resolve_path(original_image_path, settings.UPLOAD_DIR)
            if src and os.path.isfile(src):
                ext = Path(src).suffix
                dst = qdir / f"original{ext}"
                shutil.copy2(src, dst)
                archived["original"] = f"questions/{question_id}/original{ext}"
                logger.debug(f"Archived original -> {dst}")

        # 2. 写入 Markdown 结果
        if ocr_result_md:
            md_path = qdir / "result.md"
            md_path.write_text(ocr_result_md, encoding="utf-8")
            archived["result_md"] = f"questions/{question_id}/result.md"

        # 3. 归档版面分析图片
        if layout_images:
            layout_dir = qdir / "layout"
            layout_dir.mkdir(exist_ok=True)
            archived_layouts = []
            for img_path in layout_images:
                src = ArchiveService._resolve_path(img_path, settings.PROCESSED_DIR)
                if src and os.path.isfile(src):
                    fname = Path(src).name
                    dst = layout_dir / fname
                    shutil.copy2(src, dst)
                    archived_layouts.append(f"questions/{question_id}/layout/{fname}")
            if archived_layouts:
                archived["layout_images"] = archived_layouts
                logger.debug(f"Archived {len(archived_layouts)} layout images")

        # 4. 归档提取图片
        if extracted_images:
            ext_dir = qdir / "extracted"
            ext_dir.mkdir(exist_ok=True)
            archived_extracted = []
            for img_path in extracted_images:
                src = ArchiveService._resolve_path(img_path, settings.PROCESSED_DIR)
                if src and os.path.isfile(src):
                    fname = Path(src).name
                    dst = ext_dir / fname
                    shutil.copy2(src, dst)
                    archived_extracted.append(f"questions/{question_id}/extracted/{fname}")
            if archived_extracted:
                archived["extracted_images"] = archived_extracted
                logger.debug(f"Archived {len(archived_extracted)} extracted images")

        # 5. 写入元数据
        meta = metadata or {}
        meta["archived_at"] = time.time()
        meta["question_id"] = question_id
        meta_path = qdir / "metadata.json"
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        archived["metadata"] = f"questions/{question_id}/metadata.json"

        logger.info(f"Question {question_id} archived: {len(archived)} entries")
        return archived

    @staticmethod
    def get_question_files(question_id: int) -> Optional[Dict]:
        """
        获取一道题目的归档文件清单。

        Returns:
            {
                "original": "relative/path",
                "result_md": "relative/path",
                "layout_images": ["rel/path1", ...],
                "extracted_images": ["rel/path1", ...],
                "metadata": "relative/path"
            }
            如果未归档则返回 None
        """
        qdir = Path(settings.STORAGE_DIR) / "questions" / str(question_id)
        if not qdir.exists():
            return None

        result: Dict = {}

        # original
        for f in qdir.glob("original.*"):
            if f.is_file():
                result["original"] = f"questions/{question_id}/{f.name}"
                break

        # result.md
        md = qdir / "result.md"
        if md.is_file():
            result["result_md"] = f"questions/{question_id}/result.md"

        # layout
        layout_dir = qdir / "layout"
        if layout_dir.is_dir():
            result["layout_images"] = [
                f"questions/{question_id}/layout/{f.name}"
                for f in sorted(layout_dir.iterdir()) if f.is_file()
            ]

        # extracted
        ext_dir = qdir / "extracted"
        if ext_dir.is_dir():
            result["extracted_images"] = [
                f"questions/{question_id}/extracted/{f.name}"
                for f in sorted(ext_dir.iterdir()) if f.is_file()
            ]

        # metadata
        meta = qdir / "metadata.json"
        if meta.is_file():
            result["metadata"] = f"questions/{question_id}/metadata.json"

        return result if result else None

    @staticmethod
    def create_download_zip(question_id: int) -> Optional[str]:
        """
        将一道题目的全部归档文件打包为 ZIP。

        Returns:
            ZIP 文件的绝对路径, 或 None
        """
        qdir = Path(settings.STORAGE_DIR) / "questions" / str(question_id)
        if not qdir.exists():
            return None

        zip_dir = Path(settings.STORAGE_DIR) / "exports" / "zip"
        zip_dir.mkdir(parents=True, exist_ok=True)
        zip_path = zip_dir / f"question_{question_id}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(qdir):
                for fname in files:
                    full = os.path.join(root, fname)
                    arcname = os.path.relpath(full, qdir)
                    zf.write(full, arcname)

        logger.info(f"Created ZIP: {zip_path}")
        return str(zip_path)

    @staticmethod
    def create_batch_zip(question_ids: List[int]) -> Optional[str]:
        """批量打包多道题目"""
        zip_dir = Path(settings.STORAGE_DIR) / "exports" / "zip"
        zip_dir.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        zip_path = zip_dir / f"cuoti_batch_{ts}.zip"

        count = 0
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for qid in question_ids:
                qdir = Path(settings.STORAGE_DIR) / "questions" / str(qid)
                if not qdir.exists():
                    continue
                for root, dirs, files in os.walk(qdir):
                    for fname in files:
                        full = os.path.join(root, fname)
                        arcname = os.path.join(f"question_{qid}", os.path.relpath(full, qdir))
                        zf.write(full, arcname)
                        count += 1

        if count == 0:
            zip_path.unlink(missing_ok=True)
            return None

        logger.info(f"Created batch ZIP: {zip_path} ({count} files)")
        return str(zip_path)

    @staticmethod
    def delete_question_archive(question_id: int):
        """删除一道题目的归档"""
        qdir = Path(settings.STORAGE_DIR) / "questions" / str(question_id)
        if qdir.exists():
            shutil.rmtree(qdir)
            logger.info(f"Deleted archive for question {question_id}")

    @staticmethod
    def _resolve_path(path: str, base_dir: str) -> Optional[str]:
        """
        解析文件路径：
        - 如果是绝对路径且文件存在 -> 直接使用
        - 如果是 ./processed/xxx -> 拼接 PROCESSED_DIR
        - 如果是纯文件名 -> 拼接 base_dir
        """
        if not path:
            return None

        # 已经是存在的绝对路径
        if os.path.isabs(path) and os.path.isfile(path):
            return path

        # 相对路径 ./processed/xxx 或 processed/xxx
        normalized = path.replace("\\", "/")
        if normalized.startswith("./"):
            normalized = normalized[2:]

        # 尝试拼接项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )))

        candidates = [
            os.path.join(project_root, "backend", normalized),
            os.path.join(project_root, normalized),
            os.path.join(base_dir, normalized),
            os.path.join(base_dir, os.path.basename(normalized)),
        ]

        for c in candidates:
            if os.path.isfile(c):
                return c

        return None


# 全局实例
archive_service = ArchiveService()
