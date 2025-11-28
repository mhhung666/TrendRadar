"""
TrendRadar MCP Server - FastMCP 2.0 實現

使用 FastMCP 2.0 提供生產級 MCP 工具服務器。
支持 stdio 和 HTTP 兩種傳輸模式。
"""

import json
from typing import List, Optional, Dict

from fastmcp import FastMCP

from .tools.data_query import DataQueryTools
from .tools.analytics import AnalyticsTools
from .tools.search_tools import SearchTools
from .tools.config_mgmt import ConfigManagementTools
from .tools.system import SystemManagementTools
from .utils.date_parser import DateParser
from .utils.errors import MCPError


# 創建 FastMCP 2.0 應用
mcp = FastMCP('trendradar-news')

# 全局工具實例（在第一次請求時初始化）
_tools_instances = {}


def _get_tools(project_root: Optional[str] = None):
    """獲取或創建工具實例（單例模式）"""
    if not _tools_instances:
        _tools_instances['data'] = DataQueryTools(project_root)
        _tools_instances['analytics'] = AnalyticsTools(project_root)
        _tools_instances['search'] = SearchTools(project_root)
        _tools_instances['config'] = ConfigManagementTools(project_root)
        _tools_instances['system'] = SystemManagementTools(project_root)
    return _tools_instances


# ==================== 日期解析工具（優先調用）====================

@mcp.tool
async def resolve_date_range(
    expression: str
) -> str:
    """
    【推薦優先調用】將自然語言日期表達式解析爲標準日期範圍

    **爲什麼需要這個工具？**
    用戶經常使用"本週"、"最近7天"等自然語言表達日期，但 AI 模型自己計算日期
    可能導致不一致的結果。此工具在服務器端使用精確的當前時間計算，確保所有
    AI 模型獲得一致的日期範圍。

    **推薦使用流程：**
    1. 用戶說"分析AI本週的情感傾向"
    2. AI 調用 resolve_date_range("本週") → 獲取精確日期範圍
    3. AI 調用 analyze_sentiment(topic="ai", date_range=上一步返回的date_range)

    Args:
        expression: 自然語言日期表達式，支持：
            - 單日: "今天", "昨天", "today", "yesterday"
            - 周: "本週", "上週", "this week", "last week"
            - 月: "本月", "上月", "this month", "last month"
            - 最近N天: "最近7天", "最近30天", "last 7 days", "last 30 days"
            - 動態: "最近5天", "last 10 days"（任意天數）

    Returns:
        JSON格式的日期範圍，可直接用於其他工具的 date_range 參數：
        {
            "success": true,
            "expression": "本週",
            "date_range": {
                "start": "2025-11-18",
                "end": "2025-11-26"
            },
            "current_date": "2025-11-26",
            "description": "本週（週一到週日，11-18 至 11-26）"
        }

    Examples:
        用戶："分析AI本週的情感傾向"
        AI調用步驟：
        1. resolve_date_range("本週")
           → {"date_range": {"start": "2025-11-18", "end": "2025-11-26"}, ...}
        2. analyze_sentiment(topic="ai", date_range={"start": "2025-11-18", "end": "2025-11-26"})

        用戶："看看最近7天的特斯拉新聞"
        AI調用步驟：
        1. resolve_date_range("最近7天")
           → {"date_range": {"start": "2025-11-20", "end": "2025-11-26"}, ...}
        2. search_news(query="特斯拉", date_range={"start": "2025-11-20", "end": "2025-11-26"})
    """
    try:
        result = DateParser.resolve_date_range_expression(expression)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except MCPError as e:
        return json.dumps({
            "success": False,
            "error": e.to_dict()
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }, ensure_ascii=False, indent=2)


# ==================== 數據查詢工具 ====================

