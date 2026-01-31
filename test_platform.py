#!/usr/bin/env python3
"""
Cross-platform functionality test script

Tests the platform handler abstraction layer and demonstrates
platform-specific features.
"""
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from platform_handler import (
    get_platform_handler_singleton,
    WindowsHandler,
    LinuxHandler,
    MacOSHandler
)


def test_platform_detection():
    """Test platform detection"""
    print("=" * 70)
    print("Testing Platform Detection")
    print("=" * 70)

    handler = get_platform_handler_singleton()
    print(f"✅ Current Platform: {sys.platform}")
    print(f"✅ Handler Type: {handler.__class__.__name__}")
    print(f"✅ Supports Inodes: {handler.supports_inodes()}")
    print()


def test_path_filtering():
    """Test path filtering for special filesystems"""
    print("=" * 70)
    print("Testing Special Path Filtering")
    print("=" * 70)

    handler = get_platform_handler_singleton()

    # Test paths to check
    test_paths = [
        Path("/proc"),
        Path("/sys"),
        Path("/dev"),
        Path("/tmp"),
        Path("/home/user/documents"),
        Path("/var/log"),
    ]

    print(f"Handler: {handler.__class__.__name__}")
    print()
    for path in test_paths:
        should_skip = handler.should_skip_path(path)
        status = "⏭️  SKIP" if should_skip else "✅ SCAN"
        print(f"{status:10s} {path}")

    print()


def test_file_info():
    """Test file info extraction"""
    print("=" * 70)
    print("Testing File Info Extraction")
    print("=" * 70)

    handler = get_platform_handler_singleton()

    # Test with current directory
    test_file = Path(__file__)

    file_info = handler.get_file_info(test_file)

    if file_info:
        print(f"✅ File: {file_info.path}")
        print(f"✅ Size: {file_info.size} bytes")
        print(f"✅ Modified: {file_info.mtime}")
        print(f"✅ Is Symlink: {file_info.is_symlink}")
        print(f"✅ Inode: {file_info.inode}")
        print(f"✅ Mode: {file_info.mode}")

        if file_info.is_symlink and file_info.target:
            print(f"✅ Symlink Target: {file_info.target}")
    else:
        print("❌ Failed to get file info")

    print()


def test_windows_specific():
    """Test Windows-specific features (only on Windows)"""
    if sys.platform != 'win32':
        return

    print("=" * 70)
    print("Testing Windows-Specific Features")
    print("=" * 70)

    handler = WindowsHandler()

    windows_paths = [
        Path("C:/System Volume Information"),
        Path("C:/$RECYCLE.BIN"),
        Path("C:/Windows"),
        Path("C:/Users"),
        Path("C:/Program Files"),
    ]

    for path in windows_paths:
        should_skip = handler.should_skip_path(path)
        status = "⏭️  SKIP" if should_skip else "✅ SCAN"
        print(f"{status:10s} {path}")

    print()


def test_linux_specific():
    """Test Linux-specific features (only on Linux)"""
    if not sys.platform.startswith('linux'):
        return

    print("=" * 70)
    print("Testing Linux-Specific Features")
    print("=" * 70)

    handler = LinuxHandler()

    print(f"✅ Detected special filesystems: {len(handler.detected_special_fs)}")
    for fs in sorted(handler.detected_special_fs):
        print(f"   - {fs}")

    print()

    # Test special device files
    special_devices = [
        Path("/dev/null"),
        Path("/dev/zero"),
        Path("/dev/random"),
        Path("/home/user/file.txt"),
    ]

    print("Special device filtering:")
    for path in special_devices:
        should_skip = handler.should_skip_path(path)
        status = "⏭️  SKIP" if should_skip else "✅ SCAN"
        print(f"{status:10s} {path}")

    print()


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 Cross-Platform Functionality Tests")
    print("=" * 70)
    print()

    try:
        test_platform_detection()
        test_path_filtering()
        test_file_info()
        test_windows_specific()
        test_linux_specific()

        print("=" * 70)
        print("✅ All tests completed successfully!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    run_all_tests()
