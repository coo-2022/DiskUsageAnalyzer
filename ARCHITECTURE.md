# DiskUsageAnalyzer - 跨平台架构文档

## 概述

DiskUsageAnalyzer 使用策略模式和抽象工厂模式实现了完整的跨平台支持。通过 `platform_handler.py` 抽象层，核心业务逻辑与平台特定实现完全解耦。

## 架构设计

### 设计模式

1. **策略模式 (Strategy Pattern)**
   - 不同平台使用不同的文件系统访问策略
   - 运行时动态选择合适的实现

2. **抽象工厂模式 (Abstract Factory Pattern)**
   - `get_platform_handler()` 工厂函数根据平台创建对应处理器

3. **单例模式 (Singleton Pattern)**
   - `get_platform_handler_singleton()` 确保全局共享一个平台处理器实例

### 类层次结构

```
PlatformHandler (ABC)
├── WindowsHandler
├── LinuxHandler
│   └── MacOSHandler (继承)
```

## 核心组件

### 1. PlatformHandler (抽象基类)

定义了所有平台必须实现的接口：

```python
class PlatformHandler(ABC):
    @abstractmethod
    def should_skip_path(self, path: Path) -> bool:
        """判断是否应该跳过某个路径"""

    @abstractmethod
    def get_file_info(self, path: Path) -> Optional[FileInfo]:
        """获取文件信息"""

    @abstractmethod
    def supports_inodes(self) -> bool:
        """是否支持inode信息"""

    def setup_console_encoding(self):
        """设置控制台编码（可选实现）"""
```

### 2. FileInfo (数据类)

统一的文件信息结构，封装所有平台的文件属性：

```python
@dataclass
class FileInfo:
    path: Path              # 文件路径
    size: int               # 文件大小
    mtime: float            # 修改时间
    is_symlink: bool        # 是否符号链接
    inode: Optional[int]    # inode号（Linux/macOS）
    mode: Optional[int]     # 文件权限
    target: Optional[Path]  # 符号链接目标
```

### 3. 平台实现类

#### WindowsHandler

**特性：**
- UTF-8 控制台输出
- 跳过 Windows 系统目录
- 无 inode 支持
- 使用标准 Windows API

**跳过的路径：**
- `$RECYCLE.BIN`
- `System Volume Information`
- `Config.Msi`
- `Windows`
- 隐藏文件/目录（以 `.` 开头）

#### LinuxHandler

**特性：**
- 完整的 inode 支持
- 符号链接处理（使用 `lstat`）
- 动态检测特殊文件系统
- 读取 `/proc/mounts` 识别虚拟文件系统

**跳过的路径：**
- `/proc`, `/sys`, `/dev` (预定义)
- 动态检测到的虚拟文件系统挂载点
- 特殊设备文件 (`/dev/null`, `/dev/zero` 等)

**检测的文件系统类型：**
- `proc`, `sysfs`, `devtmpfs`, `tmpfs`
- `debugfs`, `tracefs`, `cgroup`, `configfs`, `fusectl`

#### MacOSHandler

继承 `LinuxHandler`，添加 macOS 特有路径：

- `/.Spotlight-V100` (Spotlight 索引)
- `/.fseventsd` (文件系统事件)
- `/.Trashes` (回收站)
- `/Volumes` (网络卷)

## 集成方式

### DiskAnalyzer 使用平台处理器

```python
class DiskAnalyzer:
    def __init__(self, root_path: str):
        # 获取平台处理器单例
        self.platform = get_platform_handler_singleton()

    def scan(self, show_progress: bool = True):
        for root, dirs, files in os.walk(self.root_path):
            # 使用平台处理器过滤目录
            dirs[:] = [d for d in dirs
                      if not self.platform.should_skip_path(Path(root) / d)]

            for file in files:
                file_path = Path(root) / file

                # 使用平台处理器获取文件信息
                file_info = self.platform.get_file_info(file_path)

                if file_info is None:
                    continue

                # 使用统一的信息结构
                size = file_info.size
                mtime = file_info.mtime
                # ...
```

### 重复文件检测优化

Linux/macOS 使用 inode 快速识别硬链接：

