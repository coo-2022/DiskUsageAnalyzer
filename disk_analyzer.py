"""
Disk Usage Analyzer - 分析磁盘空间使用情况
"""
import os
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# 设置UTF-8编码输出（Windows兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class DiskAnalyzer:
    """磁盘使用分析器"""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.total_size = 0
        self.file_count = 0
        self.dir_count = 0
        self.folders = {}  # path -> size
        self.file_types = defaultdict(int)  # extension -> size
        self.large_files = []  # list of (path, size)

    def scan(self, show_progress: bool = True):
        """扫描目录"""
        if not self.root_path.exists():
            raise ValueError(f"路径不存在: {self.root_path}")

        print(f"🔍 正在扫描: {self.root_path}")
        print("=" * 60)

        for root, dirs, files in os.walk(self.root_path):
            # 计算当前目录大小
            dir_size = 0

            for file in files:
                file_path = Path(root) / file
                try:
                    size = file_path.stat().st_size
                    dir_size += size
                    self.file_count += 1
                    self.total_size += size

                    # 统计文件类型
                    ext = file_path.suffix.lower() or "(无扩展名)"
                    self.file_types[ext] += size

                    # 记录大文件 (> 100MB)
                    if size > 100 * 1024 * 1024:
                        self.large_files.append((file_path, size))

                except (PermissionError, FileNotFoundError) as e:
                    pass

            # 记录文件夹大小
            self.folders[Path(root)] = dir_size
            self.dir_count += 1

            # 显示进度
            if show_progress and self.dir_count % 100 == 0:
                print(f"已扫描 {self.dir_count} 个目录, {self.file_count} 个文件...", end='\r')

        if show_progress:
            print(f"\n✅ 扫描完成! 共扫描 {self.dir_count} 个目录, {self.file_count} 个文件")

    def get_top_folders(self, n: int = 10) -> List[Tuple[Path, int]]:
        """获取最大的n个文件夹"""
        sorted_folders = sorted(self.folders.items(), key=lambda x: x[1], reverse=True)
        return sorted_folders[:n]

    def get_top_files(self, n: int = 10) -> List[Tuple[Path, int]]:
        """获取最大的n个文件"""
        return sorted(self.large_files, key=lambda x: x[1], reverse=True)[:n]

    def get_file_types_summary(self) -> Dict[str, int]:
        """获取文件类型统计"""
        return dict(sorted(self.file_types.items(), key=lambda x: x[1], reverse=True))

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
