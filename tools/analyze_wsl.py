"""
WSL磁盘分析工具
分析WSL内部磁盘占用情况
"""
import subprocess
import sys
import json
from pathlib import Path

# 设置UTF-8编码输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def run_wsl_command(distro, command):
    """执行WSL命令"""
    full_command = f'wsl -d {distro} -- {command}'
    result = subprocess.run(
        full_command,
        shell=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore',
        timeout=60
    )
    return result.stdout + result.stderr


def run_docker_command(command):
    """执行Docker命令（从Windows）"""
    full_command = f'docker {command}'
    result = subprocess.run(
        full_command,
        shell=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore',
        timeout=60
    )
    return result.stdout + result.stderr


def analyze_ubuntu():
    """分析Ubuntu磁盘占用"""
    print("📊 Ubuntu 22.04 磁盘分析")
    print("=" * 60)

    # 1. 获取总体磁盘使用
    print("\n📈 总体磁盘使用:")
    print("-" * 60)
    output = run_wsl_command('Ubuntu-22.04', 'df -h /')
    for line in output.split('\n'):
        if line and not line.startswith('Filesystem'):
            print(f"   {line}")

    # 2. 获取根目录下各目录占用
    print("\n📁 根目录各文件夹占用 (Top 20):")
    print("-" * 60)
    try:
        output = run_wsl_command(
            'Ubuntu-22.04',
            'du -sh /* 2>/dev/null | sort -hr | head -20'
        )

        lines = [line for line in output.split('\n') if line.strip() and not line.startswith('Microsoft') and not line.startswith('(c)')]
        for line in lines:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                size, path = parts[0], parts[1]
                print(f"   {size:<10} {path}")
            elif len(parts) == 1 and line.strip():
                # 可能没有制表符分隔
                parts = line.strip().split(maxsplit=1)
                if len(parts) >= 2:
                    size, path = parts[0], parts[1]
                    print(f"   {size:<10} {path}")
    except Exception as e:
        print(f"   ⚠️  无法获取详细信息: {e}")

    # 3. 分析home目录
    print("\n🏠 Home目录分析 (Top 15):")
    print("-" * 60)
    output = run_wsl_command(
        'Ubuntu-22.04',
        'du -sh ~/* 2>/dev/null | sort -hr | head -15'
    )

    for line in output.split('\n'):
        if line.strip():
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                size, path = parts[0], parts[1]
                print(f"   {size:<10} {path}")

    # 4. 查找大文件
    print("\n📄 最大的文件 (Top 10):")
    print("-" * 60)
    output = run_wsl_command(
        'Ubuntu-22.04',
        'find / -type f -size +100M 2>/dev/null | xargs du -sh 2>/dev/null | sort -hr | head -10'
    )

    for line in output.split('\n'):
        if line.strip():
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                size, path = parts[0], parts[1]
                print(f"   {size:<10} {path}")

    # 5. APT缓存
    print("\n📦 APT缓存:")
    print("-" * 60)
    output = run_wsl_command(
        'Ubuntu-22.04',
        'du -sh /var/cache/apt 2>/dev/null'
    )
    print(f"   {output.strip()}")

    # 6. 日志文件
    print("\n📝 日志文件:")
    print("-" * 60)
    output = run_wsl_command(
        'Ubuntu-22.04',
        'du -sh /var/log 2>/dev/null'
    )
    print(f"   {output.strip()}")


def analyze_docker():
    """分析Docker占用"""
    print("\n\n🐳 Docker 磁盘分析")
    print("=" * 60)

    # 1. Docker系统总体信息
    print("\n📈 Docker系统总体信息:")
    print("-" * 60)
    output = run_docker_command('system df')

    for line in output.split('\n'):
        if line.strip():
            print(f"   {line}")

    # 2. 镜像详情
    print("\n🖼️  Docker镜像 (Top 10):")
    print("-" * 60)
    output = run_docker_command('images --format "table {{.Size}}\t{{.Repository}}:{{.Tag}}"')

    for line in output.split('\n'):
        if line.strip():
            print(f"   {line}")

    # 3. 容器详情
    print("\n📦 Docker容器 (所有):")
    print("-" * 60)
    output = run_docker_command('ps -as --format "table {{.Size}}\t{{.Names}}\t{{.Status}}"')

    for line in output.split('\n'):
        if line.strip():
            print(f"   {line}")

    # 4. 卷详情
    print("\n💾 Docker卷 (所有):")
    print("-" * 60)
    output = run_docker_command('volume ls')

    for line in output.split('\n'):
        if line.strip():
            print(f"   {line}")

    # 5. 悬空镜像（可清理）
    print("\n🗑️  悬空资源详情:")
    print("-" * 60)
    output = run_docker_command('system df -v')

    for line in output.split('\n'):
        if line.strip():
            print(f"   {line}")


def show_cleanup_commands():
    """显示清理命令"""
    print("\n\n🧹 清理命令参考")
    print("=" * 60)

    print("\n📦 Ubuntu清理:")
    print("   # 清理APT缓存")
    print("   wsl -d Ubuntu-22.04 -- sudo apt-get clean")
    print("   wsl -d Ubuntu-22.04 -- sudo apt-get autoremove")
    print()
    print("   # 清理旧的日志")
    print("   wsl -d Ubuntu-22.04 -- sudo journalctl --vacuum-size=100M")

    print("\n🐳 Docker清理:")
    print("   # 清理悬空镜像、容器、卷")
    print("   wsl -d docker-desktop -- docker system prune -a --volumes")
    print()
    print("   # 只清理悬空资源")
    print("   wsl -d docker-desktop -- docker system prune")
    print()
    print("   # 清理未使用的镜像")
    print("   wsl -d docker-desktop -- docker image prune -a")

    print("\n⚠️  WSL虚拟磁盘瘦身:")
    print("   # 1. 在WSL内优化磁盘")
    print("   wsl -d Ubuntu-22.04 -- sudo dd if=/dev/zero of=/empty bs=1M")
    print("   wsl -d Ubuntu-22.04 -- sudo rm -f /empty")
    print()
    print("   # 2. 在Windows端压缩虚拟磁盘")
    print("   powershell.exe Optimize-VHD -Path \\\"%USERPROFILE%\\AppData\\Local\\Packages\\CanonicalGroupLimited.Ubuntu22.04LTS_79rhkp1fndgsc\\LocalState\\ext4.vhdx\\\" -Mode Full")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='WSL磁盘分析工具')
    parser.add_argument('--ubuntu', action='store_true', help='只分析Ubuntu')
    parser.add_argument('--docker', action='store_true', help='只分析Docker')
    parser.add_argument('--cleanup', action='store_true', help='显示清理命令')

    args = parser.parse_args()

    try:
        if args.docker:
            analyze_docker()
        elif args.ubuntu:
            analyze_ubuntu()
        else:
            analyze_ubuntu()
            analyze_docker()

        if args.cleanup or not (args.ubuntu or args.docker):
            show_cleanup_commands()

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
