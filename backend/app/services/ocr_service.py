import time
import os
from typing import Dict, Optional
from datetime import datetime, timezone

# 禁用 MKL-DNN 以避免兼容性问题（必须在导入 paddle 之前设置）
os.environ['FLAGS_use_mkldnn'] = '0'

from ..config import settings
from ..utils.logger import logger
from .image_service import ImageService
from .markdown_service import MarkdownService


class OCRService:
    """OCR处理服务 - 集成PaddleOCR ppstructureV3和ppOCRv5"""
    
    def __init__(self):
        self.ppstructure = None
        self.ppocr = None
        self.image_service = ImageService()
        self.markdown_service = MarkdownService()
        self._initialized = False
    
    def initialize(self):
        """初始化OCR模型(延迟加载)"""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing PaddleOCR models...")
            
            # 尝试导入PaddleX和PaddleOCR
            try:
                from paddleocr import PaddleOCR
                
                # 初始化ppOCR用于文字识别 (新版本API)
                # 确保使用 CPU 并禁用 oneDNN
                import paddle
                paddle.set_device('cpu')
                
                self.ppocr = PaddleOCR(
                    lang=settings.OCR_LANG,
                    ocr_version='PP-OCRv5'  # 显式指定 OCR 版本
                )
                logger.info("PaddleOCR initialized successfully")
                
                # 尝试初始化版面分析 (可选)
                try:
                    import paddlex
                    # PaddleX 3.x 使用 create_pipeline
                    self.ppstructure = paddlex.create_pipeline(
                        pipeline='ppstructure_v3',
                        lang=settings.OCR_LANG
                    )
                    logger.info("PP-StructureV3 initialized successfully")
                except Exception as e:
                    logger.warning(f"PP-StructureV3 not available: {str(e)}")
                    self.ppstructure = None
                
                self._initialized = True
                logger.info("All OCR models initialized successfully")
                
            except ImportError as e:
                logger.warning(f"PaddleOCR not available: {str(e)}")
                logger.warning("OCR service will run in mock mode")
                self._initialized = True  # 标记为已初始化,但使用mock模式
        
        except Exception as e:
            logger.error(f"Failed to initialize OCR models: {str(e)}")
            raise
    
    def process_image(self, image_path: str) -> Dict:
        """
        处理图片的完整流程
        
        Args:
            image_path: 图片路径
            
        Returns:
            处理结果字典
        """
        start_time = time.time()
        
        try:
            # 确保模型已初始化
            self.initialize()
            
            logger.info(f"Starting OCR processing for: {image_path}")
            
            # Step 1: 使用ppstructureV3进行版面分析
            logger.info("Step 1: Layout analysis with PP-StructureV3")
            layout_result = self._perform_layout_analysis(image_path)
            
            # Step 2: 提取图片区域
            logger.info("Step 2: Extracting image regions")
            image_regions = self.image_service.extract_image_regions(layout_result)
            
            # Step 3: 在原图上添加遮罩
            logger.info(f"Step 3: Applying mask to {len(image_regions)} regions")
            masked_image_array = self.image_service.apply_mask(image_path, image_regions)
            
            # 保存遮罩后的图片
            processed_dir = settings.PROCESSED_DIR
            os.makedirs(processed_dir, exist_ok=True)
            base_name = os.path.basename(image_path)
            masked_image_path = os.path.join(processed_dir, f"masked_{base_name}")
            self.image_service.save_image(masked_image_array, masked_image_path)
            
            # Step 4: 调用ppOCR进行文字识别
            logger.info("Step 4: OCR recognition with PaddleOCR")
            ocr_result = self._perform_ocr_recognition(masked_image_path)
            
            # Step 5: 生成结构化Markdown
            logger.info("Step 5: Generating structured Markdown")
            markdown_content = self.markdown_service.generate(ocr_result, layout_result)
            
            # 计算处理时间
            processing_time_ms = (time.time() - start_time) * 1000
            
            # 构建元数据(用于JSON存储)
            metadata = {
                'processed_at': datetime.now(timezone.utc).isoformat(),  # JSON需要字符串格式
                'language': settings.OCR_LANG,
                'image_count': len(image_regions),
                'processing_time_ms': processing_time_ms,
                'layout_elements': len(layout_result.get('results', [])) if isinstance(layout_result, dict) else 0,
                'confidence_avg': self._calculate_avg_confidence(ocr_result)
            }
            
            # 添加元数据到Markdown
            markdown_content = self.markdown_service.add_metadata_section(markdown_content, metadata)
            
            logger.info(f"OCR processing completed in {processing_time_ms:.2f}ms")
            
            return {
                'markdown_content': markdown_content,
                'processed_image_path': masked_image_path,
                'original_image_path': image_path,
                'metadata': metadata,
                'ocr_raw_data': ocr_result,
                'layout_result': layout_result
            }
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(f"OCR processing failed after {processing_time_ms:.2f}ms: {str(e)}")
            raise
    
    def _perform_layout_analysis(self, image_path: str) -> Dict:
        """执行版面分析"""
        try:
            if self.ppstructure:
                result = self.ppstructure(input=image_path)
                return result
            else:
                # 不使用 mock，直接返回空结果
                logger.info("Layout analysis not available, skipping")
                return {'results': []}
        except Exception as e:
            logger.error(f"Layout analysis failed: {str(e)}")
            return {'results': []}
    
    def _perform_ocr_recognition(self, image_path: str) -> Dict:
        """执行OCR文字识别"""
        try:
            if self.ppocr:
                # 新版本 PaddleOCR 不支持 cls 参数
                result = self.ppocr.ocr(image_path)
                
                # 转换结果为统一格式
                if result and result[0]:
                    texts = [line[1][0] for line in result[0]]
                    scores = [line[1][1] for line in result[0]]
                    return {
                        'rec_texts': texts,
                        'rec_scores': scores,
                        'raw_result': result
                    }
                return {'rec_texts': [], 'rec_scores': []}
            else:
                # Mock模式
                logger.warning("Using mock OCR recognition")
                return {
                    'rec_texts': ['Mock OCR text line 1', 'Mock OCR text line 2'],
                    'rec_scores': [0.95, 0.92]
                }
        except Exception as e:
            logger.error(f"OCR recognition failed: {str(e)}")
            return {'rec_texts': [], 'rec_scores': []}
    
    def _calculate_avg_confidence(self, ocr_result: Dict) -> float:
        """计算平均置信度"""
        try:
            scores = ocr_result.get('rec_scores', [])
            if scores:
                return sum(scores) / len(scores)
            return 0.0
        except:
            return 0.0


# 全局OCR服务实例
ocr_service = OCRService()
