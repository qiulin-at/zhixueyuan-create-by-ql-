@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist "..\.venv\Scripts\python.exe" (
  echo [错误] 找不到虚拟环境：..\.venv\Scripts\python.exe
  echo 请先在项目根目录创建 .venv 并安装依赖：
  echo     python -m venv .venv
  echo     .venv\Scripts\python.exe -m pip install -r backend\requirements.txt
  echo.
  pause
  exit /b 1
)

echo ============================================
echo   智学云 · 面向教育平台的智能体
echo   接口: http://127.0.0.1:8000
echo   文档: http://127.0.0.1:8000/docs
echo   停止: 按 Ctrl+C
echo ============================================
echo.

"..\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000

echo.
echo 服务已停止。若上方有报错，常见原因是 8000 端口被占用。
echo 按任意键关闭窗口。
pause >nul
