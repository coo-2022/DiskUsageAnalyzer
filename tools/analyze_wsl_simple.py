"""
WSL磁盘分析工具 - 简化版
使用df命令分析WSL磁盘占用
"""
import subprocess
import sys

# 设置UTF-8编码输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def run_wsl(distro, command, timeout=30):
    """执行WSL命令"""
    try:
        result = subprocess.run(
            f'wsl -d {distro} -- {command}',
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=timeout
        )
        # 过滤掉Windows的输出
        output = result.stdout
        lines = []
        for line in output.split('\n'):
            if not line.startswith('Microsoft') and not line.startswith('(c)') and line.strip():
                lines.append(line)
        return '\n'.join(lines)
    except subprocess.TimeoutExpired:
        return f"命令超时 ({timeout}秒)"
    except Exception as e:
        return f"错误: {e}"


def main():
    print("📊 WSL磁盘快速分析")
    print("=" * 60)

    # 1. Ubuntu磁盘使用情况
    print("\n🐧 Ubuntu 22.04:")
    print("-" * 60)

    # 总体使用
    output = run_wsl('Ubuntu-22.04', 'df -h /')
    print(output)

    # 主要目录
    print("\n主要目录占用:")
    print("-" * 60)
    for dir_path in ['/home', '/usr', '/var', '/opt', '/root', '/tmp']:
        output = run_wsl('Ubuntu-22.04', f'du -sh {dir_path} 2>/dev/null | head -1', timeout=10)
        if output and not output.startswith('错误') and not output.startswith('命令超时'):
            print(f"   {output.strip()}")

    # Docker目录
    print("\nDocker相关目录:")
    print("-" * 60)
    output = run_wsl('Ubuntu-22.04', 'ls -lh /var/lib/docker 2>/dev/null | head -20', timeout=10)
    if output:
        print(output)

    # Snap包
    print("\nSnap包:")
    print("-" * 60)
    output = run_wsl('Ubuntu-22.04', 'du -sh /snap/* 2>/dev/null | sort -hr | head -10', timeout=10)
    if output and not output.startswith('错误'):
        lines = output.split('\n')[:10]
        for line in lines:
            if line.strip():
                print(f"   {line.strip()}")

    # 日志
    print("\n日志文件:")
    print("-" * 60)
    output = run_wsl('Ubuntu-22.04', 'du -sh /var/log/* 2>/dev/null | sort -hr | head -10', timeout=10)
    if output and not output.startswith('错误'):
        lines = output.split('\n')[:10]
        for line in lines:
            if line.strip():
                print(f"   {line.strip()}")

    print("\n" + "=" * 60)
    print("✅ 分析完成")
    print("\n💡 清理建议:")
    print("   1. 清理APT缓存: sudo apt-get clean && sudo apt-get autoremove")
    print("   2. 清理日志: sudo journalctl --vacuum-size=100M")
    print("   3. 查看旧的内核: sudo dpkg --list 'linux-image*'")
    print("   4. 检查Docker: docker system prune")
    print("\n🔧 虚拟磁盘压缩:")
    print("   1. 在WSL内清理空间后，运行:")
    print("      sudo dd if=/dev/zero of=/empty bs=1M; sudo rm -f /empty")
    print("   2. 在Windows PowerShell运行:")
    print("      Optimize-VHD -Path \"$env:USERPROFILE\\AppData\\Local\\Packages\\CanonicalGroupLimited.Ubuntu22.04LTS_79rhkp1fndgsc\\LocalState\\ext4.vhdx\" -Mode Full")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
