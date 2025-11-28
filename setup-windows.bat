@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo   TrendRadar MCP 一鍵部署 (Windows)
echo ==========================================
echo.

REM 修復：使用腳本所在目錄，而不是當前工作目錄
set "PROJECT_ROOT=%~dp0"
REM 移除末尾的反斜槓
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

echo 📍 項目目錄: %PROJECT_ROOT%
echo.

REM 切換到項目目錄
cd /d "%PROJECT_ROOT%"
if %errorlevel% neq 0 (
    echo ❌ 無法訪問項目目錄
    pause
    exit /b 1
)

REM 驗證項目結構
echo [0/4] 🔍 驗證項目結構...
if not exist "pyproject.toml" (
    echo ❌ 未找到 pyproject.toml 文件: %PROJECT_ROOT%
    echo.
    echo 請檢查:
    echo   1. setup-windows.bat 是否在項目根目錄?
    echo   2. 項目文件是否完整?
    echo.
    echo 當前目錄內容:
    dir /b
    echo.
    pause
    exit /b 1
)
echo ✅ pyproject.toml 已找到
echo.

REM 檢查 Python
echo [1/4] 🐍 檢查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未檢測到 Python，請先安裝 Python 3.10+
    echo 下載地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo ✅ %%i
echo.

REM 檢查 UV
echo [2/4] 🔧 檢查 UV...
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo UV 未安裝，正在自動安裝...
    echo.
    
    echo 嘗試方法1: PowerShell 安裝...
    powershell -ExecutionPolicy Bypass -Command "try { irm https://astral.sh/uv/install.ps1 | iex; exit 0 } catch { Write-Host 'PowerShell 安裝失敗'; exit 1 }"
    
    if %errorlevel% neq 0 (
        echo.
        echo 方法1失敗，嘗試方法2: pip 安裝...
        python -m pip install --upgrade uv
        
        if %errorlevel% neq 0 (
            echo.
            echo ❌ 自動安裝失敗
            echo.
            echo 請手動安裝 UV，可選方法:
            echo.
            echo   方法1 - pip:
            echo     python -m pip install uv
            echo.
            echo   方法2 - pipx:
            echo     pip install pipx
            echo     pipx install uv
            echo.
            echo   方法3 - 手動下載:
            echo     訪問: https://docs.astral.sh/uv/getting-started/installation/
            echo.
            pause
            exit /b 1
        )
    )
    
    echo.
    echo ✅ UV 安裝完成！
    echo.
    echo ⚠️  重要: 請按照以下步驟操作:
    echo   1. 關閉此窗口
    echo   2. 重新打開命令提示符（或 PowerShell）
    echo   3. 回到項目目錄: %PROJECT_ROOT%
    echo   4. 重新運行此腳本: setup-windows.bat
    echo.
    pause
    exit /b 0
) else (
    for /f "tokens=*" %%i in ('uv --version') do echo ✅ %%i
)
echo.

echo [3/4] 📦 安裝項目依賴...
echo 工作目錄: %PROJECT_ROOT%
echo.

REM 確保在項目目錄下執行
cd /d "%PROJECT_ROOT%"
uv sync
if %errorlevel% neq 0 (
    echo.
    echo ❌ 依賴安裝失敗
    echo.
    echo 可能的原因:
    echo   1. 網絡連接問題
    echo   2. Python 版本不兼容（需要 ^>= 3.10）
    echo   3. pyproject.toml 文件格式錯誤
    echo.
    echo 故障排查:
    echo   - 檢查網絡連接
    echo   - 驗證 Python 版本: python --version
    echo   - 嘗試詳細輸出: uv sync --verbose
    echo.
    echo 項目目錄: %PROJECT_ROOT%
    echo.
    pause
    exit /b 1
)
echo.
echo ✅ 依賴安裝成功
echo.

echo [4/4] ⚙️  檢查配置文件...
if not exist "config\config.yaml" (
    echo ⚠️  配置文件不存在: config\config.yaml
    if exist "config\config.example.yaml" (
        echo.
        echo 創建配置文件:
        echo   1. 複製: copy config\config.example.yaml config\config.yaml
        echo   2. 編輯: notepad config\config.yaml
        echo   3. 填入 API 密鑰
    )
    echo.
) else (
    echo ✅ config\config.yaml 已存在
)
echo.

REM 獲取 UV 路徑
for /f "tokens=*" %%i in ('where uv 2^>nul') do set "UV_PATH=%%i"
if not defined UV_PATH (
    set "UV_PATH=uv"
)

echo.
echo ==========================================
echo            部署完成！
echo ==========================================
echo.
echo 📋 MCP 服務器配置信息（用於 Claude Desktop）:
echo.
echo   命令: %UV_PATH%
echo   工作目錄: %PROJECT_ROOT%
echo.
echo   參數（逐行填入）:
echo     --directory
echo     %PROJECT_ROOT%
echo     run
echo     python
echo     -m
echo     mcp_server.server
echo.
echo 📖 詳細教程: README-Cherry-Studio.md
echo.
echo.
pause