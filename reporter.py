"""
生成磁盘使用报告
"""
from disk_analyzer import DiskAnalyzer


class ReportGenerator:
    """报告生成器"""

    def __init__(self, analyzer: DiskAnalyzer):
        self.analyzer = analyzer

    def generate_terminal_report(self, top_n: int = 10):
        """生成终端报告"""
        print("\n" + "=" * 70)
        print(f"📊 磁盘使用分析报告 - {self.analyzer.root_path}")
        print("=" * 70)

        # 总览
        total_size = self.analyzer.format_size(self.analyzer.total_size)
        print(f"\n📈 总览:")
        print(f"  总大小: {total_size}")
        print(f"  文件数: {self.analyzer.file_count:,}")
        print(f"  目录数: {self.analyzer.dir_count:,}")

        # 最大的文件夹
        print(f"\n📁 最大的文件夹 (Top {top_n}):")
        print("-" * 70)
        top_folders = self.analyzer.get_top_folders(top_n)
        for i, (path, size) in enumerate(top_folders, 1):
            size_str = self.analyzer.format_size(size)
            percent = (size / self.analyzer.total_size * 100) if self.analyzer.total_size > 0 else 0
            # 显示相对路径
            rel_path = path.relative_to(self.analyzer.root_path) if path != self.analyzer.root_path else "."
            bar = self._make_bar(percent)
            print(f"  {i:2d}. {str(rel_path):50s} {size_str:>8s} {percent:5.1f}% {bar}")

        # 最大的文件
        print(f"\n📄 最大的文件 (Top {top_n}):")
        print("-" * 70)
        top_files = self.analyzer.get_top_files(top_n)
        if top_files:
            for i, (path, size) in enumerate(top_files, 1):
                size_str = self.analyzer.format_size(size)
                rel_path = path.relative_to(self.analyzer.root_path)
                print(f"  {i:2d}. {str(rel_path):60s} {size_str:>8s}")
        else:
            print("  (没有找到大于100MB的文件)")

        # 文件类型统计
        print(f"\n📊 文件类型统计 (Top 10):")
        print("-" * 70)
        file_types = self.analyzer.get_file_types_summary()
        for i, (ext, size) in enumerate(list(file_types.items())[:10], 1):
            size_str = self.analyzer.format_size(size)
            percent = (size / self.analyzer.total_size * 100) if self.analyzer.total_size > 0 else 0
            bar = self._make_bar(percent)
            print(f"  {i:2d}. {ext:15s} {size_str:>8s} {percent:5.1f}% {bar}")

        print("\n" + "=" * 70)

    def _make_bar(self, percent: float, length: int = 20) -> str:
        """创建进度条"""
        filled = int(percent / 100 * length)
        return "█" * filled + "░" * (length - filled)
