import cv2
import numpy as np
from typing import List, Tuple, Dict
from pathlib import Path
from app.utils.logger import logger


class ImageService:
    """图像处理服务"""
    
    @staticmethod
    def apply_mask(
        image_path: str, 
        regions: List[Tuple[int, int, int, int]], 
        alpha: float = 0.6
    ) -> np.ndarray:
        """
        在指定区域添加半透明遮罩
        
        Args:
            image_path: 图片路径
            regions: 遮罩区域列表 [(x, y, w, h), ...]
            alpha: 透明度 (0-1), 0完全透明, 1完全不透明
            
        Returns:
            添加遮罩后的图片数组
        """
        try:
            # 读取图片
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Failed to read image: {image_path}")
            
            # 创建遮罩层
            overlay = img.copy()
            
            # 在每个区域绘制半透明矩形
            for (x, y, w, h) in regions:
                # 确保坐标在图片范围内
                x = max(0, min(x, img.shape[1]))
                y = max(0, min(y, img.shape[0]))
                w = max(0, min(w, img.shape[1] - x))
                h = max(0, min(h, img.shape[0] - y))
                
                # 绘制黑色半透明矩形
                cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 0), -1)
            
            # 混合原图和遮罩层
            result = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
            
            logger.debug(f"Applied mask to {len(regions)} regions")
            return result
            
        except Exception as e:
            logger.error(f"Failed to apply mask: {str(e)}")
            raise
    
    @staticmethod
    def extract_image_regions(layout_result: Dict) -> List[Tuple[int, int, int, int]]:
        """
        从版面分析结果中提取图片区域坐标
        
        Args:
            layout_result: ppstructureV3的版面分析结果
            
        Returns:
            图片区域坐标列表 [(x, y, w, h), ...]
        """
        regions = []
        
        try:
            # 解析ppstructure的输出
            # 假设layout_result包含'results'字段,每个元素有'bbox'和'type'
            if isinstance(layout_result, dict) and 'results' in layout_result:
                for item in layout_result['results']:
                    # 识别图片类型的区域
                    if item.get('type') in ['figure', 'image', 'picture']:
                        bbox = item.get('bbox', [])
                        if len(bbox) == 4:
                            x, y, w, h = bbox
                            regions.append((int(x), int(y), int(w), int(h)))
            
            # 如果没有找到明确的图片类型,尝试从所有区域中筛选
            elif isinstance(layout_result, list):
                for item in layout_result:
                    if isinstance(item, dict):
                        bbox = item.get('bbox') or item.get('box') or item.get('region')
                        item_type = item.get('type') or item.get('category') or ''
                        
                        # 如果是图片类型或包含'image'关键字
                        if bbox and ('image' in str(item_type).lower() or 'figure' in str(item_type).lower()):
                            if len(bbox) == 4:
                                x, y, w, h = bbox
                                regions.append((int(x), int(y), int(w), int(h)))
            
            logger.info(f"Extracted {len(regions)} image regions from layout analysis")
            return regions
            
        except Exception as e:
            logger.error(f"Failed to extract image regions: {str(e)}")
            return regions
    
    @staticmethod
    def save_image(image_array: np.ndarray, output_path: str) -> str:
        """
        保存图片数组到文件
        
        Args:
            image_array: 图片数组
            output_path: 输出路径
            
        Returns:
            保存的文件路径
        """
        try:
            # 确保目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 保存图片
            success = cv2.imwrite(output_path, image_array)
            if not success:
                raise ValueError(f"Failed to save image to: {output_path}")
            
            logger.debug(f"Image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}")
            raise
    
    @staticmethod
    def resize_image(image_path: str, max_size: Tuple[int, int] = (1920, 1080)) -> str:
        """
        调整图片大小(如果超过最大尺寸)
        
        Args:
            image_path: 图片路径
            max_size: 最大宽高 (width, height)
            
        Returns:
            调整后的图片路径
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Failed to read image: {image_path}")
            
            h, w = img.shape[:2]
            max_w, max_h = max_size
            
            # 如果图片尺寸在限制范围内,直接返回原路径
            if w <= max_w and h <= max_h:
                return image_path
            
            # 计算缩放比例
            scale = min(max_w / w, max_h / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            # 调整大小
            resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            # 保存调整后的图片
            output_path = image_path.replace('.', '_resized.')
            cv2.imwrite(output_path, resized)
            
            logger.info(f"Image resized from ({w}x{h}) to ({new_w}x{new_h})")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to resize image: {str(e)}")
            return image_path
