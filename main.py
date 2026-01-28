"""
Disk Usage Analyzer - 命令行入口
"""
import argparse
import sys
from pathlib import Path
from disk_analyzer import DiskAnalyzer
from reporter import ReportGenerator

# 读取版本号
VERSION_FILE = Path(__file__).parent / 'VERSION'
VERSION = VERSION_FILE.read_text().strip() if VERSION_FILE.exists() else '1.1.0'


def main():
    parser = argparse.ArgumentParser(
        description='磁盘使用分析工具 - 快速找出占用空间的大文件和文件夹',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=r"""
示例:
  python main.py                      # 分析当前目录
  python main.py C:\                  # 分析C盘
  python main.py . -n 20              # 显示Top 20
  python main.py . --cache            # 使用缓存加速
  python main.py . --duplicates       # 查找重复文件
  python main.py . --export-csv       # 导出CSV报告
  python main.py . --export-json      # 导出JSON报告
        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {VERSION}'
    )

    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='要分析的路径 (默认: 当前目录)'
    )

    parser.add_argument(
        '-n', '--top',
        type=int,
        default=10,
        help='显示前N个结果 (默认: 10)'
    )

    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='不显示扫描进度'
    )

    parser.add_argument(
        '--cache',
        action='store_true',
        help='使用缓存加速扫描（如果有有效缓存）'
    )

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='不使用缓存，强制重新扫描'
    )

    parser.add_argument(
        '--duplicates',
        action='store_true',
        help='查找重复文件'
    )

    parser.add_argument(
        '--dup-min-size',
        type=int,
        default=1,
        metavar='MB',
        help='重复文件检测的最小大小(MB)，默认1MB'
    )

    parser.add_argument(
        '--export-csv',
        action='store_true',
        help='导出CSV格式报告'
    )

    parser.add_argument(
        '--export-json',
        metavar='FILE',
        help='导出JSON格式报告到指定文件'
    )

    parser.add_argument(
        '--export-dir',
        default='.',
        help='导出文件保存目录 (默认: 当前目录)'
    )

    args = parser.parse_args()

    try:
        # 创建分析器
        analyzer = DiskAnalyzer(args.path)

        # 尝试使用缓存
        use_cache = args.cache and not args.no_cache
        loaded_from_cache = False

        if use_cache and analyzer.is_cache_valid():
            print("📦 发现有效缓存，正在加载...")
            if analyzer.load_cache():
                print("✅ 缓存加载成功!")
                loaded_from_cache = True
            else:
                print("⚠️  缓存加载失败，重新扫描...")

        # 如果没有使用缓存，则进行扫描
        if not loaded_from_cache:
            analyzer.scan(show_progress=not args.no_progress)
            # 保存缓存供下次使用
            cache_path = analyzer.save_cache()
            print(f"💾 缓存已保存: {cache_path}")

        # 生成报告
        reporter = ReportGenerator(analyzer)
        reporter.generate_terminal_report(top_n=args.top)

        # 查找重复文件
        if args.duplicates:
            print("\n🔍 正在查找重复文件...")
            duplicates = analyzer.find_duplicates(min_size=args.dup_min_size * 1024 * 1024)
            reporter.show_duplicates(duplicates, top_n=args.top)

        # 导出CSV
        if args.export_csv:
            print("\n📄 正在导出CSV报告...")
            csv_files = analyzer.export_to_csv(args.export_dir)
            print(f"✅ CSV报告已导出:")
            for f in csv_files:
                print(f"   - {f}")

        # 导出JSON
        if args.export_json:
            print(f"\n📄 正在导出JSON报告...")
            json_file = analyzer.export_to_json(args.export_json)
            print(f"✅ JSON报告已导出: {json_file}")

    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
