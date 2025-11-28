# TrendRadar 專案架構文檔

> 多平台熱搜新聞監控系統 - 技術架構與運作原理

---

## 📋 目錄

- [專案概述](#專案概述)
- [整體架構](#整體架構)
- [目錄結構](#目錄結構)
- [核心模組](#核心模組)
- [資料流程](#資料流程)
- [技術棧](#技術棧)
- [配置系統](#配置系統)
- [MCP Server](#mcp-server)
- [前端系統](#前端系統)
- [自動化部署](#自動化部署)
- [部署方式](#部署方式)

---

## 專案概述

**TrendRadar** 是一個智能新聞熱搜監控系統，具備以下特點：

- 🔍 **多平台監控**：支援 11+ 個主流平台（微博、知乎、抖音、百度等）
- 🎯 **關鍵詞追蹤**：自定義關注詞，精準捕捉感興趣的話題
- 📊 **智能分析**：基於排名、頻次、熱度的綜合權重計算
- 🔔 **多渠道通知**：支援 8 種通知方式（飛書、釘釘、Telegram 等）
- 🤖 **AI 增強**：內建 MCP Server，為 AI 助手提供智能查詢能力
- 🚀 **靈活部署**：支援本地、Docker、GitHub Actions 等多種部署方式

---

## 整體架構

```
┌─────────────────────────────────────────────────────────────────┐
│                         TrendRadar 系統                          │
└─────────────────────────────────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────▼────────┐      ┌────────▼─────────┐     ┌──────▼──────┐
│  資料收集層     │      │   資料處理層      │     │   展示層     │
│                │      │                  │     │              │
│ • API 爬取     │─────▶│ • 關鍵詞匹配     │────▶│ • HTML 報告  │
│ • 11+ 平台     │      │ • 權重計算       │     │ • TXT 輸出   │
│ • 自動重試     │      │ • 趨勢分析       │     │ • Web 界面   │
└────────────────┘      └──────────────────┘     └──────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
            ┌───────▼────────┐       ┌───────▼────────┐
            │   通知推送層    │       │  AI 分析層     │
            │                │       │                │
            │ • 飛書         │       │ • MCP Server   │
            │ • 釘釘         │       │ • 13 個工具    │
            │ • Telegram     │       │ • 自然語言查詢 │
            │ • 8 種渠道     │       │ • 趨勢洞察     │
            └────────────────┘       └────────────────┘
```

---

## 目錄結構

```
TrendRadar/
├── 📂 config/                      # 配置文件目錄
│   ├── config.yaml                # 主配置文件（平台、通知、權重）
│   └── frequency_words.txt        # 關注詞配置（監控關鍵詞）
│
├── 📂 output/                      # 數據輸出目錄
│   └── 2025年11月28日/           # 按日期分類
│       ├── txt/                   # 文本格式數據
│       └── html/                  # HTML 可視化報告
│
├── 📂 mcp_server/                  # MCP Server 模組
│   ├── server.py                  # FastMCP 服務器主入口（782 行）
│   ├── tools/                     # MCP 工具集
│   │   ├── data_query.py         # 基礎數據查詢
│   │   ├── analytics.py          # 高級分析（趨勢、情感）
│   │   ├── search_tools.py       # 智能檢索
│   │   ├── config_mgmt.py        # 配置管理
│   │   └── system.py             # 系統管理
│   ├── services/                  # 核心服務層
│   │   ├── data_service.py       # 數據查詢服務
│   │   ├── parser_service.py     # 文件解析服務
│   │   └── cache_service.py      # 緩存管理服務
│   └── utils/                     # 工具函數
│       ├── date_parser.py        # 日期解析器
│       ├── validators.py         # 參數驗證器
│       └── errors.py             # 異常定義
│
├── 📂 docker/                      # Docker 部署
│   ├── Dockerfile                # 容器鏡像定義
│   ├── docker-compose.yml        # 服務編排配置
│   └── entrypoint.sh             # 容器啟動腳本
│
├── 📂 .github/workflows/           # GitHub Actions 自動化
│   ├── crawler.yml               # 定時爬蟲工作流（每小時）
│   └── docker.yml                # Docker 構建工作流
│
├── 📄 main.py                      # 核心爬蟲程序（4813 行）
├── 📄 index.html                   # Web 可視化界面
├── 📄 requirements.txt             # Python 依賴
├── 📄 pyproject.toml               # 項目元數據
├── 📄 start-http.sh                # HTTP 模式啟動腳本
└── 📄 setup-mac.sh                 # macOS 自動化部署腳本
```

---

## 核心模組

### 1. 主程序 ([main.py](main.py))

**核心類：NewsAnalyzer**
- **職責**：總控制器，負責爬取、分析、通知
- **代碼量**：4813 行

**三種運行模式**：

| 模式 | 說明 | 推送條件 |
|------|------|---------|
| `daily` | 當日彙總模式 | 按時推送所有匹配新聞 |
| `current` | 當前榜單模式 | 按時推送最新一批數據 |
| `incremental` | 增量模式 | 僅有新增新聞時才推送 |

**主要功能模組**：

```python
class DataFetcher:
    """資料抓取器"""
    def fetch_data(platform_id: str) -> dict:
        """從 API 獲取單個平台熱搜"""

    def crawl_websites(platforms: list) -> dict:
        """批量爬取多個平台"""

# 資料處理函數
def save_titles_to_file():
    """保存原始數據到 txt"""

def count_word_frequency():
    """統計關鍵詞頻率（支援必須詞、排除詞）"""

def generate_html_report():
    """生成 HTML 可視化報告"""

# 通知系統
def send_to_notifications():
    """多渠道推送通知"""

def prepare_report_data():
    """準備推送數據（分批、格式化）"""
```

### 2. MCP Server ([mcp_server/server.py](mcp_server/server.py))

**架構設計**：基於 FastMCP 2.0 的生產級工具服務器

**13 個註冊工具**：

| 工具名稱 | 功能 | 推薦場景 |
|---------|------|---------|
| `resolve_date_range` | 日期解析 | ⭐ 優先調用 |
| `get_latest_news` | 獲取最新新聞 | 快速查看 |
| `get_news_by_date` | 按日期查詢 | 歷史數據 |
| `get_trending_topics` | 獲取趨勢話題 | 發現熱點 |
| `search_news` | 統一搜索接口 | 關鍵詞查找 |
| `search_related_news_history` | 歷史相關新聞 | 追蹤話題發展 |
| `analyze_topic_trend` | 話題趨勢分析 | 熱度變化曲線 |
| `analyze_data_insights` | 數據洞察分析 | 綜合分析 |
| `analyze_sentiment` | 情感傾向分析 | 輿情判斷 |
| `find_similar_news` | 相似新聞查找 | 關聯發現 |
| `generate_summary_report` | 摘要報告生成 | 快速總結 |
| `get_current_config` | 獲取配置 | 系統狀態 |
| `trigger_crawl` | 手動觸發爬取 | 即時更新 |

**服務架構**：

```
AI 助手 (Claude/ChatGPT)
    ↓ (MCP 協議)
FastMCP Server (stdio/http)
    ↓
Tools Layer (13 個工具)
    ↓
Services Layer (數據、解析、緩存)
    ↓
Data Layer (output/ 目錄的 txt 文件)
```

---

## 資料流程

### 完整數據處理流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 資料收集階段                                                  │
└─────────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
    [啟動爬蟲]      [載入配置]      [調用 API]
      main.py       config.yaml    vvhan.com
          │               │               │
          └───────────────┼───────────────┘
                          ↓
            https://api.vvhan.com/api/hotlist
                 (11+ 平台數據)
                          │
┌─────────────────────────────────────────────────────────────────┐
│ 2. 資料解析階段                                                  │
└─────────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
  [解析 JSON]       [去重合併]        [記錄時間]
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ↓
              output/日期/txt/時間.txt
                 (原始數據存儲)
                          │
┌─────────────────────────────────────────────────────────────────┐
│ 3. 智能處理階段                                                  │
└─────────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
  [關鍵詞匹配]      [權重計算]        [趨勢分析]
frequency_words    排名+頻次+熱度      新增標記
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. 輸出與推送階段                                                │
└─────────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
  [生成報告]          [多渠道推送]      [MCP 查詢]
  HTML/TXT          8 種通知方式     AI 智能分析
        │                 │                 │
        ↓                 ↓                 ↓
   index.html        飛書/釘釘/Telegram   Claude/ChatGPT
```

### 關鍵詞匹配邏輯

```python
# frequency_words.txt 語法示例

# 1. 普通詞（OR 邏輯）
華為
比亞迪
AI

# 2. 必須詞組合（AND 邏輯，用空行分隔）
華為        # 詞組1：同時包含"華為"和"鴻蒙"
鴻蒙

特斯拉      # 詞組2：同時包含"特斯拉"和"馬斯克"
馬斯克

# 3. 排除詞（前綴 !）
!車         # 排除包含"車"的新聞
!餐         # 排除包含"餐"的新聞
```

### 權重計算公式

```python
綜合權重 = (排名權重 × 0.6) + (頻次權重 × 0.3) + (熱度權重 × 0.1)

其中：
- 排名權重 = (100 - 排名) / 100  # 排名越高分數越高
- 頻次權重 = 出現次數 / 最大出現次數
- 熱度權重 = 熱度值 / 最大熱度值
```

---

## 技術棧

### 核心依賴

```python
# requirements.txt
requests>=2.32.5      # HTTP 請求庫
pytz>=2025.2          # 時區處理
PyYAML>=6.0.3         # YAML 配置解析
fastmcp>=2.12.0       # MCP Server 框架
websockets>=13.0      # WebSocket 支持
```

### 技術特點

- ✅ **無第三方爬蟲依賴**：直接調用公開 API
- ✅ **輕量級設計**：僅 5 個核心依賴
- ✅ **純 Python 實現**：無需複雜編譯環境
- ✅ **跨平台支持**：Windows、macOS、Linux、Docker

### 支援平台 (11+)

| 平台 | ID | 平台 | ID |
|------|-------|------|-------|
| 今日頭條 | toutiao | 百度熱搜 | baidu |
| 微博熱搜 | weibo | 知乎熱榜 | zhihu |
| 抖音熱搜 | douyin | B站熱搜 | bilibili |
| 36氪 | 36ke | 少數派 | sspai |
| IT之家 | ithome | 澎湃新聞 | thepaper |
| 天涯 | tianya | | |

---

## 配置系統

### 1. 主配置文件 ([config/config.yaml](config/config.yaml))

**核心配置區塊**：

#### 應用配置
```yaml
app:
  version_check_url: "https://api.github.com/repos/..."
  show_version_update: true
```

#### 爬蟲配置
```yaml
crawler:
  request_interval: 1000         # 請求間隔（毫秒）
  enable_crawler: true           # 是否啟用爬蟲
  use_proxy: false               # 是否使用代理
  max_retries: 3                 # 最大重試次數
```

#### 報告模式
```yaml
report:
  mode: "daily"                  # daily/incremental/current
  rank_threshold: 5              # 排名高亮閾值（≤5 標記為 🔥）
  sort_by_position_first: false  # 優先按排名排序
  max_news_per_keyword: 0        # 每個關鍵詞最大顯示數（0=無限制）
```

#### 通知配置
```yaml
notification:
  enable_notification: true
  push_window:                   # 推送時間窗口
    enabled: false
    time_range:
      start: "20:00"
      end: "22:00"
    once_per_day: true           # 每日只推送一次
  webhooks:
    feishu_url: ""               # 飛書 Webhook
    dingtalk_url: ""             # 釘釘 Webhook
    wecom_url: ""                # 企業微信 Webhook
    telegram_bot_token: ""       # Telegram Bot Token
    telegram_chat_id: ""         # Telegram Chat ID
    email_config:                # 郵件配置
      smtp_server: ""
      smtp_port: 587
      sender: ""
      password: ""
      recipients: []
    ntfy_topic: ""               # ntfy 主題
    bark_url: ""                 # Bark URL
    slack_webhook_url: ""        # Slack Webhook
```

#### 權重配置
```yaml
weight:
  rank_weight: 0.6               # 排名權重
  frequency_weight: 0.3          # 頻次權重
  hotness_weight: 0.1            # 熱度權重
```

### 2. 關注詞配置 ([config/frequency_words.txt](config/frequency_words.txt))

**實際配置示例**（114 行）：

```
# 國產科技
胖東來
DeepSeek
華為
比亞迪
大疆

# 國際科技
特斯拉
微軟
英偉達
OpenAI
Google

# 關鍵技術
AI
自動駕駛
機器人
芯片

# 綜合話題
三體
黑神話
核能

# 排除詞
!車
!餐
```

### 環境變量支持

配置優先級：**環境變量 > config.yaml**

```bash
# 支持的環境變量
FEISHU_WEBHOOK_URL=""
DINGTALK_WEBHOOK_URL=""
WECOM_WEBHOOK_URL=""
TELEGRAM_BOT_TOKEN=""
TELEGRAM_CHAT_ID=""
REPORT_MODE="daily"              # daily/incremental/current
ENABLE_NOTIFICATION="true"
```

---

## MCP Server

### 核心定位

MCP Server 是 TrendRadar 的 **AI 智能分析層**：

- 📚 將歷史新聞數據轉化為可查詢的知識庫
- 🤖 為 AI 助手（Claude、ChatGPT 等）提供專業工具
- 💬 支持自然語言交互式數據分析

### 兩種運行模式

#### 1. stdio 模式（本地）

```bash
python -m mcp_server.server --transport stdio
```

- **適用場景**：Claude Desktop、本地 AI 客戶端
- **協議**：標準輸入輸出
- **優點**：低延遲、高安全性

**Claude Desktop 配置**：
```json
{
  "mcpServers": {
    "trendradar": {
      "command": "python",
      "args": ["-m", "mcp_server.server", "--transport", "stdio"],
      "cwd": "/path/to/TrendRadar"
    }
  }
}
```

#### 2. HTTP 模式（遠程）

```bash
# macOS/Linux
./start-http.sh

# Windows
start-http.bat

# 手動啟動
python -m mcp_server.server --transport http --port 3333
```

- **適用場景**：遠程訪問、團隊共享
- **協議**：HTTP + WebSocket
- **端點**：`http://localhost:3333/mcp`

### 高級功能示例

#### 趨勢分析
```python
# AI 調用流程
1. resolve_date_range("本週")
   → {"start": "2025-11-18", "end": "2025-11-26"}

2. analyze_topic_trend(
     topic="AI",
     date_range={"start": "2025-11-18", "end": "2025-11-26"}
   )

# 返回結果
{
  "trend_chart": [...],           # 熱度變化曲線
  "spike_detection": {...},       # 爆火檢測
  "lifecycle_stage": "成長期",    # 生命週期
  "top_news": [...]               # 代表性新聞
}
```

#### 智能搜索
```python
# 支持三種模式
search_news(
  query="特斯拉",
  search_mode="keyword",    # keyword/fuzzy/entity
  date_range={...},
  max_results=10
)
```

#### 情感分析
```python
analyze_sentiment(
  topic="華為",
  date_range={...}
)

# 返回
{
  "positive_ratio": 0.75,
  "negative_ratio": 0.15,
  "neutral_ratio": 0.10,
  "sample_news": {...}
}
```

---

## 前端系統

### 架構關係

```
前端界面                後端程序
─────────              ─────────
index.html  ←────┐     main.py (爬蟲 + 通知)
                 │         ↓
HTML 報告    ←───┤     生成數據文件
                 │         ↓
AI 助手      ←───┴─    mcp_server (數據查詢)
```

### [index.html](index.html) 特點

- **靜態 HTML**：無需後端服務器，直接在瀏覽器打開
- **數據嵌入**：JavaScript 變量直接包含新聞數據
- **核心功能**：
  - 🔍 實時搜索和過濾
  - 📋 複製分享鏈接
  - 📸 截圖保存（html2canvas）
  - 📱 響應式設計

### 生成機制

```python
# main.py 中
def generate_html_report():
    # 1. 讀取 HTML 模板
    # 2. 插入新聞數據到 JavaScript 變量
    # 3. 保存到兩個位置：
    #    - output/日期/html/時間.html
    #    - 根目錄/index.html（最新報告）
```

---

## 自動化部署

### GitHub Actions 工作流

#### [crawler.yml](.github/workflows/crawler.yml) - 定時爬蟲

**觸發方式**：
- **定時執行**：`cron: "0 * * * *"` (每小時整點)
- **手動觸發**：`workflow_dispatch`

**執行步驟**：
```yaml
jobs:
  crawl:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: 檢出代碼
        uses: actions/checkout@v3

      - name: 設置 Python 3.10
        uses: actions/setup-python@v4

      - name: 安裝依賴
        run: pip install -r requirements.txt

      - name: 驗證配置文件
        run: |
          test -f config/config.yaml
          test -f config/frequency_words.txt

      - name: 運行爬蟲
        env:
          FEISHU_WEBHOOK_URL: ${{ secrets.FEISHU_WEBHOOK_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          # ... 其他 secrets
        run: python main.py

      - name: 提交更新
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add output/ index.html
          git commit -m "Auto update by GitHub Actions"
          git push
```

**安全特性**：
- ✅ Webhook 存儲在 GitHub Secrets
- ✅ 並發控制（同時只運行一個實例）
- ✅ 超時保護（30 分鐘）
- ✅ 衝突重試（最多 5 次）

### 配置 GitHub Secrets

```
Settings → Secrets and variables → Actions → New repository secret

建議配置：
- FEISHU_WEBHOOK_URL
- DINGTALK_WEBHOOK_URL
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- EMAIL_PASSWORD
```

---

## 部署方式

### 方式對比

| 部署方式 | 適用場景 | 優點 | 缺點 | 成本 |
|---------|---------|------|------|------|
| **本地運行** | 測試、開發 | 靈活、即時 | 需手動執行 | 免費 |
| **Docker** | 個人服務器 | 穩定、自動化 | 需服務器資源 | 服務器成本 |
| **GitHub Actions** | 零成本部署 | 完全免費、自動執行 | 時間不精確（±15分鐘） | 免費 |
| **MCP Server** | AI 輔助分析 | 智能查詢、自然語言 | 需 AI 客戶端 | 免費 |

### 1. 本地部署

#### 基本運行
```bash
# 1. 克隆項目
git clone https://github.com/your-username/TrendRadar.git
cd TrendRadar

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 配置文件
# 編輯 config/config.yaml（添加 webhook）
# 編輯 config/frequency_words.txt（添加關注詞）

# 4. 運行爬蟲
python main.py
```

#### macOS 自動化部署
```bash
# 一鍵設置
./setup-mac.sh

# 功能：
# - 創建虛擬環境
# - 安裝依賴
# - 配置啟動腳本
# - 設置定時任務
```

### 2. Docker 部署（推薦）

```bash
# 1. 進入 docker 目錄
cd docker/

# 2. 創建 .env 文件
cat > .env << EOF
CRON_SCHEDULE=*/5 * * * *    # 每 5 分鐘執行
RUN_MODE=cron                # cron/once
IMMEDIATE_RUN=true           # 立即執行一次
FEISHU_WEBHOOK_URL=https://...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
EOF

# 3. 啟動服務
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 停止服務
docker-compose down
```

**Docker 特點**：
- ✅ 基於 `python:3.10-slim`
- ✅ 使用 supercronic（更穩定的 cron）
- ✅ 支持 amd64 和 arm64 架構
- ✅ 自動健康檢查

### 3. GitHub Actions 部署（零成本）

```bash
# 1. Fork 項目到自己的 GitHub
# 2. 配置 Secrets
#    Settings → Secrets and variables → Actions
#    添加：FEISHU_WEBHOOK_URL, TELEGRAM_BOT_TOKEN 等

# 3. 啟用 Actions
#    Actions → I understand my workflows, go ahead and enable them

# 4. 手動觸發測試
#    Actions → Crawler → Run workflow

# 5. 等待自動執行（每小時整點）
```

### 4. MCP Server 部署

#### HTTP 模式（適合遠程訪問）
```bash
# macOS/Linux
./start-http.sh

# Windows
start-http.bat

# 訪問測試
curl http://localhost:3333/mcp
```

#### stdio 模式（適合本地 AI 客戶端）
```bash
python -m mcp_server.server --transport stdio
```

---

## 核心文件路徑速查

### 配置文件
- [config/config.yaml](config/config.yaml) - 主配置（122 行）
- [config/frequency_words.txt](config/frequency_words.txt) - 關注詞（114 行）

### 程序文件
- [main.py](main.py) - 爬蟲主程序（4813 行）
- [mcp_server/server.py](mcp_server/server.py) - MCP 服務器（782 行）
- [index.html](index.html) - Web 可視化界面

### 部署文件
- [docker/Dockerfile](docker/Dockerfile) - Docker 鏡像
- [docker/docker-compose.yml](docker/docker-compose.yml) - 服務編排
- [.github/workflows/crawler.yml](.github/workflows/crawler.yml) - 自動化工作流

### 服務層
- [mcp_server/services/data_service.py](mcp_server/services/data_service.py) - 數據服務
- [mcp_server/services/parser_service.py](mcp_server/services/parser_service.py) - 解析服務
- [mcp_server/tools/analytics.py](mcp_server/tools/analytics.py) - 分析工具（74KB）

---

## 常見問題

### Q1: 如何添加新的關注詞？
編輯 `config/frequency_words.txt`，每行一個關鍵詞即可。

### Q2: 如何修改爬取頻率？
- **本地/Docker**：修改 `config.yaml` 中的 `request_interval`
- **GitHub Actions**：修改 `.github/workflows/crawler.yml` 中的 `cron` 表達式

### Q3: 如何查看歷史數據？
使用 MCP Server 的 AI 查詢功能，或直接訪問 `output/日期/` 目錄。

### Q4: 推送通知不工作？
1. 檢查 webhook URL 是否正確
2. 確認 `enable_notification: true`
3. 檢查推送時間窗口設置
4. 查看日志輸出的錯誤信息

### Q5: GitHub Actions 執行不穩定？
由於免費版有 ±15 分鐘的時間誤差，建議使用 Docker 部署以獲得精確定時。

---

## 貢獻指南

歡迎提交 Issue 和 Pull Request！

**開發環境設置**：
```bash
# 1. Fork 並克隆項目
git clone https://github.com/your-username/TrendRadar.git

# 2. 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安裝開發依賴
pip install -r requirements.txt

# 4. 運行測試
python main.py
```

---

## 授權協議

本項目採用 MIT 授權協議。

---

## 聯繫方式

- 項目主頁：[GitHub](https://github.com/your-username/TrendRadar)
- 問題反饋：[Issues](https://github.com/your-username/TrendRadar/issues)

---

**最後更新時間**：2025-11-28