```python
def find_duplicates(self, min_size: int):
    if self.platform.supports_inodes():
        return self._find_duplicates_with_inodes(min_size)
    else:
        return self._find_duplicates_by_hash(min_size)

def _find_duplicates_with_inodes(self, min_size: int):
    # 使用 inode 快速识别硬链接
    # 避免对相同 inode 的文件重复计算哈希
    inode_map: Dict[int, List[Path]] = defaultdict(list)

    for file_path, size, _ in self.all_files:
        file_info = self.platform.get_file_info(file_path)
        if file_info and file_info.inode:
            inode_map[file_info.inode].append(file_path)

    # 找出硬链接，只保留一个用于哈希计算
    # ...
```

## 扩展指南

### 添加新平台支持

1. **创建新的处理器类**

```python
class FreeBSDHandler(PlatformHandler):
    def should_skip_path(self, path: Path) -> bool:
        # FreeBSD 特定的路径过滤逻辑
        return False

    def get_file_info(self, path: Path) -> Optional[FileInfo]:
        # FreeBSD 特定的文件信息获取
        try:
            stat_result = os.lstat(path)
            return FileInfo(
                path=path,
                size=stat_result.st_size,
                mtime=stat_result.st_mtime,
                is_symlink=stat.S_ISLNK(stat_result.st_mode),
                inode=stat_result.st_ino,
                mode=stat_result.st_mode,
            )
        except (PermissionError, FileNotFoundError):
            return None

    def supports_inodes(self) -> bool:
        return True
```

2. **更新工厂函数**

```python
def get_platform_handler() -> PlatformHandler:
    if sys.platform == 'win32':
        return WindowsHandler()
    elif sys.platform == 'darwin':
        return MacOSHandler()
    elif sys.platform.startswith('linux'):
        return LinuxHandler()
    elif sys.platform.startswith('freebsd'):
        return FreeBSDHandler()  # 新增
    else:
        return LinuxHandler()  # 默认
```

### 自定义路径过滤

可以通过继承现有处理器并覆盖 `should_skip_path` 方法：

```python
class CustomLinuxHandler(LinuxHandler):
    def should_skip_path(self, path: Path) -> bool:
        # 先调用父类逻辑
        if super().should_skip_path(path):
            return True

        # 添加自定义过滤逻辑
        if 'node_modules' in path.parts:
            return True

        if '.git' in path.parts:
            return True

        return False
```

然后在 `get_platform_handler()` 中使用自定义类：

```python
def get_platform_handler() -> PlatformHandler:
    if sys.platform.startswith('linux'):
        return CustomLinuxHandler()  # 使用自定义版本
    # ...
```

## 性能考虑

### 1. 单例模式
- 平台处理器只创建一次
- 避免重复初始化（如读取 `/proc/mounts`）

### 2. 惰性求值
- 特殊文件系统检测只在需要时执行
- 不会在每次 `should_skip_path` 调用时重新检测

### 3. inode 优化
- Linux/macOS 上使用 inode 避免重复哈希计算
- 对于硬链接文件，只计算一次 MD5

### 4. 缓存友好的设计
- `detected_special_fs` 在初始化时一次性构建
- 后续查询使用集合查找，O(1) 复杂度

## 测试

项目包含 `test_platform.py` 用于验证跨平台功能：

```bash
python test_platform.py
```

测试覆盖：
- 平台检测
- 路径过滤
- 文件信息提取
- 平台特定功能

## 兼容性

| Python 版本 | Windows | Linux | macOS |
|------------|---------|-------|-------|
| 3.6+       | ✅      | ✅    | ✅    |
| 3.7+       | ✅      | ✅    | ✅    |
| 3.8+       | ✅      | ✅    | ✅    |
| 3.9+       | ✅      | ✅    | ✅    |
| 3.10+      | ✅      | ✅    | ✅    |
| 3.11+      | ✅      | ✅    | ✅    |

## 未来改进

1. **更多平台支持**
   - FreeBSD
   - OpenBSD
   - AIX

2. **性能优化**
   - 多线程扫描（使用 `concurrent.futures`）
   - 增量扫描支持

3. **功能增强**
   - 可配置的忽略列表（`.gitignore` 风格）
   - 实时监控模式（`inotify` / `ReadDirectoryChangesW`）

4. **文件类型特定优化**
   - 压缩文件内容扫描
   - 媒体文件元数据提取

## 参考资料

- [Python pathlib 文档](https://docs.python.org/3/library/pathlib.html)
- [Python os.stat 文档](https://docs.python.org/3/library/os.html#os.stat)
- [Linux inode 详解](https://www.kernel.org/doc/html/latest/filesystems/ext4/inodes.html)
- [Windows 文件系统](https://docs.microsoft.com/en-us/windows/win32/fileio/file-systems)
