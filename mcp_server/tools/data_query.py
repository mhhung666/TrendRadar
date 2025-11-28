"""
數據查詢工具

實現P0核心的數據查詢工具。
"""

from typing import Dict, List, Optional

from ..services.data_service import DataService
from ..utils.validators import (
    validate_platforms,
    validate_limit,
    validate_keyword,
    validate_date_range,
    validate_top_n,
    validate_mode,
    validate_date_query
)
from ..utils.errors import MCPError


class DataQueryTools:
    """數據查詢工具類"""

    def __init__(self, project_root: str = None):
        """
        初始化數據查詢工具

        Args:
            project_root: 項目根目錄
        """
        self.data_service = DataService(project_root)

    def get_latest_news(
        self,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None,
        include_url: bool = False
    ) -> Dict:
        """
        獲取最新一批爬取的新聞數據

        Args:
            platforms: 平臺ID列表，如 ['zhihu', 'weibo']
            limit: 返回條數限制，默認20
            include_url: 是否包含URL鏈接，默認False（節省token）

        Returns:
            新聞列表字典

        Example:
            >>> tools = DataQueryTools()
            >>> result = tools.get_latest_news(platforms=['zhihu'], limit=10)
            >>> print(result['total'])
            10
        """
        try:
            # 參數驗證
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # 獲取數據
            news_list = self.data_service.get_latest_news(
                platforms=platforms,
                limit=limit,
                include_url=include_url
            )

            return {
                "news": news_list,
                "total": len(news_list),
                "platforms": platforms,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def search_news_by_keyword(
        self,
        keyword: str,
        date_range: Optional[Dict] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Dict:
        """
        按關鍵詞搜索歷史新聞

        Args:
            keyword: 搜索關鍵詞（必需）
            date_range: 日期範圍，格式: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
            platforms: 平臺過濾列表
            limit: 返回條數限制（可選，默認返回所有）

        Returns:
            搜索結果字典

        Example (假設今天是 2025-11-17):
            >>> tools = DataQueryTools()
            >>> result = tools.search_news_by_keyword(
            ...     keyword="人工智能",
            ...     date_range={"start": "2025-11-08", "end": "2025-11-17"},
            ...     limit=50
            ... )
            >>> print(result['total'])
        """
        try:
            # 參數驗證
            keyword = validate_keyword(keyword)
            date_range_tuple = validate_date_range(date_range)
            platforms = validate_platforms(platforms)

            if limit is not None:
                limit = validate_limit(limit, default=100)

            # 搜索數據
            search_result = self.data_service.search_news_by_keyword(
                keyword=keyword,
                date_range=date_range_tuple,
                platforms=platforms,
                limit=limit
            )

            return {
                **search_result,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def get_trending_topics(
        self,
        top_n: Optional[int] = None,
        mode: Optional[str] = None
    ) -> Dict:
        """
        獲取個人關注詞的新聞出現頻率統計

        注意：本工具基於 config/frequency_words.txt 中的個人關注詞列表進行統計，
        而不是自動從新聞中提取熱點話題。這是一個個人可定製的關注詞列表，
        用戶可以根據自己的興趣添加或刪除關注詞。

        Args:
            top_n: 返回TOP N關注詞，默認10
            mode: 模式 - daily(當日累計), current(最新一批), incremental(增量)

        Returns:
            關注詞頻率統計字典，包含每個關注詞在新聞中出現的次數

        Example:
            >>> tools = DataQueryTools()
            >>> result = tools.get_trending_topics(top_n=5, mode="current")
            >>> print(len(result['topics']))
            5
            >>> # 返回的是你在 frequency_words.txt 中設置的關注詞的頻率統計
        """
        try:
            # 參數驗證
            top_n = validate_top_n(top_n, default=10)
            valid_modes = ["daily", "current", "incremental"]
            mode = validate_mode(mode, valid_modes, default="current")

            # 獲取趨勢話題
            trending_result = self.data_service.get_trending_topics(
                top_n=top_n,
                mode=mode
            )

            return {
                **trending_result,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def get_news_by_date(
        self,
        date_query: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None,
        include_url: bool = False
    ) -> Dict:
        """
        按日期查詢新聞，支持自然語言日期

        Args:
            date_query: 日期查詢字符串（可選，默認"今天"），支持：
                - 相對日期：今天、昨天、前天、3天前、yesterday、3 days ago
                - 星期：上週一、本週三、last monday、this friday
                - 絕對日期：2025-10-10、10月10日、2025年10月10日
            platforms: 平臺ID列表，如 ['zhihu', 'weibo']
            limit: 返回條數限制，默認50
            include_url: 是否包含URL鏈接，默認False（節省token）

        Returns:
            新聞列表字典

        Example:
            >>> tools = DataQueryTools()
            >>> # 不指定日期，默認查詢今天
            >>> result = tools.get_news_by_date(platforms=['zhihu'], limit=20)
            >>> # 指定日期
            >>> result = tools.get_news_by_date(
            ...     date_query="昨天",
            ...     platforms=['zhihu'],
            ...     limit=20
            ... )
            >>> print(result['total'])
            20
        """
        try:
            # 參數驗證 - 默認今天
            if date_query is None:
                date_query = "今天"
            target_date = validate_date_query(date_query)
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # 獲取數據
            news_list = self.data_service.get_news_by_date(
                target_date=target_date,
                platforms=platforms,
                limit=limit,
                include_url=include_url
            )

            return {
                "news": news_list,
                "total": len(news_list),
                "date": target_date.strftime("%Y-%m-%d"),
                "date_query": date_query,
                "platforms": platforms,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

