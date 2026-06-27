from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QProgressBar, 
                             QGroupBox, QHBoxLayout, QTextEdit)
from PyQt6.QtCore import QTimer

from api.client import api_client


class SystemMonitor(QWidget):
    """系统监控面板"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # 自动刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)  # 每5秒刷新一次
    
    def setup_ui(self):
        """设置界面"""
        main_layout = QVBoxLayout(self)
        
        # 系统资源监控
        resource_group = QGroupBox("💻 系统资源")
        resource_layout = QVBoxLayout()
        
        # CPU使用率
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU使用率:"))
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setMaximum(100)
        cpu_layout.addWidget(self.cpu_bar)
        self.cpu_label = QLabel("0%")
        cpu_layout.addWidget(self.cpu_label)
        resource_layout.addLayout(cpu_layout)
        
        # 内存使用率
        mem_layout = QHBoxLayout()
        mem_layout.addWidget(QLabel("内存使用率:"))
        self.mem_bar = QProgressBar()
        self.mem_bar.setMaximum(100)
        mem_layout.addWidget(self.mem_bar)
        self.mem_label = QLabel("0%")
        mem_layout.addWidget(self.mem_label)
        resource_layout.addLayout(mem_layout)
        
        # 磁盘使用率
        disk_layout = QHBoxLayout()
        disk_layout.addWidget(QLabel("磁盘使用率:"))
        self.disk_bar = QProgressBar()
        self.disk_bar.setMaximum(100)
        disk_layout.addWidget(self.disk_bar)
        self.disk_label = QLabel("0%")
        disk_layout.addWidget(self.disk_label)
        resource_layout.addLayout(disk_layout)
        
        resource_group.setLayout(resource_layout)
        main_layout.addWidget(resource_group)
        
        # 统计信息
        stats_group = QGroupBox("📊 统计信息")
        stats_layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        stats_layout.addWidget(self.stats_text)
        
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)
    
    def refresh_data(self):
        """刷新数据"""
        try:
            # 获取系统状态
            status = api_client.get_system_status()
            
            self.cpu_bar.setValue(int(status.get('cpu_percent', 0)))
            self.cpu_label.setText(f"{status.get('cpu_percent', 0):.1f}%")
            
            self.mem_bar.setValue(int(status.get('memory_percent', 0)))
            self.mem_label.setText(f"{status.get('memory_percent', 0):.1f}%")
            
            self.disk_bar.setValue(int(status.get('disk_usage_percent', 0)))
            self.disk_label.setText(f"{status.get('disk_usage_percent', 0):.1f}%")
            
            # 获取统计数据
            stats = api_client.get_statistics()
            
            stats_text = f"总错题数: {stats.get('total_questions', 0)}\n"
            stats_text += f"今日处理: {stats.get('today_processed', 0)}\n"
            stats_text += f"平均处理时间: {stats.get('avg_processing_time_ms', 0):.2f}ms\n\n"
            
            # 状态分布
            status_dist = stats.get('status_distribution', {})
            stats_text += "状态分布:\n"
            for status_name, count in status_dist.items():
                stats_text += f"  - {status_name}: {count}\n"
            
            self.stats_text.setText(stats_text)
        
        except Exception as e:
            pass  # 静默失败,避免频繁弹窗
