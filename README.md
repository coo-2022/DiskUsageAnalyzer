# Disk Usage Analyzer

一个简单快速的磁盘空间分析工具，帮助你找出占用空间的大文件和文件夹。

## 功能

- 📊 **快速扫描** - 高效遍历目录树，统计所有文件和文件夹大小
- 🔍 **智能排序** - 自动找出占用空间最大的文件夹和文件
- 📈 **分类统计** - 按文件类型分析空间占用情况
- 🎨 **可视化报告** - 清晰的终端表格输出，带进度条
- 🚀 **缓存机制** - 加速二次扫描，保存扫描结果
- 🔁 **重复文件检测** - 查找重复文件，节省磁盘空间
- 📊 **CSV/JSON导出** - 导出详细报告用于深入分析
- ⚡ **跨平台** - Windows / macOS / Linux 通用

## 安装

无需额外依赖，只需要 Python 3.6+：

```bash
git clone <repository-url>
cd disk_usage_analyzer
```

## 使用方法

### 基本用法

```bash
# 分析当前目录
python main.py

# 分析指定目录
python main.py C:\

# 分析用户目录
python main.py ~

# 显示前20个结果
python main.py -n 20
```

### 高级功能

#### 1. 使用缓存加速

```bash
# 第一次扫描会保存缓存
python main.py C:\

# 第二次使用缓存，几乎瞬间完成
python main.py C:\ --cache

# 强制重新扫描
python main.py C:\ --no-cache
```

#### 2. 查找重复文件

```bash
# 查找重复文件（默认大于1MB）
python main.py ~/Downloads --duplicates

# 只检测大于10MB的文件
python main.py ~/Downloads --duplicates --dup-min-size 10
```

#### 3. 导出报告

```bash
# 导出CSV格式（方便Excel打开）
python main.py C:\ --export-csv

# 导出JSON格式
python main.py C:\ --export-json report.json

# 指定导出目录
python main.py C:\ --export-csv --export-dir ./reports
```

#### 4. 组合使用

```bash
# 分析整个D盘，使用缓存，查找重复文件，导出报告
python main.py D:\ --cache --duplicates --export-csv --export-json d_drive_report.json

# 快速查看Top 20大文件
python main.py . -n 20 --no-progress
```

## 输出示例

### 基本报告

```
📊 磁盘使用分析报告 - C:\Users\username
======================================================================

📈 总览:
  总大小: 256.5 GB
  文件数: 125,430
  目录数: 18,234

📁 最大的文件夹 (Top 10):
----------------------------------------------------------------------
   1. node_modules/                                    120.5 GB  47.0% ████████████████████
   2. Downloads/                                        45.2 GB  17.6% ███████
   3. AppData/Local/                                    32.1 GB  12.5% ██████
   ...

📄 最大的文件 (Top 10):
----------------------------------------------------------------------
   1. backup.zip                                                 8.5 GB
   2. video.mp4                                                  3.2 GB
   ...

📊 文件类型统计 (Top 10):
----------------------------------------------------------------------
   1. .mp4                                           45.2 GB  17.6% ███████
   2. .zip                                           12.3 GB   4.8% ██
   ...
```

### 重复文件报告

```
🔁 重复文件检测 (Top 10)
======================================================================

📌 重复组 #1 (3 个文件, 各 1.2 GB)
   ⚠️  可节省: 2.4 GB
      1. Downloads/backup.zip
      2. Documents/backup copy.zip
      3. .temp/backup.zip

📌 重复组 #2 (2 个文件, 各 450 MB)
   ⚠️  可节省: 450 MB
      1. Videos/movie.mp4
      2. Backup/movie.mp4

----------------------------------------------------------------------
💰 总计可节省空间: 2.9 GB
======================================================================
```

## 项目结构

```
disk_usage_analyzer/
├── disk_analyzer.py   # 核心分析器（扫描、缓存、重复检测、导出）
├── reporter.py        # 报告生成器（终端输出）
├── main.py           # CLI 入口
├── .analyzer_cache/  # 缓存目录（自动生成）
└── README.md         # 说明文档
```

## 技术实现

- **缓存机制**: 使用 `pickle` 序列化扫描结果，基于路径哈希存储
- **重复检测**: 先按文件大小预筛选，再计算 MD5 哈希确认
- **导出功能**: CSV 使用 `csv` 模块（UTF-8-BOM编码），JSON 使用 `json` 模块

## 开发路线

- [x] 基础扫描和统计功能
- [x] 终端可视化报告
- [x] CSV/JSON 导出
- [x] 重复文件检测
- [x] 缓存机制加速二次扫描
- [ ] HTML 可视化报告
- [ ] 忽略列表配置
- [ ] 定时扫描和报告

## License

MIT
