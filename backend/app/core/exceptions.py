class AppException(Exception):
    """应用基础异常类"""
    def __init__(self, message: str = "Application error", status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class FileUploadError(AppException):
    """文件上传异常"""
    def __init__(self, message: str = "File upload failed", details: dict = None):
        super().__init__(message=message, status_code=400, details=details)


class OCRProcessingError(AppException):
    """OCR处理异常"""
    def __init__(self, message: str = "OCR processing failed", details: dict = None):
        super().__init__(message=message, status_code=500, details=details)


class ValidationError(AppException):
    """数据验证异常"""
    def __init__(self, message: str = "Validation error", details: dict = None):
        super().__init__(message=message, status_code=422, details=details)


class NotFoundError(AppException):
    """资源未找到异常"""
    def __init__(self, message: str = "Resource not found", details: dict = None):
        super().__init__(message=message, status_code=404, details=details)
