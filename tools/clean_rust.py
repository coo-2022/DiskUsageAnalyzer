"""
Rust编译产物清理工具
安全删除 target 目录和 Rust 编译产物
"""
import os
import sys
import shutil
from pathlib import Path

# 设置UTF-8编码输出（Windows兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def find_target_dirs(root_path: Path, dry_run: bool = True) -> list:
    """
    查找所有target目录

    Args:
        root_path: 根目录
        dry_run: 是否只显示不删除

    Returns:
        list of (target_dir_path, size_mb)
    """
    target_dirs = []

    print(f"🔍 正在扫描: {root_path}")
    print("=" * 60)

    for root, dirs, files in os.walk(root_path):
        if 'target' in dirs:
            target_path = Path(root) / 'target'

            # 计算大小
            total_size = 0
            try:
                for dirpath, dirnames, filenames in os.walk(target_path):
                    for filename in filenames:
                        filepath = Path(dirpath) / filename
                        try:
                            total_size += filepath.stat().st_size
                        except (PermissionError, FileNotFoundError):
                            pass
            except (PermissionError, FileNotFoundError):
                continue

            size_mb = total_size / (1024 * 1024)
            size_gb = size_mb / 1024

            # 获取相对路径
            try:
                rel_path = target_path.relative_to(root_path)
            except ValueError:
                rel_path = target_path

            target_dirs.append((target_path, total_size))

            # 显示结果
            if size_gb >= 1.0:
                size_str = f"{size_gb:.2f} GB"
            else:
                size_str = f"{size_mb:.2f} MB"

            print(f"📁 {rel_path}")
            print(f"   大小: {size_str}")

            # 显示主要的子目录
            try:
                subdirs = [d for d in target_path.iterdir() if d.is_dir()]
                debug_dir = target_path / 'debug'
                release_dir = target_path / 'release'

                if debug_dir.exists():
                    debug_size = sum(f.stat().st_size for f in debug_dir.rglob('*') if f.is_file()) / (1024**3)
                    print(f"   └─ debug/: {debug_size:.2f} GB")

                if release_dir.exists():
                    release_size = sum(f.stat().st_size for f in release_dir.rglob('*') if f.is_file()) / (1024**3)
                    print(f"   └─ release/: {release_size:.2f} GB")
            except:
                pass

            print()

    return target_dirs


def clean_target_dirs(target_dirs: list, dry_run: bool = True, skip_confirm: bool = False):
    """
    清理target目录

    Args:
        target_dirs: list of (target_dir_path, size)
        dry_run: 是否只显示不删除
        skip_confirm: 是否跳过确认提示
    """
    if not target_dirs:
        print("✅ 未找到target目录")
        return

    total_size = sum(size for _, size in target_dirs)
    total_gb = total_size / (1024**3)

    print("=" * 60)
    print(f"📊 统计:")
    print(f"   找到 {len(target_dirs)} 个target目录")
    print(f"   总大小: {total_gb:.2f} GB")
    print("=" * 60)

    if dry_run:
        print("\n🔍 这是预览模式，没有删除任何文件")
        print("   使用 --execute 参数来实际删除")
        return

    # 确认删除
    if not skip_confirm:
        print("\n⚠️  警告：即将删除所有target目录！")
        try:
            response = input("确认删除？(输入 'yes' 确认): ")
            if response.lower() != 'yes':
                print("❌ 取消删除")
                return
        except EOFError:
            print("\n❌ 无法获取确认，请使用 --yes 参数跳过确认")
            return

    # 执行删除
    print("\n🗑️  开始删除...")
    deleted_size = 0
    deleted_count = 0

    for target_path, size in target_dirs:
        try:
            shutil.rmtree(target_path)
            deleted_size += size
            deleted_count += 1

            size_gb = size / (1024**3)
            if size_gb >= 1.0:
                size_str = f"{size_gb:.2f} GB"
            else:
                size_mb = size / (1024**2)
                size_str = f"{size_mb:.2f} MB"

            print(f"   ✅ 已删除: {target_path.name}/ ({size_str})")
        except Exception as e:
            print(f"   ❌ 删除失败: {target_path}")
            print(f"      错误: {e}")

    print("\n" + "=" * 60)
    print(f"✅ 清理完成!")
    print(f"   删除了 {deleted_count} 个目录")
    print(f"   释放空间: {deleted_size / (1024**3):.2f} GB")
    print("=" * 60)


def clean_cargo_cache(dry_run: bool = True):
    """
    清理Cargo缓存

    Args:
        dry_run: 是否只显示不删除
    """
    cargo_cache_path = Path.home() / ".cargo" / "registry"

    if not cargo_cache_path.exists():
        print("✅ Cargo缓存目录不存在")
        return

    print("\n" + "=" * 60)
    print("📦 Cargo缓存")
    print("=" * 60)

    # 计算缓存大小
    total_size = 0
    try:
        for item in cargo_cache_path.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
    except:
        pass

    size_gb = total_size / (1024**3)
    size_mb = total_size / (1024**2)

    if size_gb >= 1.0:
        size_str = f"{size_gb:.2f} GB"
    else:
        size_str = f"{size_mb:.2f} MB"

    print(f"路径: {cargo_cache_path}")
    print(f"大小: {size_str}")

    if dry_run:
        print("\n提示: 运行 'cargo clean' 来清理项目缓存")
        print("      运行 'cargo cache-dir --info' 查看缓存信息")
        return

    response = input("\n是否清理Cargo缓存？(y/n): ")
    if response.lower() == 'y':
        os.system("cargo clean")
        print("✅ Cargo缓存清理完成")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Rust编译产物清理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python clean_rust.py                    # 预览模式，显示可删除的文件
  python clean_rust.py --execute          # 实际删除target目录
  python clean_rust.py ~/code --execute   # 清理指定目录
  python clean_rust.py --cargo-cache      # 清理Cargo缓存
        """
    )

    parser.add_argument(
        'path',
        nargs='?',
        default='~/code',
        help='要清理的路径 (默认: ~/code)'
    )

    parser.add_argument(
        '--execute', '-e',
        action='store_true',
        help='实际删除（默认只预览）'
    )

    parser.add_argument(
        '--cargo-cache',
        action='store_true',
        help='清理Cargo全局缓存'
    )

    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='跳过确认提示'
    )

    args = parser.parse_args()

    # 展开路径
    root_path = Path(args.path).expanduser().resolve()

    if not root_path.exists():
        print(f"❌ 错误: 路径不存在 - {root_path}")
        sys.exit(1)

    try:
        # 查找target目录
        target_dirs = find_target_dirs(root_path, dry_run=not args.execute)

        # 清理target目录
        clean_target_dirs(target_dirs, dry_run=not args.execute, skip_confirm=args.yes)

        # 清理Cargo缓存
        if args.cargo_cache:
            clean_cargo_cache(dry_run=not args.execute)

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