@mcp.tool
async def get_latest_news(
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    獲取最新一批爬取的新聞數據，快速瞭解當前熱點

    Args:
        platforms: 平臺ID列表，如 ['zhihu', 'weibo', 'douyin']
                   - 不指定時：使用 config.yaml 中配置的所有平臺
                   - 支持的平臺來自 config/config.yaml 的 platforms 配置
                   - 每個平臺都有對應的name字段（如"知乎"、"微博"），方便AI識別
        limit: 返回條數限制，默認50，最大1000
               注意：實際返回數量可能少於請求值，取決於當前可用的新聞總數
        include_url: 是否包含URL鏈接，默認False（節省token）

    Returns:
        JSON格式的新聞列表

    **重要：數據展示建議**
    本工具會返回完整的新聞列表（通常50條）給你。但請注意：
    - **工具返回**：完整的50條數據 ✅
    - **建議展示**：向用戶展示全部數據，除非用戶明確要求總結
    - **用戶期望**：用戶可能需要完整數據，請謹慎總結

    **何時可以總結**：
    - 用戶明確說"給我總結一下"或"挑重點說"
    - 數據量超過100條時，可先展示部分並詢問是否查看全部

    **注意**：如果用戶詢問"爲什麼只顯示了部分"，說明他們需要完整數據
    """
    tools = _get_tools()
    result = tools['data'].get_latest_news(platforms=platforms, limit=limit, include_url=include_url)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_trending_topics(
    top_n: int = 10,
    mode: str = 'current'
) -> str:
    """
    獲取個人關注詞的新聞出現頻率統計（基於 config/frequency_words.txt）

    注意：本工具不是自動提取新聞熱點，而是統計你在 config/frequency_words.txt 中
    設置的個人關注詞在新聞中出現的頻率。你可以自定義這個關注詞列表。

    Args:
        top_n: 返回TOP N關注詞，默認10
        mode: 模式選擇
            - daily: 當日累計數據統計
            - current: 最新一批數據統計（默認）

    Returns:
        JSON格式的關注詞頻率統計列表
    """
    tools = _get_tools()
    result = tools['data'].get_trending_topics(top_n=top_n, mode=mode)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_news_by_date(
    date_query: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    獲取指定日期的新聞數據，用於歷史數據分析和對比

    Args:
        date_query: 日期查詢，可選格式:
            - 自然語言: "今天", "昨天", "前天", "3天前"
            - 標準日期: "2024-01-15", "2024/01/15"
            - 默認值: "今天"（節省token）
        platforms: 平臺ID列表，如 ['zhihu', 'weibo', 'douyin']
                   - 不指定時：使用 config.yaml 中配置的所有平臺
                   - 支持的平臺來自 config/config.yaml 的 platforms 配置
                   - 每個平臺都有對應的name字段（如"知乎"、"微博"），方便AI識別
        limit: 返回條數限制，默認50，最大1000
               注意：實際返回數量可能少於請求值，取決於指定日期的新聞總數
        include_url: 是否包含URL鏈接，默認False（節省token）

    Returns:
        JSON格式的新聞列表，包含標題、平臺、排名等信息

    **重要：數據展示建議**
    本工具會返回完整的新聞列表（通常50條）給你。但請注意：
    - **工具返回**：完整的50條數據 ✅
    - **建議展示**：向用戶展示全部數據，除非用戶明確要求總結
    - **用戶期望**：用戶可能需要完整數據，請謹慎總結

    **何時可以總結**：
    - 用戶明確說"給我總結一下"或"挑重點說"
    - 數據量超過100條時，可先展示部分並詢問是否查看全部

    **注意**：如果用戶詢問"爲什麼只顯示了部分"，說明他們需要完整數據
    """
    tools = _get_tools()
    result = tools['data'].get_news_by_date(
        date_query=date_query,
        platforms=platforms,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)



# ==================== 高級數據分析工具 ====================

@mcp.tool
async def analyze_topic_trend(
    topic: str,
    analysis_type: str = "trend",
    date_range: Optional[Dict[str, str]] = None,
    granularity: str = "day",
    threshold: float = 3.0,
    time_window: int = 24,
    lookahead_hours: int = 6,
    confidence_threshold: float = 0.7
) -> str:
    """
    統一話題趨勢分析工具 - 整合多種趨勢分析模式

    **重要：日期範圍處理**
    當用戶使用"本週"、"最近7天"等自然語言時，請先調用 resolve_date_range 工具獲取精確日期：
    1. 調用 resolve_date_range("本週") → 獲取 {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
    2. 將返回的 date_range 傳入本工具

    Args:
        topic: 話題關鍵詞（必需）
        analysis_type: 分析類型，可選值：
            - "trend": 熱度趨勢分析（追蹤話題的熱度變化）
            - "lifecycle": 生命週期分析（從出現到消失的完整週期）
            - "viral": 異常熱度檢測（識別突然爆火的話題）
            - "predict": 話題預測（預測未來可能的熱點）
        date_range: 日期範圍（trend和lifecycle模式），可選
                    - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **獲取方式**: 調用 resolve_date_range 工具解析自然語言日期
                    - **默認**: 不指定時默認分析最近7天
        granularity: 時間粒度（trend模式），默認"day"（僅支持 day，因爲底層數據按天聚合）
        threshold: 熱度突增倍數閾值（viral模式），默認3.0
        time_window: 檢測時間窗口小時數（viral模式），默認24
        lookahead_hours: 預測未來小時數（predict模式），默認6
        confidence_threshold: 置信度閾值（predict模式），默認0.7

    Returns:
        JSON格式的趨勢分析結果

    Examples:
        用戶："分析AI本週的趨勢"
        推薦調用流程：
        1. resolve_date_range("本週") → {"date_range": {"start": "2025-11-18", "end": "2025-11-26"}}
        2. analyze_topic_trend(topic="AI", date_range={"start": "2025-11-18", "end": "2025-11-26"})

        用戶："看看特斯拉最近30天的熱度"
        推薦調用流程：
        1. resolve_date_range("最近30天") → {"date_range": {"start": "2025-10-28", "end": "2025-11-26"}}
        2. analyze_topic_trend(topic="特斯拉", analysis_type="lifecycle", date_range=...)
    """
    tools = _get_tools()
    result = tools['analytics'].analyze_topic_trend_unified(
        topic=topic,
        analysis_type=analysis_type,
        date_range=date_range,
        granularity=granularity,
        threshold=threshold,
        time_window=time_window,
        lookahead_hours=lookahead_hours,
        confidence_threshold=confidence_threshold
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def analyze_data_insights(
    insight_type: str = "platform_compare",
    topic: Optional[str] = None,
    date_range: Optional[Dict[str, str]] = None,
    min_frequency: int = 3,
    top_n: int = 20
) -> str:
    """
    統一數據洞察分析工具 - 整合多種數據分析模式

    Args:
        insight_type: 洞察類型，可選值：
            - "platform_compare": 平臺對比分析（對比不同平臺對話題的關注度）
            - "platform_activity": 平臺活躍度統計（統計各平臺發佈頻率和活躍時間）
            - "keyword_cooccur": 關鍵詞共現分析（分析關鍵詞同時出現的模式）
        topic: 話題關鍵詞（可選，platform_compare模式適用）
        date_range: **【對象類型】** 日期範圍（可選）
                    - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **示例**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **重要**: 必須是對象格式，不能傳遞整數
        min_frequency: 最小共現頻次（keyword_cooccur模式），默認3
        top_n: 返回TOP N結果（keyword_cooccur模式），默認20

    Returns:
        JSON格式的數據洞察分析結果

    Examples:
        - analyze_data_insights(insight_type="platform_compare", topic="人工智能")
        - analyze_data_insights(insight_type="platform_activity", date_range={"start": "2025-01-01", "end": "2025-01-07"})
        - analyze_data_insights(insight_type="keyword_cooccur", min_frequency=5, top_n=15)
    """
    tools = _get_tools()
    result = tools['analytics'].analyze_data_insights_unified(
        insight_type=insight_type,
        topic=topic,
        date_range=date_range,
        min_frequency=min_frequency,
        top_n=top_n
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def analyze_sentiment(
    topic: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    date_range: Optional[Dict[str, str]] = None,
    limit: int = 50,
    sort_by_weight: bool = True,
    include_url: bool = False
) -> str:
    """
    分析新聞的情感傾向和熱度趨勢

    **重要：日期範圍處理**
    當用戶使用"本週"、"最近7天"等自然語言時，請先調用 resolve_date_range 工具獲取精確日期：
    1. 調用 resolve_date_range("本週") → 獲取 {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
    2. 將返回的 date_range 傳入本工具

    Args:
        topic: 話題關鍵詞（可選）
        platforms: 平臺ID列表，如 ['zhihu', 'weibo', 'douyin']
                   - 不指定時：使用 config.yaml 中配置的所有平臺
                   - 支持的平臺來自 config/config.yaml 的 platforms 配置
                   - 每個平臺都有對應的name字段（如"知乎"、"微博"），方便AI識別
        date_range: 日期範圍（可選）
                    - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **獲取方式**: 調用 resolve_date_range 工具解析自然語言日期
                    - **默認**: 不指定則默認查詢今天的數據
        limit: 返回新聞數量，默認50，最大100
               注意：本工具會對新聞標題進行去重（同一標題在不同平臺只保留一次），
               因此實際返回數量可能少於請求的 limit 值
        sort_by_weight: 是否按熱度權重排序，默認True
        include_url: 是否包含URL鏈接，默認False（節省token）

    Returns:
        JSON格式的分析結果，包含情感分佈、熱度趨勢和相關新聞

    Examples:
        用戶："分析AI本週的情感傾向"
        推薦調用流程：
        1. resolve_date_range("本週") → {"date_range": {"start": "2025-11-18", "end": "2025-11-26"}}
        2. analyze_sentiment(topic="AI", date_range={"start": "2025-11-18", "end": "2025-11-26"})

        用戶："分析特斯拉最近7天的新聞情感"
        推薦調用流程：
        1. resolve_date_range("最近7天") → {"date_range": {"start": "2025-11-20", "end": "2025-11-26"}}
        2. analyze_sentiment(topic="特斯拉", date_range={"start": "2025-11-20", "end": "2025-11-26"})

    **重要：數據展示策略**
    - 本工具返回完整的分析結果和新聞列表
    - **默認展示方式**：展示完整的分析結果（包括所有新聞）
    - 僅在用戶明確要求"總結"或"挑重點"時才進行篩選
    """
    tools = _get_tools()
    result = tools['analytics'].analyze_sentiment(
        topic=topic,
        platforms=platforms,
        date_range=date_range,
        limit=limit,
        sort_by_weight=sort_by_weight,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def find_similar_news(
    reference_title: str,
    threshold: float = 0.6,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    查找與指定新聞標題相似的其他新聞

    Args:
        reference_title: 新聞標題（完整或部分）
        threshold: 相似度閾值，0-1之間，默認0.6
                   注意：閾值越高匹配越嚴格，返回結果越少
        limit: 返回條數限制，默認50，最大100
               注意：實際返回數量取決於相似度匹配結果，可能少於請求值
        include_url: 是否包含URL鏈接，默認False（節省token）

    Returns:
        JSON格式的相似新聞列表，包含相似度分數

    **重要：數據展示策略**
    - 本工具返回完整的相似新聞列表
    - **默認展示方式**：展示全部返回的新聞（包括相似度分數）
    - 僅在用戶明確要求"總結"或"挑重點"時才進行篩選
    """
    tools = _get_tools()
    result = tools['analytics'].find_similar_news(
        reference_title=reference_title,
        threshold=threshold,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def generate_summary_report(
    report_type: str = "daily",
    date_range: Optional[Dict[str, str]] = None
) -> str:
    """
    每日/每週摘要生成器 - 自動生成熱點摘要報告

    Args:
        report_type: 報告類型（daily/weekly）
        date_range: **【對象類型】** 自定義日期範圍（可選）
                    - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **示例**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **重要**: 必須是對象格式，不能傳遞整數

    Returns:
        JSON格式的摘要報告，包含Markdown格式內容
    """
    tools = _get_tools()
    result = tools['analytics'].generate_summary_report(
        report_type=report_type,
        date_range=date_range
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== 智能檢索工具 ====================

@mcp.tool
async def search_news(
    query: str,
    search_mode: str = "keyword",
    date_range: Optional[Dict[str, str]] = None,
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    sort_by: str = "relevance",
    threshold: float = 0.6,
    include_url: bool = False
) -> str:
    """
    統一搜索接口，支持多種搜索模式

    **重要：日期範圍處理**
    當用戶使用"本週"、"最近7天"等自然語言時，請先調用 resolve_date_range 工具獲取精確日期：
    1. 調用 resolve_date_range("本週") → 獲取 {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
    2. 將返回的 date_range 傳入本工具

    Args:
        query: 搜索關鍵詞或內容片段
        search_mode: 搜索模式，可選值：
            - "keyword": 精確關鍵詞匹配（默認，適合搜索特定話題）
            - "fuzzy": 模糊內容匹配（適合搜索內容片段，會過濾相似度低於閾值的結果）
            - "entity": 實體名稱搜索（適合搜索人物/地點/機構）
        date_range: 日期範圍（可選）
                    - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **獲取方式**: 調用 resolve_date_range 工具解析自然語言日期
                    - **默認**: 不指定時默認查詢今天的新聞
        platforms: 平臺ID列表，如 ['zhihu', 'weibo', 'douyin']
                   - 不指定時：使用 config.yaml 中配置的所有平臺
                   - 支持的平臺來自 config/config.yaml 的 platforms 配置
                   - 每個平臺都有對應的name字段（如"知乎"、"微博"），方便AI識別
        limit: 返回條數限制，默認50，最大1000
               注意：實際返回數量取決於搜索匹配結果（特別是 fuzzy 模式下會過濾低相似度結果）
        sort_by: 排序方式，可選值：
            - "relevance": 按相關度排序（默認）
            - "weight": 按新聞權重排序
            - "date": 按日期排序
        threshold: 相似度閾值（僅fuzzy模式有效），0-1之間，默認0.6
                   注意：閾值越高匹配越嚴格，返回結果越少
        include_url: 是否包含URL鏈接，默認False（節省token）

    Returns:
        JSON格式的搜索結果，包含標題、平臺、排名等信息

    Examples:
        用戶："搜索本週的AI新聞"
        推薦調用流程：
        1. resolve_date_range("本週") → {"date_range": {"start": "2025-11-18", "end": "2025-11-26"}}
        2. search_news(query="AI", date_range={"start": "2025-11-18", "end": "2025-11-26"})

        用戶："最近7天的特斯拉新聞"
        推薦調用流程：
        1. resolve_date_range("最近7天") → {"date_range": {"start": "2025-11-20", "end": "2025-11-26"}}
        2. search_news(query="特斯拉", date_range={"start": "2025-11-20", "end": "2025-11-26"})

        用戶："今天的AI新聞"（默認今天，無需解析）
        → search_news(query="AI")

    **重要：數據展示策略**
    - 本工具返回完整的搜索結果列表
    - **默認展示方式**：展示全部返回的新聞，無需總結或篩選
    - 僅在用戶明確要求"總結"或"挑重點"時才進行篩選
    """
    tools = _get_tools()
    result = tools['search'].search_news_unified(
        query=query,
        search_mode=search_mode,
        date_range=date_range,
        platforms=platforms,
        limit=limit,
        sort_by=sort_by,
        threshold=threshold,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def search_related_news_history(
    reference_text: str,
    time_preset: str = "yesterday",
    threshold: float = 0.4,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    基於種子新聞，在歷史數據中搜索相關新聞

    Args:
        reference_text: 參考新聞標題（完整或部分）
        time_preset: 時間範圍預設值，可選：
            - "yesterday": 昨天
            - "last_week": 上週 (7天)
            - "last_month": 上個月 (30天)
            - "custom": 自定義日期範圍（需要提供 start_date 和 end_date）
        threshold: 相關性閾值，0-1之間，默認0.4
                   注意：綜合相似度計算（70%關鍵詞重合 + 30%文本相似度）
                   閾值越高匹配越嚴格，返回結果越少
        limit: 返回條數限制，默認50，最大100
               注意：實際返回數量取決於相關性匹配結果，可能少於請求值
        include_url: 是否包含URL鏈接，默認False（節省token）

    Returns:
        JSON格式的相關新聞列表，包含相關性分數和時間分佈

    **重要：數據展示策略**
    - 本工具返回完整的相關新聞列表
    - **默認展示方式**：展示全部返回的新聞（包括相關性分數）
    - 僅在用戶明確要求"總結"或"挑重點"時才進行篩選
    """
    tools = _get_tools()
    result = tools['search'].search_related_news_history(
        reference_text=reference_text,
        time_preset=time_preset,
        threshold=threshold,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== 配置與系統管理工具 ====================

@mcp.tool
async def get_current_config(
    section: str = "all"
) -> str:
    """
    獲取當前系統配置

    Args:
        section: 配置節，可選值：
            - "all": 所有配置（默認）
            - "crawler": 爬蟲配置
            - "push": 推送配置
            - "keywords": 關鍵詞配置
            - "weights": 權重配置

    Returns:
        JSON格式的配置信息
    """
    tools = _get_tools()
    result = tools['config'].get_current_config(section=section)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_system_status() -> str:
    """
    獲取系統運行狀態和健康檢查信息

    返回系統版本、數據統計、緩存狀態等信息

    Returns:
        JSON格式的系統狀態信息
    """
    tools = _get_tools()
    result = tools['system'].get_system_status()
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def trigger_crawl(
    platforms: Optional[List[str]] = None,
    save_to_local: bool = False,
    include_url: bool = False
) -> str:
    """
    手動觸發一次爬取任務（可選持久化）

    Args:
        platforms: 指定平臺ID列表，如 ['zhihu', 'weibo', 'douyin']
                   - 不指定時：使用 config.yaml 中配置的所有平臺
                   - 支持的平臺來自 config/config.yaml 的 platforms 配置
                   - 每個平臺都有對應的name字段（如"知乎"、"微博"），方便AI識別
                   - 注意：失敗的平臺會在返回結果的 failed_platforms 字段中列出
        save_to_local: 是否保存到本地 output 目錄，默認 False
        include_url: 是否包含URL鏈接，默認False（節省token）

    Returns:
        JSON格式的任務狀態信息，包含：
        - platforms: 成功爬取的平臺列表
        - failed_platforms: 失敗的平臺列表（如有）
        - total_news: 爬取的新聞總數
        - data: 新聞數據

    Examples:
        - 臨時爬取: trigger_crawl(platforms=['zhihu'])
        - 爬取並保存: trigger_crawl(platforms=['weibo'], save_to_local=True)
        - 使用默認平臺: trigger_crawl()  # 爬取config.yaml中配置的所有平臺
    """
    tools = _get_tools()
    result = tools['system'].trigger_crawl(platforms=platforms, save_to_local=save_to_local, include_url=include_url)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== 啓動入口 ====================

def run_server(
    project_root: Optional[str] = None,
    transport: str = 'stdio',
    host: str = '0.0.0.0',
    port: int = 3333
):
    """
    啓動 MCP 服務器

    Args:
        project_root: 項目根目錄路徑
        transport: 傳輸模式，'stdio' 或 'http'
        host: HTTP模式的監聽地址，默認 0.0.0.0
        port: HTTP模式的監聽端口，默認 3333
    """
    # 初始化工具實例
    _get_tools(project_root)

    # 打印啓動信息
    print()
    print("=" * 60)
    print("  TrendRadar MCP Server - FastMCP 2.0")
    print("=" * 60)
    print(f"  傳輸模式: {transport.upper()}")

    if transport == 'stdio':
        print("  協議: MCP over stdio (標準輸入輸出)")
        print("  說明: 通過標準輸入輸出與 MCP 客戶端通信")
    elif transport == 'http':
        print(f"  協議: MCP over HTTP (生產環境)")
        print(f"  服務器監聽: {host}:{port}")

    if project_root:
        print(f"  項目目錄: {project_root}")
    else:
        print("  項目目錄: 當前目錄")

    print()
    print("  已註冊的工具:")
    print("    === 日期解析工具（推薦優先調用）===")
    print("    0. resolve_date_range       - 解析自然語言日期爲標準格式")
    print()
    print("    === 基礎數據查詢（P0核心）===")
    print("    1. get_latest_news        - 獲取最新新聞")
    print("    2. get_news_by_date       - 按日期查詢新聞（支持自然語言）")
    print("    3. get_trending_topics    - 獲取趨勢話題")
    print()
    print("    === 智能檢索工具 ===")
    print("    4. search_news                  - 統一新聞搜索（關鍵詞/模糊/實體）")
    print("    5. search_related_news_history  - 歷史相關新聞檢索")
    print()
    print("    === 高級數據分析 ===")
    print("    6. analyze_topic_trend      - 統一話題趨勢分析（熱度/生命週期/爆火/預測）")
    print("    7. analyze_data_insights    - 統一數據洞察分析（平臺對比/活躍度/關鍵詞共現）")
    print("    8. analyze_sentiment        - 情感傾向分析")
    print("    9. find_similar_news        - 相似新聞查找")
    print("    10. generate_summary_report - 每日/每週摘要生成")
    print()
    print("    === 配置與系統管理 ===")
    print("    11. get_current_config      - 獲取當前系統配置")
    print("    12. get_system_status       - 獲取系統運行狀態")
    print("    13. trigger_crawl           - 手動觸發爬取任務")
    print("=" * 60)
    print()

    # 根據傳輸模式運行服務器
    if transport == 'stdio':
        mcp.run(transport='stdio')
    elif transport == 'http':
        # HTTP 模式（生產推薦）
        mcp.run(
            transport='http',
            host=host,
            port=port,
            path='/mcp'  # HTTP 端點路徑
        )
    else:
        raise ValueError(f"不支持的傳輸模式: {transport}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='TrendRadar MCP Server - 新聞熱點聚合 MCP 工具服務器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
詳細配置教程請查看: README-Cherry-Studio.md
        """
    )
    parser.add_argument(
        '--transport',
        choices=['stdio', 'http'],
        default='stdio',
        help='傳輸模式：stdio (默認) 或 http (生產環境)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='HTTP模式的監聽地址，默認 0.0.0.0'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=3333,
        help='HTTP模式的監聽端口，默認 3333'
    )
    parser.add_argument(
        '--project-root',
        help='項目根目錄路徑'
    )

    args = parser.parse_args()

    run_server(
        project_root=args.project_root,
        transport=args.transport,
        host=args.host,
        port=args.port
    )
