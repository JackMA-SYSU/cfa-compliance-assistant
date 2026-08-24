@echo off
chcp 65001 >nul
cd /d D:\cfa-compliance-assistant
echo 正在打开 AI 开发助手...
echo 提示：它会读取项目里的 AGENTS.md（记忆文档），并尝试续接上次会话。
echo.
opencode -c
