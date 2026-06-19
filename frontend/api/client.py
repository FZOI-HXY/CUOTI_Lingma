import os
import requests
from typing import Optional, Dict, Any
from config.settings import app_settings


class APIClient:
    """API客户端封装"""
    
    def __init__(self):
        self.base_url = app_settings.base_url
        self.session = requests.Session()
        # 不设置全局Content-Type，让requests根据请求类型自动设置
    
    def upload_image(self, file_path: str) -> Dict[str, Any]:
        """上传图片文件"""
        url = f"{self.base_url}/upload/image"
        
        try:
            with open(file_path, 'rb') as f:
                # 文件上传时，requests会自动设置正确的Content-Type (multipart/form-data)
                files = {'file': (os.path.basename(file_path), f, 'image/jpeg')}
                response = self.session.post(url, files=files)
                response.raise_for_status()
                return response.json()
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Upload failed: {str(e)}")
    
    def process_ocr(self, file_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """启动OCR处理"""
        url = f"{self.base_url}/ocr/process"
        
        data = {
            'file_id': file_id,
            'user_id': user_id
        }
        
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"OCR processing failed: {str(e)}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询任务状态"""
        url = f"{self.base_url}/ocr/status/{task_id}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get task status: {str(e)}")
    
    def list_questions(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        """获取错题列表"""
        url = f"{self.base_url}/questions/"
        
        params = {
            'page': page,
            'page_size': page_size,
            **filters
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to list questions: {str(e)}")
    
    def get_question(self, question_id: int) -> Dict[str, Any]:
        """获取错题详情"""
        url = f"{self.base_url}/questions/{question_id}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get question: {str(e)}")
    
    def delete_question(self, question_id: int) -> Dict[str, Any]:
        """删除错题"""
        url = f"{self.base_url}/questions/{question_id}"
        
        try:
            response = self.session.delete(url)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to delete question: {str(e)}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        url = f"{self.base_url}/system/status"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get system status: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计数据"""
        url = f"{self.base_url}/system/stats"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get statistics: {str(e)}")
    
    # ─────────────────────────────────────────
    # 报告下载
    # ─────────────────────────────────────────

    def download_markdown(self, question_id: int, save_path: str) -> str:
        """下载单题 Markdown 报告，返回保存路径"""
        url = f"{self.base_url}/reports/{question_id}/markdown"
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return save_path
        except requests.exceptions.RequestException as e:
            raise Exception(f"Markdown 下载失败: {str(e)}")

    def download_pdf(self, question_id: int, save_path: str) -> str:
        """下载单题 PDF 报告，返回保存路径"""
        url = f"{self.base_url}/reports/{question_id}/pdf"
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return save_path
        except requests.exceptions.RequestException as e:
            raise Exception(f"PDF 下载失败: {str(e)}")

    def download_batch_zip(
        self,
        question_ids: list,
        formats: list = None,
        save_path: str = None
    ) -> str:
        """批量导出报告 ZIP 包，返回保存路径"""
        url = f"{self.base_url}/reports/batch"
        if formats is None:
            formats = ['markdown', 'pdf']
        try:
            payload = {
                'question_ids': question_ids,
                'formats': formats,
            }
            response = self.session.post(
                url,
                json=payload,
                stream=True,
                timeout=300
            )
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return save_path
        except requests.exceptions.RequestException as e:
            raise Exception(f"批量导出失败: {str(e)}")

    def health_check(self) -> bool:
        """健康检查"""
        url = f"{app_settings.get('backend_url', 'http://localhost:8100')}/health"
        
        try:
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        
        except:
            return False


# 全局API客户端实例
api_client = APIClient()
