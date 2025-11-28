#!/bin/bash

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}╔════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║  TrendRadar MCP 一鍵部署 (Mac)        ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════╝${NC}"
echo ""

# 獲取項目根目錄
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo -e "📍 項目目錄: ${BLUE}${PROJECT_ROOT}${NC}"
echo ""

# 檢查 UV 是否已安裝
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}[1/3] 🔧 UV 未安裝，正在自動安裝...${NC}"
    echo "提示: UV 是一個快速的 Python 包管理器，只需安裝一次"
    echo ""
    curl -LsSf https://astral.sh/uv/install.sh | sh

    echo ""
    echo "正在刷新 PATH 環境變量..."
    echo ""

    # 添加 UV 到 PATH
    export PATH="$HOME/.cargo/bin:$PATH"

    # 驗證 UV 是否真正可用
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}❌ [錯誤] UV 安裝失敗${NC}"
        echo ""
        echo "可能的原因："
        echo "  1. 網絡連接問題，無法下載安裝腳本"
        echo "  2. 安裝路徑權限不足"
        echo "  3. 安裝腳本執行異常"
        echo ""
        echo "解決方案："
        echo "  1. 檢查網絡連接是否正常"
        echo "  2. 手動安裝: https://docs.astral.sh/uv/getting-started/installation/"
        echo "  3. 或運行: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    echo -e "${GREEN}✅ [成功] UV 已安裝${NC}"
    echo -e "${YELLOW}⚠️  請重新運行此腳本以繼續${NC}"
    exit 0
else
    echo -e "${GREEN}[1/3] ✅ UV 已安裝${NC}"
    uv --version
fi

echo ""
echo "[2/3] 📦 安裝項目依賴..."
echo "提示: 這可能需要 1-2 分鐘，請耐心等待"
echo ""

# 創建虛擬環境並安裝依賴
uv sync

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ [錯誤] 依賴安裝失敗${NC}"
    echo "請檢查網絡連接後重試"
    exit 1
fi

echo ""
echo -e "${GREEN}[3/3] ✅ 檢查配置文件...${NC}"
echo ""

# 檢查配置文件
if [ ! -f "config/config.yaml" ]; then
    echo -e "${YELLOW}⚠️  [警告] 未找到配置文件: config/config.yaml${NC}"
    echo "請確保配置文件存在"
    echo ""
fi

# 添加執行權限
chmod +x start-http.sh 2>/dev/null || true

# 獲取 UV 路徑
UV_PATH=$(which uv)

echo ""
echo -e "${BOLD}╔════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║           部署完成！                   ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════╝${NC}"
echo ""
echo "📋 下一步操作:"
echo ""
echo "  1️⃣  打開 Cherry Studio"
echo "  2️⃣  進入 設置 > MCP Servers > 添加服務器"
echo "  3️⃣  填入以下配置:"
echo ""
echo "      名稱: TrendRadar"
echo "      描述: 新聞熱點聚合工具"
echo "      類型: STDIO"
echo -e "      命令: ${BLUE}${UV_PATH}${NC}"
echo "      參數（每個佔一行）:"
echo -e "        ${BLUE}--directory${NC}"
echo -e "        ${BLUE}${PROJECT_ROOT}${NC}"
echo -e "        ${BLUE}run${NC}"
echo -e "        ${BLUE}python${NC}"
echo -e "        ${BLUE}-m${NC}"
echo -e "        ${BLUE}mcp_server.server${NC}"
echo ""
echo "  4️⃣  保存並啓用 MCP 開關"
echo ""
echo "📖 詳細教程請查看: README-Cherry-Studio.md，本窗口別關，待會兒用於填入參數"
echo ""
