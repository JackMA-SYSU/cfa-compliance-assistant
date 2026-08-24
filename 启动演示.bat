@echo off
chcp 65001 >nul
cd /d D:\cfa-compliance-assistant
echo 正在启动 CFA 合规自检助手（局域网演示模式）...
echo 关闭本窗口即可停止服务。
echo.
python scripts\start_demo.py
pause
