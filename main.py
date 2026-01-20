"""
Disk Usage Analyzer - 命令行入口
"""
import argparse
import sys
from disk_analyzer import DiskAnalyzer
from reporter import ReportGenerator


def main():
    parser = argparse.ArgumentParser(
        description='磁盘使用分析工具 - 快速找出占用空间的大文件和文件夹',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 分析当前目录
  python main.py C:\\                # 分析C盘
  python main.py ~/Downloads        # 分析下载文件夹
  python main.py . -n 20            # 显示Top 20
        """
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

    args = parser.parse_args()

    try:
        # 创建分析器
        analyzer = DiskAnalyzer(args.path)

        # 扫描目录
        analyzer.scan(show_progress=not args.no_progress)

        # 生成报告
        reporter = ReportGenerator(analyzer)
        reporter.generate_terminal_report(top_n=args.top)

    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
