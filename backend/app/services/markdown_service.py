from typing import Dict, List
from .utils.logger import logger


class MarkdownService:
    """Markdown生成服务"""
    
    @staticmethod
    def generate(ocr_result: Dict, layout_result: Dict) -> str:
        """
        根据OCR结果和版面信息生成结构化Markdown
        
        Args:
            ocr_result: ppOCR的识别结果
            layout_result: ppstructure的版面分析结果
            
        Returns:
            生成的Markdown文本
        """
        try:
            markdown_parts = []
            
            # 添加标题
            markdown_parts.append("# OCR识别结果\n")
            markdown_parts.append("---\n\n")
            
            # 处理版面分析结果,按阅读顺序组织内容
            if layout_result and isinstance(layout_result, dict):
                layout_sections = layout_result.get('results', [])
                
                # 按位置排序(从上到下,从左到右)
                sorted_sections = sorted(
                    layout_sections, 
                    key=lambda x: (x.get('bbox', [0, 0, 0, 0])[1], x.get('bbox', [0, 0, 0, 0])[0])
                )
                
                for section in sorted_sections:
                    section_md = MarkdownService._convert_section_to_markdown(section)
                    if section_md:
                        markdown_parts.append(section_md)
                        markdown_parts.append("\n\n")
            
            # 如果OCR结果包含文本行信息
            if ocr_result and isinstance(ocr_result, dict):
                text_lines = ocr_result.get('rec_texts', [])
                confidences = ocr_result.get('rec_scores', [])
                
                if text_lines:
                    markdown_parts.append("## 识别文本\n\n")
                    
                    for i, (text, confidence) in enumerate(zip(text_lines, confidences)):
                        # 添加置信度较高的文本
                        if confidence > 0.5:
                            markdown_parts.append(f"{text}\n\n")
            
            # 如果没有从版面分析得到内容,直接使用OCR结果
            if len(markdown_parts) <= 3:  # 只有标题部分
                markdown_parts = MarkdownService._generate_simple_markdown(ocr_result)
            
            return ''.join(markdown_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate markdown: {str(e)}")
            return f"# OCR识别结果\n\n处理失败: {str(e)}"
    
    @staticmethod
    def _convert_section_to_markdown(section: Dict) -> str:
        """将单个版面区域转换为Markdown"""
        try:
            section_type = section.get('type', '').lower()
            text = section.get('text', '') or section.get('content', '')
            
            if not text:
                return ""
            
            # 根据类型格式化
            if 'title' in section_type or 'header' in section_type:
                # 标题
                level = section.get('level', 1)
                return f"{'#' * level} {text}"
            
            elif 'table' in section_type:
                # 表格 - 简化处理
                return f"| {text} |\n|---|"
            
            elif 'list' in section_type:
                # 列表
                lines = text.split('\n')
                return '\n'.join([f"- {line.strip()}" for line in lines if line.strip()])
            
            elif 'figure' in section_type or 'image' in section_type:
                # 图片占位符
                return "![图片](image_placeholder)"
            
            else:
                # 普通文本
                return text
                
        except Exception as e:
            logger.warning(f"Failed to convert section to markdown: {str(e)}")
            return ""
    
    @staticmethod
    def _generate_simple_markdown(ocr_result: Dict) -> List[str]:
        """生成简单的Markdown格式"""
        markdown_parts = ["# OCR识别结果\n\n"]
        
        if isinstance(ocr_result, list):
            # 如果是列表格式
            for item in ocr_result:
                if isinstance(item, dict):
                    text = item.get('text') or item.get('transcription') or ''
                    if text:
                        markdown_parts.append(f"{text}\n\n")
        
        elif isinstance(ocr_result, dict):
            # 如果是字典格式
            texts = ocr_result.get('rec_texts', [])
            for text in texts:
                if text:
                    markdown_parts.append(f"{text}\n\n")
        
        return markdown_parts
    
    @staticmethod
    def add_metadata_section(markdown: str, metadata: Dict) -> str:
        """在Markdown中添加元数据部分"""
        try:
            metadata_md = "\n---\n\n## 元数据\n\n"
            metadata_md += f"- **处理时间**: {metadata.get('processed_at', 'N/A')}\n"
            metadata_md += f"- **语言**: {metadata.get('language', 'ch')}\n"
            metadata_md += f"- **置信度**: {metadata.get('confidence', 'N/A')}\n"
            metadata_md += f"- **图片数量**: {metadata.get('image_count', 0)}\n"
            
            if metadata.get('processing_time_ms'):
                metadata_md += f"- **处理耗时**: {metadata['processing_time_ms']:.2f}ms\n"
            
            return markdown + metadata_md
            
        except Exception as e:
            logger.warning(f"Failed to add metadata: {str(e)}")
            return markdown
