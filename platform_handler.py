"""
Platform Handler - 跨平台文件系统操作抽象层

提供统一的接口处理不同操作系统的文件系统特性:
- Windows: 标准文件系统访问
- Linux: 特殊文件系统处理、符号链接、inode信息
- macOS: 类似Linux的处理
"""
import os
import sys
import stat
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List, Set
from dataclasses import dataclass


@dataclass
class FileInfo:
    """统一的文件信息结构"""
    path: Path
    size: int
    mtime: float
    is_symlink: bool = False
    inode: Optional[int] = None
    mode: Optional[int] = None
    target: Optional[Path] = None  # 符号链接目标


class PlatformHandler(ABC):
    """平台处理器抽象基类"""

    @abstractmethod
    def should_skip_path(self, path: Path) -> bool:
        """判断是否应该跳过某个路径"""
        pass

    @abstractmethod
    def get_file_info(self, path: Path) -> Optional[FileInfo]:
        """获取文件信息，如果无法访问返回None"""
        pass

    @abstractmethod
    def supports_inodes(self) -> bool:
        """是否支持inode信息"""
        pass

    def setup_console_encoding(self):
        """设置控制台编码"""
        pass


class WindowsHandler(PlatformHandler):
    """Windows平台处理器"""

    # Windows需要跳过的系统目录
    SKIP_DIRS = {
        '$RECYCLE.BIN',
        'System Volume Information',
        'Config.Msi',
        'Windows',
    }

    def __init__(self):
        self.setup_console_encoding()

    def should_skip_path(self, path: Path) -> bool:
        """检查是否应该跳过该路径"""
        # 跳过系统目录
        if path.name in self.SKIP_DIRS:
            return True

        # 跳过隐藏文件/目录（以.开头但不是当前/父目录）
        if path.name.startswith('.') and path.name not in ('.', '..'):
            return True

        return False

    def get_file_info(self, path: Path) -> Optional[FileInfo]:
        """获取Windows文件信息"""
        try:
            stat_result = path.stat()
            return FileInfo(
                path=path,
                size=stat_result.st_size,
                mtime=stat_result.st_mtime,
                is_symlink=path.is_symlink(),
                inode=None,  # Windows不支持inode
                mode=stat_result.st_mode,
            )
        except (PermissionError, FileNotFoundError, OSError):
            return None

    def supports_inodes(self) -> bool:
        """Windows不支持inode"""
        return False

    def setup_console_encoding(self):
        """设置Windows控制台为UTF-8"""
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class LinuxHandler(PlatformHandler):
    """Linux平台处理器"""

    # Linux特殊文件系统挂载点
    SPECIAL_FILESYSTEMS = {
        '/proc',
        '/sys',
        '/dev',
        '/run',
        '/tmp',
        '/var/tmp',
        '/var/run',
        '/proc/sys/fs/binfmt_misc',
    }

    # 需要跳过的特殊设备
    SPECIAL_DEVICES = {
        '/dev/null',
        '/dev/zero',
        '/dev/full',
        '/dev/random',
        '/dev/urandom',
    }

    def __init__(self):
        """初始化Linux处理器，检测特殊文件系统"""
        self.detected_special_fs: Set[str] = set()
        self._detect_special_filesystems()

    def _detect_special_filesystems(self):
        """检测系统中的特殊文件系统挂载点"""
        try:
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        mount_point = parts[1]
                        fs_type = parts[2] if len(parts) > 2 else ''

                        # 检测虚拟文件系统
                        if fs_type in ('proc', 'sysfs', 'devtmpfs', 'tmpfs', 'debugfs',
                                       'tracefs', 'cgroup', 'configfs', 'fusectl'):
                            self.detected_special_fs.add(mount_point)
        except (FileNotFoundError, PermissionError):
            # 如果无法读取/proc/mounts，使用默认列表
            self.detected_special_fs = self.SPECIAL_FILESYSTEMS.copy()

    def should_skip_path(self, path: Path) -> bool:
        """检查是否应该跳过该路径"""
        path_str = str(path)

        # 跳过特殊文件系统
        if path_str in self.SPECIAL_FILESYSTEMS:
            return True

        # 跳过检测到的特殊挂载点
        for mount_point in self.detected_special_fs:
            if path_str.startswith(mount_point + '/') or path_str == mount_point:
                return True

        # 跳过特殊设备文件
        if path_str in self.SPECIAL_DEVICES:
            return True

        # 跳过用户隐藏文件（可选，尊重用户隐私）
        # 如果用户目录下的隐藏文件，可能需要跳过
        # 这里不强制跳过，让用户决定

        return False

    def get_file_info(self, path: Path) -> Optional[FileInfo]:
        """获取Linux文件信息，包含inode和符号链接信息"""
        try:
            # 使用lstat而不是stat，以获取符号链接本身的信息
            stat_result = os.lstat(path)

            is_symlink = stat.S_ISLNK(stat_result.st_mode)
            target = None

            # 如果是符号链接，获取目标
            if is_symlink:
                try:
                    target = Path(os.readlink(path))
                except (OSError, PermissionError):
                    pass

            return FileInfo(
                path=path,
                size=stat_result.st_size,
                mtime=stat_result.st_mtime,
                is_symlink=is_symlink,
                inode=stat_result.st_ino,
                mode=stat_result.st_mode,
                target=target,
            )
        except (PermissionError, FileNotFoundError, OSError):
            return None

    def supports_inodes(self) -> bool:
        """Linux支持inode"""
        return True

    def setup_console_encoding(self):
        """Linux通常默认就是UTF-8，无需特殊处理"""
        pass


class MacOSHandler(LinuxHandler):
    """macOS平台处理器（继承Linux处理器）"""

    # macOS特有的特殊路径
    MACOS_SPECIAL_PATHS = {
        '/Volumes',  # 网络卷等
        '/.Spotlight-V100',  # Spotlight索引
        '/.fseventsd',  # 文件系统事件
        '/.Trashes',  # 回收站
    }

    def should_skip_path(self, path: Path) -> bool:
        """检查是否应该跳过该路径"""
        # 先检查macOS特殊路径
        path_str = str(path)
        if path_str in self.MACOS_SPECIAL_PATHS:
            return True

        # 再使用Linux的逻辑
        return super().should_skip_path(path)


def get_platform_handler() -> PlatformHandler:
    """工厂函数：根据当前平台返回相应的处理器"""
    if sys.platform == 'win32':
        return WindowsHandler()
    elif sys.platform == 'darwin':
        return MacOSHandler()
    elif sys.platform.startswith('linux'):
        return LinuxHandler()
    else:
        # 默认使用Linux处理器（适用于大多数Unix系统）
        return LinuxHandler()


# 单例模式，全局共享一个平台处理器
_platform_handler: Optional[PlatformHandler] = None


def get_platform_handler_singleton() -> PlatformHandler:
    """获取平台处理器单例"""
    global _platform_handler
    if _platform_handler is None:
        _platform_handler = get_platform_handler()
    return _platform_handler
