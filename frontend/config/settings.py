import json
import os
from pathlib import Path


class AppSettings:
    """应用配置管理类"""
    
    def __init__(self):
        self.config_file = Path.home() / ".cuoti_system" / "config.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 默认配置
        self.defaults = {
            'backend_url': 'http://localhost:8000',
            'api_version': '/api/v1',
            'upload_dir': str(Path.home() / "CuotiUploads"),
            'max_file_size_mb': 10,
            'language': 'zh_CN',
            'theme': 'light',
            'auto_start_backend': False,
            'log_level': 'INFO'
        }
        
        # 加载配置
        self.settings = self.load_settings()
    
    def load_settings(self) -> dict:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    # 合并默认配置
                    return {**self.defaults, **saved_settings}
            except Exception as e:
                print(f"Failed to load settings: {e}")
        
        return self.defaults.copy()
    
    def save_settings(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save settings: {e}")
    
    def get(self, key: str, default=None):
        """获取配置项"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        """设置配置项"""
        self.settings[key] = value
        self.save_settings()
    
    @property
    def base_url(self) -> str:
        """获取API基础URL"""
        return f"{self.settings['backend_url']}{self.settings['api_version']}"


# 全局配置实例
app_settings = AppSettings()
