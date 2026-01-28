@echo off
chcp 65001 >nul
echo 📊 WSL磁盘详细分析
echo ============================================================

echo.
echo 🐧 Ubuntu 22.04 磁盘使用情况:
echo ------------------------------------------------------------
wsl -d Ubuntu-22.04 -- df -h /

echo.
echo 📁 主要目录占用 (Top 15):
echo ------------------------------------------------------------
wsl -d Ubuntu-22.04 -- bash -c "du -sh /* 2^>/dev/null ^| sort -hr ^| head -15"

echo.
echo 🏠 Home目录内容:
echo ------------------------------------------------------------
wsl -d Ubuntu-22.04 -- bash -c "du -sh ~/.* ~/* 2^>/dev/null ^| sort -hr ^| head -15"

echo.
echo 📦 最大的文件 (100MB+):
echo ------------------------------------------------------------
wsl -d Ubuntu-22.04 -- bash -c "find / -type f -size +100M 2^>/dev/null ^| xargs du -sh 2^>/dev/null ^| sort -hr ^| head -10"

echo.
echo 🐳 Docker系统占用:
echo ------------------------------------------------------------
docker system df

echo.
echo 🖼️ Docker镜像详情:
echo ------------------------------------------------------------
docker images

echo.
echo 📦 Docker容器:
echo ------------------------------------------------------------
docker ps -as

echo.
echo ============================================================
echo ✅ 分析完成
echo.
echo 💡 快速清理命令:
echo    1. Docker清理: docker system prune -a --volumes
echo    2. Ubuntu清理: wsl -d Ubuntu-22.04 -- sudo apt-get clean
echo    3. 压缩WSL磁盘:
echo       wsl --shutdown
echo       powershell.exe Optimize-VHD -Path "%USERPROFILE%\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu22.04LTS_79rhkp1fndgsc\LocalState\ext4.vhdx" -Mode Full
echo ============================================================

pause
