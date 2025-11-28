#!/bin/bash

echo "╔════════════════════════════════════════╗"
echo "║  TrendRadar MCP Server (HTTP 模式)    ║"
echo "╚════════════════════════════════════════╝"
echo ""

# 檢查虛擬環境
if [ ! -d ".venv" ]; then
    echo "❌ [錯誤] 虛擬環境未找到"
    echo "請先運行 ./setup-mac.sh 進行部署"
    echo ""
    exit 1
fi

echo "[模式] HTTP (適合遠程訪問)"
echo "[地址] http://localhost:3333/mcp"
echo "[提示] 按 Ctrl+C 停止服務"
echo ""

uv run python -m mcp_server.server --transport http --host 0.0.0.0 --port 3333
