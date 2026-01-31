"""
Disk Usage Analyzer - 分析磁盘空间使用情况
"""
import os
import sys
import pickle
import hashlib
import json
import csv
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
from platform_handler import get_platform_handler_singleton, FileInfo


class DiskAnalyzer:
    """磁盘使用分析器"""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path).resolve()
        self.total_size = 0
        self.file_count = 0
        self.dir_count = 0
        self.folders = {}  # path -> size
        self.file_types = defaultdict(int)  # extension -> size
        self.large_files = []  # list of (path, size)
        self.all_files = []  # 记录所有文件 (path, size, mtime)
        self.scan_time = None  # 扫描时间
        self.cache_dir = Path('.analyzer_cache')

        # 获取平台处理器单例
        self.platform = get_platform_handler_singleton()

        # 统计信息
        self.symlink_count = 0
        self.skipped_paths: Set[Path] = set()

    def scan(self, show_progress: bool = True):
        """扫描目录"""
        if not self.root_path.exists():
            raise ValueError(f"路径不存在: {self.root_path}")

        print(f"🔍 正在扫描: {self.root_path}")
        print("=" * 60)

        for root, dirs, files in os.walk(self.root_path):
            # 计算当前目录大小
            dir_size = 0

            # 使用平台处理器过滤需要跳过的目录
            dirs[:] = [d for d in dirs if not self.platform.should_skip_path(Path(root) / d)]

            for file in files:
                file_path = Path(root) / file

                # 使用平台处理器获取文件信息
                file_info: Optional[FileInfo] = self.platform.get_file_info(file_path)

                if file_info is None:
                    continue

                # 统计符号链接（但不计入大小）
                if file_info.is_symlink:
                    self.symlink_count += 1
                    # 符号链接仍然计入大小（指向的文件大小）
                    # 如果要跳过符号链接，可以在这里 continue

                size = file_info.size
                mtime = file_info.mtime
                dir_size += size
                self.file_count += 1
                self.total_size += size

                # 记录所有文件（用于重复检测）
                self.all_files.append((file_path, size, mtime))

                # 统计文件类型
                ext = file_path.suffix.lower() or "(无扩展名)"
                self.file_types[ext] += size

                # 记录大文件 (> 100MB)
                if size > 100 * 1024 * 1024:
                    self.large_files.append((file_path, size))

            # 记录文件夹大小
            self.folders[Path(root)] = dir_size
            self.dir_count += 1

            # 显示进度
            if show_progress and self.dir_count % 100 == 0:
                print(f"已扫描 {self.dir_count} 个目录, {self.file_count} 个文件...", end='\r')

        if show_progress:
            print(f"\n✅ 扫描完成! 共扫描 {self.dir_count} 个目录, {self.file_count} 个文件")
            if self.symlink_count > 0:
                print(f"🔗 发现 {self.symlink_count} 个符号链接")
            if self.skipped_paths:
                print(f"⏭️  跳过 {len(self.skipped_paths)} 个特殊路径")

        self.scan_time = datetime.now()

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

    # ==================== 缓存功能 ====================

    def _get_cache_path(self) -> Path:
        """获取缓存文件路径"""
        # 使用路径的哈希值作为缓存文件名，避免路径中的特殊字符
        path_hash = hashlib.md5(str(self.root_path).encode('utf-8')).hexdigest()
        self.cache_dir.mkdir(exist_ok=True)
        return self.cache_dir / f"scan_{path_hash}.pkl"

    def save_cache(self):
        """保存扫描结果到缓存"""
        cache_data = {
            'root_path': str(self.root_path),
            'total_size': self.total_size,
            'file_count': self.file_count,
            'dir_count': self.dir_count,
            'folders': {str(k): v for k, v in self.folders.items()},
            'file_types': dict(self.file_types),
            'large_files': [(str(p), s) for p, s in self.large_files],
            'all_files': [(str(p), s, m) for p, s, m in self.all_files],
            'scan_time': self.scan_time,
        }

        cache_path = self._get_cache_path()
        with open(cache_path, 'wb') as f:
            pickle.dump(cache_data, f)

        return cache_path

    def load_cache(self) -> bool:
        """从缓存加载扫描结果，返回是否成功"""
        cache_path = self._get_cache_path()

        if not cache_path.exists():
            return False

        try:
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)

            # 验证缓存是否有效（检查根路径是否匹配）
            if cache_data.get('root_path') != str(self.root_path):
                return False

            # 恢复数据
            self.total_size = cache_data['total_size']
            self.file_count = cache_data['file_count']
            self.dir_count = cache_data['dir_count']
            self.folders = {Path(k): v for k, v in cache_data['folders'].items()}
            self.file_types = defaultdict(int, cache_data['file_types'])
            self.large_files = [(Path(p), s) for p, s in cache_data['large_files']]
            self.all_files = [(Path(p), s, m) for p, s, m in cache_data['all_files']]
            self.scan_time = cache_data.get('scan_time')

            return True

        except Exception:
            return False

    def is_cache_valid(self, max_age_hours: int = 24) -> bool:
        """检查缓存是否有效（存在且未过期）"""
        cache_path = self._get_cache_path()

        if not cache_path.exists():
            return False

        # 检查缓存年龄
        cache_age = datetime.now().timestamp() - cache_path.stat().st_mtime
        if cache_age > max_age_hours * 3600:
            return False

        return True

    # ==================== 重复文件检测 ====================

    @staticmethod
    def _calculate_file_hash(file_path: Path, chunk_size: int = 8192) -> Optional[str]:
        """计算文件的MD5哈希值"""
        try:
            md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    md5.update(chunk)
            return md5.hexdigest()
        except (PermissionError, FileNotFoundError):
            return None

    def find_duplicates(self, min_size: int = 1024 * 1024) -> Dict[str, List[Tuple[Path, int]]]:
        """
        查找重复文件

        Args:
            min_size: 只检测大于此大小的文件（默认1MB），加快速度

        Returns:
            {hash: [(file_path, size), ...]} - 重复文件列表
        """
        # 如果支持inode，使用inode快速去重
        if self.platform.supports_inodes():
            return self._find_duplicates_with_inodes(min_size)
        else:
            return self._find_duplicates_by_hash(min_size)

    def _find_duplicates_with_inodes(self, min_size: int) -> Dict[str, List[Tuple[Path, int]]]:
        """
        使用inode信息快速查找重复文件（Linux/macOS）

        通过inode可以快速识别硬链接，避免重复计算哈希
        """
        # 按文件大小分组
        size_groups = defaultdict(list)
        inode_map: Dict[int, List[Path]] = defaultdict(list)

        for file_path, size, _ in self.all_files:
            if size < min_size:
                continue

            size_groups[size].append((file_path, size))

            # 获取inode信息
            file_info = self.platform.get_file_info(file_path)
            if file_info and file_info.inode:
                inode_map[file_info.inode].append(file_path)

        # 找出硬链接（相同inode的文件）
        hardlink_groups = []
        for inode, paths in inode_map.items():
            if len(paths) > 1:
                # 这些是硬链接，只保留一个用于哈希计算
                hardlink_groups.append(paths[0])

        duplicates = {}
        checked_hashes = set()

        for size, files in size_groups.items():
            if len(files) < 2:
                continue

            # 计算哈希值（跳过硬链接，只计算一次）
            for file_path, size in files:
                # 如果是硬链接的代表文件，或者不在硬链接组中
                is_representative = True
                for group in hardlink_groups:
                    if file_path in group and file_path != group[0]:
                        is_representative = False
                        break

                if not is_representative:
                    continue

                file_hash = self._calculate_file_hash(file_path)
                if file_hash and file_hash not in checked_hashes:
                    if file_hash not in duplicates:
                        duplicates[file_hash] = []
                    duplicates[file_hash].append((file_path, size))
                    checked_hashes.add(file_hash)

        # 只返回有重复的文件
        return {h: files for h, files in duplicates.items() if len(files) > 1}

    def _find_duplicates_by_hash(self, min_size: int) -> Dict[str, List[Tuple[Path, int]]]:
        """
        通过哈希值查找重复文件（Windows）

        Args:
            min_size: 只检测大于此大小的文件（默认1MB），加快速度

        Returns:
            {hash: [(file_path, size), ...]} - 重复文件列表
        """
        # 按文件大小分组
        size_groups = defaultdict(list)
        for file_path, size, _ in self.all_files:
            if size >= min_size:
                size_groups[size].append((file_path, size))

        # 只处理可能有重复的文件组
        duplicates = {}
        checked_hashes = set()

        for size, files in size_groups.items():
            if len(files) < 2:
                continue  # 没有重复的可能

            # 计算哈希值
            for file_path, size in files:
                file_hash = self._calculate_file_hash(file_path)
                if file_hash and file_hash not in checked_hashes:
                    if file_hash not in duplicates:
                        duplicates[file_hash] = []
                    duplicates[file_hash].append((file_path, size))
                    checked_hashes.add(file_hash)

        # 只返回有重复的文件
        return {h: files for h, files in duplicates.items() if len(files) > 1}

    # ==================== 导出功能 ====================

    def export_to_json(self, output_path: str):
        """导出扫描结果到JSON文件"""
        data = {
            'scan_info': {
                'root_path': str(self.root_path),
                'scan_time': self.scan_time.isoformat() if self.scan_time else None,
                'total_size': self.total_size,
                'file_count': self.file_count,
                'dir_count': self.dir_count,
            },
            'top_folders': [
                {'path': str(p), 'size': s, 'size_human': self.format_size(s)}
                for p, s in self.get_top_folders(20)
            ],
            'top_files': [
                {'path': str(p), 'size': s, 'size_human': self.format_size(s)}
                for p, s in self.get_top_files(20)
            ],
            'file_types': [
                {'extension': ext, 'size': s, 'size_human': self.format_size(s)}
                for ext, s in self.get_file_types_summary().items()
            ]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return output_path

    def export_to_csv(self, output_dir: str = '.'):
        """导出扫描结果到CSV文件"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        files_created = []

        # 1. 文件夹统计
        folders_csv = output_path / f'folders_{timestamp}.csv'
        with open(folders_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['路径', '大小(字节)', '大小(可读)', '占比(%)'])

            for path, size in self.get_top_folders(100):
                percent = (size / self.total_size * 100) if self.total_size > 0 else 0
                writer.writerow([
                    str(path),
                    size,
                    self.format_size(size),
                    f'{percent:.2f}'
                ])
        files_created.append(folders_csv)

        # 2. 文件类型统计
        types_csv = output_path / f'file_types_{timestamp}.csv'
        with open(types_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['扩展名', '大小(字节)', '大小(可读)', '占比(%)'])

            for ext, size in self.get_file_types_summary().items():
                percent = (size / self.total_size * 100) if self.total_size > 0 else 0
                writer.writerow([
                    ext,
                    size,
                    self.format_size(size),
                    f'{percent:.2f}'
                ])
        files_created.append(types_csv)

        # 3. 大文件统计
        files_csv = output_path / f'large_files_{timestamp}.csv'
        with open(files_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['路径', '大小(字节)', '大小(可读)'])

            for path, size in self.get_top_files(100):
                writer.writerow([
                    str(path),
                    size,
                    self.format_size(size)
                ])
        files_created.append(files_csv)

        return files_created
