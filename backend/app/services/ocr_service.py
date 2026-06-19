import os
import time
import json
import shutil
from typing import Dict, List, Optional
from datetime import datetime, timezone

# ── 必须在导入 paddle 之前设置 ──────────────────────────
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['MKLDNN_ENABLED'] = '0'
# 禁止 PaddleX 默认使用 mkldnn（绕过 PaddlePaddle 3.3.1 oneDNN PIR bug）
os.environ['PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT'] = 'False'
# 跳过模型源连通性检查，加速初始化
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'

from ..config import settings
from ..utils.logger import logger


class OCRService:
    """OCR 处理服务 —— 基于 PP-StructureV3 一站式文档分析管线

    单次调用即完成版面分析、文字识别、表格识别，并输出:
      - 结构化 Markdown 文本
      - 版面分析可视化图片
      - 文档中提取出的图片
    """

    def __init__(self):
        self.pipeline = None
        self._initialized = False

    # ──────────────────────────────────────────────────────
    # 初始化
    # ──────────────────────────────────────────────────────
    def initialize(self):
        """延迟加载 PP-StructureV3 管线"""
        if self._initialized:
            return

        try:
            logger.info("Initializing PP-StructureV3 pipeline...")

            try:
                import paddlex
                import paddle

                paddle.set_device('cpu')
                paddle.set_flags({'FLAGS_use_mkldnn': False})

                os.environ.setdefault(
                    'PADDLE_PDX_CACHE_HOME',
                    r'E:\Program Files\PP_Models',
                )
                os.environ.setdefault(
                    'PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT',
                    'False',
                )

                config_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    'configs', 'PP-StructureV3.yaml',
                )

                self.pipeline = paddlex.create_pipeline(
                    pipeline=config_path,
                    lang=settings.OCR_LANG,
                    device='cpu',
                )
                self._initialized = True
                logger.info("PP-StructureV3 pipeline initialized")

            except ImportError as e:
                logger.warning(f"PaddleX not available: {e}")
                self._initialized = True  # mock mode

        except Exception as e:
            logger.error(f"Failed to initialize PP-StructureV3: {e}")
            raise

    # ──────────────────────────────────────────────────────
    # 主处理入口
    # ──────────────────────────────────────────────────────
    def process_image(self, image_path: str) -> Dict:
        """处理单张图片，返回结构化分析结果

        Returns:
            dict:
              markdown_content  - 格式化 Markdown 文本
              layout_images     - 版面分析可视化图片路径列表
              extracted_images  - 从文档中提取的图片路径列表
              parsing_results   - 结构化版面解析数据
              original_image_path
              metadata
              ocr_raw_data      - 兼容旧路由字段
        """
        start_time = time.time()

        try:
            self.initialize()

            if not os.path.isfile(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")

            logger.info(f"OCR processing: {image_path}")

            # ── Step 1: PP-StructureV3 一站式分析 ──
            logger.info("Step 1: PP-StructureV3 analysis")
            res = self._predict(image_path)

            # ── Step 2: 提取 Markdown ──
            # res.markdown 是 dict: {'markdown_texts': str, 'markdown_images': dict, ...}
            markdown_dict = self._get_field(res, 'markdown', {})
            if isinstance(markdown_dict, dict):
                markdown_content = markdown_dict.get('markdown_texts', '')
                markdown_images_map = markdown_dict.get('markdown_images', {})
            else:
                markdown_content = str(markdown_dict) if markdown_dict else ''
                markdown_images_map = {}

            if not markdown_content:
                # 从 parsing_res_list 手动拼接
                prl = self._get_field(res, 'parsing_res_list', [])
                markdown_content = self._build_markdown(prl)

            # ── Step 3: 保存版面分析图片 ──
            logger.info("Step 2: Saving layout analysis images")
            layout_images = self._save_layout_images(res, image_path)

            # ── Step 4: 保存文档中提取的图片 ──
            logger.info("Step 3: Saving extracted document images")
            extracted_images = self._save_extracted_images(res, image_path)

            # ── Step 5: 构建结构化解析数据 ──
            parsing_results = self._parse_blocks(res)

            # ── 元数据 ──
            processing_time_ms = (time.time() - start_time) * 1000
            metadata = {
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'language': settings.OCR_LANG,
                'processing_time_ms': processing_time_ms,
                'block_count': len(parsing_results),
                'image_count': len(extracted_images),
                'layout_image_count': len(layout_images),
            }

            # 给 Markdown 追加元数据
            markdown_content = self._append_metadata(
                markdown_content, metadata
            )

            # ── Step 6: 保存 Markdown 文件 ──
            markdown_file = self._save_markdown(markdown_content, image_path)

            logger.info(
                f"OCR done in {processing_time_ms:.0f}ms, "
                f"{len(parsing_results)} blocks, "
                f"{len(extracted_images)} images"
            )

            structured_data = {
                'parsing_results': parsing_results,
                'metadata': metadata,
            }

            return {
                'markdown_content': markdown_content,
                'markdown_file': markdown_file,
                'layout_images': layout_images,
                'extracted_images': extracted_images,
                'parsing_results': parsing_results,
                'original_image_path': image_path,
                'metadata': metadata,
                # 兼容旧路由字段
                'ocr_raw_data': structured_data,
                'processed_image_path': (
                    layout_images[0] if layout_images else image_path
                ),
            }

        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"OCR failed after {elapsed:.0f}ms: {e}")
            raise

    # ──────────────────────────────────────────────────────
    # PP-StructureV3 调用
    # ──────────────────────────────────────────────────────
    def _predict(self, image_path: str):
        """调用 PP-StructureV3 并返回结果对象"""
        if not self.pipeline:
            logger.warning("Pipeline unavailable — mock mode")
            return self._mock_result()

        results = list(self.pipeline.predict(
            input=image_path,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        ))

        if not results:
            raise RuntimeError("PP-StructureV3 returned no results")

        return results[0]

    # ──────────────────────────────────────────────────────
    # 版面分析图片保存
    # ──────────────────────────────────────────────────────
    def _save_layout_images(self, res, image_path: str) -> List[str]:
        """保存 PP-StructureV3 的版面分析可视化图片

        save_to_img() 会输出:
          - *_layout_det_res.png   版面检测框
          - *_layout_order_res.png  阅读顺序
          - *_overall_ocr_res.png   OCR 检测框
          - *_region_det_res.png    区域检测框
        """
        processed_dir = os.path.join(settings.PROCESSED_DIR, 'layout')
        os.makedirs(processed_dir, exist_ok=True)

        tmp_dir = os.path.join(settings.PROCESSED_DIR, '_pp_tmp_img')
        os.makedirs(tmp_dir, exist_ok=True)

        saved = []
        try:
            res.save_to_img(save_path=tmp_dir)

            for fname in os.listdir(tmp_dir):
                if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                    src = os.path.join(tmp_dir, fname)
                    dst = os.path.join(processed_dir, fname)
                    shutil.move(src, dst)
                    saved.append(dst)
        except Exception as e:
            logger.warning(f"save_to_img failed: {e}")

        # 清理临时目录
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass

        logger.info(f"Saved {len(saved)} layout images")
        return saved

    # ──────────────────────────────────────────────────────
    # 文档图片提取
    # ──────────────────────────────────────────────────────
    def _save_extracted_images(self, res, image_path: str) -> List[str]:
        """从 PP-StructureV3 结果中提取文档内嵌图片并保存

        res['imgs_in_doc'] 包含:
          [{'path': ..., 'img': PIL.Image, 'label': ..., 'coordinate': ..., 'score': ...}, ...]
        """
        extracted_dir = os.path.join(settings.PROCESSED_DIR, 'extracted')
        os.makedirs(extracted_dir, exist_ok=True)

        saved = []
        imgs_in_doc = self._get_field(res, 'imgs_in_doc', [])

        for i, item in enumerate(imgs_in_doc):
            try:
                img = item.get('img') if isinstance(item, dict) else getattr(item, 'img', None)
                label = (item.get('label', 'image') if isinstance(item, dict)
                         else getattr(item, 'label', 'image'))

                if img is not None:
                    fname = f"extracted_{i:02d}_{label}.jpg"
                    fpath = os.path.join(extracted_dir, fname)
                    img.save(fpath, quality=90)
                    saved.append(fpath)
            except Exception as e:
                logger.warning(f"Failed to save extracted image {i}: {e}")

        logger.info(f"Saved {len(saved)} extracted images")
        return saved

    # ──────────────────────────────────────────────────────
    # 保存 Markdown 文件
    # ──────────────────────────────────────────────────────
    def _save_markdown(self, markdown_content: str, image_path: str) -> str:
        """将 Markdown 内容保存为 .md 文件

        保存路径: processed/markdown/{原图文件名}.md
        """
        markdown_dir = os.path.join(settings.PROCESSED_DIR, 'markdown')
        os.makedirs(markdown_dir, exist_ok=True)

        # 从原图路径提取文件名（去掉扩展名）
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        md_path = os.path.join(markdown_dir, f"{base_name}.md")

        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            logger.info(f"Saved markdown to: {md_path}")
            return md_path
        except Exception as e:
            logger.warning(f"Failed to save markdown: {e}")
            return ''

    # ──────────────────────────────────────────────────────
    # 结构化解析
    # ──────────────────────────────────────────────────────
    def _parse_blocks(self, res) -> List[Dict]:
        """将 parsing_res_list 转为普通 dict 列表"""
        prl = self._get_field(res, 'parsing_res_list', [])
        blocks = []

        for block in prl:
            try:
                if isinstance(block, dict):
                    blocks.append(block)
                else:
                    # LayoutBlock 对象
                    blocks.append({
                        'label': getattr(block, 'label', ''),
                        'bbox': list(getattr(block, 'bbox', [])),
                        'content': getattr(block, 'content', ''),
                        'index': getattr(block, 'index', 0),
                    })
            except Exception as e:
                logger.warning(f"Failed to parse block: {e}")

        return blocks

    @staticmethod
    def _build_markdown(parsing_res_list) -> str:
        """从 parsing_res_list 手动构建 Markdown"""
        parts = ["# OCR 识别结果\n\n"]
        for block in parsing_res_list:
            if isinstance(block, dict):
                label = block.get('label', '')
                content = block.get('content', '')
            else:
                label = getattr(block, 'label', '')
                content = getattr(block, 'content', '')

            if not content:
                continue

            label_l = label.lower()
            if 'title' in label_l:
                parts.append(f"## {content}\n\n")
            elif 'table' in label_l:
                parts.append(f"{content}\n\n")
            elif label_l in ('image', 'figure', 'chart'):
                parts.append(f"![{label}](image_placeholder)\n\n")
            else:
                parts.append(f"{content}\n\n")

        return ''.join(parts)

    # ──────────────────────────────────────────────────────
    # 工具方法
    # ──────────────────────────────────────────────────────
    @staticmethod
    def _get_field(res, key: str, default=None):
        """从结果对象中安全提取字段（支持 dict 和属性访问）"""
        try:
            val = res[key]
            if val is not None:
                return val
        except (KeyError, TypeError, IndexError):
            pass
        try:
            val = getattr(res, key, None)
            if val is not None:
                return val
        except Exception:
            pass
        return default

    @staticmethod
    def _append_metadata(markdown: str, meta: Dict) -> str:
        lines = [
            "\n---\n",
            f"- **处理时间**: {meta.get('processed_at', 'N/A')}",
            f"- **语言**: {meta.get('language', 'ch')}",
            f"- **识别块数**: {meta.get('block_count', 0)}",
            f"- **提取图片**: {meta.get('image_count', 0)}",
        ]
        ms = meta.get('processing_time_ms')
        if ms:
            lines.append(f"- **处理耗时**: {ms:.0f}ms")
        return markdown + '\n'.join(lines) + '\n'

    # ──────────────────────────────────────────────────────
    # VL 增强模式入口
    # ──────────────────────────────────────────────────────
    def process_image_vl(self, image_path: str) -> Dict:
        """使用 PaddleOCR-VL-1.6 高精度模式处理图片

        委托给 VLService 完成，返回格式与 process_image() 完全兼容。
        """
        from .vl_service import vl_service

        vl_service.initialize()

        if not vl_service.is_available:
            raise RuntimeError(
                "VL 增强模式不可用。请确认: "
                "1) config 中 VL_ENABLED=True; "
                "2) llama-server 已启动; "
                "3) GGUF 模型文件存在。"
            )

        logger.info(f"Using VL enhancement mode for: {image_path}")
        return vl_service.process_image(image_path)

    @staticmethod
    def _mock_result():
        """Mock 结果（PaddleX 不可用时）"""
        return {
            'markdown': '# OCR 识别结果\n\nMock text line 1\n\nMock text line 2\n',
            'parsing_res_list': [
                {'label': 'text', 'content': 'Mock text line 1', 'bbox': [0, 0, 100, 30], 'index': 0},
                {'label': 'text', 'content': 'Mock text line 2', 'bbox': [0, 40, 100, 70], 'index': 1},
            ],
            'imgs_in_doc': [],
        }


# 全局 OCR 服务实例
ocr_service = OCRService()
