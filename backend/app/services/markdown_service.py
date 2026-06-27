# DEPRECATED: This module is not used. Functionality has been absorbed by ocr_service.py and archive_service.py.
# Safe to remove after verifying no external references.

from typing import Dict, List
from app.utils.logger import logger


class MarkdownService:
    """Markdown 工具服务

    注意: PP-StructureV3 已内置 save_to_markdown()，主要的 Markdown 生成
    逻辑已迁移至 ocr_service.py。本类仅保留少量辅助方法供独立调用。
    """

    @staticmethod
    def add_metadata_section(markdown: str, metadata: Dict) -> str:
        """在 Markdown 末尾追加元数据区段"""
        try:
            lines = [
                "\n---\n",
                f"- **处理时间**: {metadata.get('processed_at', 'N/A')}",
                f"- **语言**: {metadata.get('language', 'ch')}",
                f"- **置信度**: {metadata.get('confidence', 'N/A')}",
                f"- **图片数量**: {metadata.get('image_count', 0)}",
            ]
            ms = metadata.get('processing_time_ms')
            if ms:
                lines.append(f"- **处理耗时**: {ms:.2f}ms")
            return markdown + '\n'.join(lines) + '\n'
        except Exception as e:
            logger.warning(f"Failed to add metadata: {e}")
            return markdown

    @staticmethod
    def from_parsing_results(parsing_res_list: List[Dict]) -> str:
        """将 PP-StructureV3 的 parsing_res_list 简单转换为 Markdown

        此方法作为 PP-StructureV3 save_to_markdown() 的降级备选。
        """
        try:
            parts = ["# OCR 识别结果\n\n"]
            for block in parsing_res_list:
                label = str(block.get('block_label', '')).lower()
                content = block.get('block_content', '')
                if not content:
                    continue
                if 'title' in label or 'header' in label:
                    level = block.get('level', 2)
                    parts.append(f"{'#' * level} {content}\n\n")
                elif 'table' in label:
                    parts.append(f"{content}\n\n")
                elif label in ('figure', 'image', 'chart'):
                    parts.append("![图片](image_placeholder)\n\n")
                else:
                    parts.append(f"{content}\n\n")
            return ''.join(parts)
        except Exception as e:
            logger.error(f"Failed to generate markdown from parsing results: {e}")
            return "# OCR 识别结果\n\n生成失败\n"
