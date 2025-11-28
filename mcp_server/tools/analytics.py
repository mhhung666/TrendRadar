"""
高級數據分析工具

提供熱度趨勢分析、平臺對比、關鍵詞共現、情感分析等高級分析功能。
"""

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from difflib import SequenceMatcher

from ..services.data_service import DataService
from ..utils.validators import (
    validate_platforms,
    validate_limit,
    validate_keyword,
    validate_top_n,
    validate_date_range
)
from ..utils.errors import MCPError, InvalidParameterError, DataNotFoundError


def calculate_news_weight(news_data: Dict, rank_threshold: int = 5) -> float:
    """
    計算新聞權重（用於排序）

    基於 main.py 的權重算法實現，綜合考慮：
    - 排名權重 (60%)：新聞在榜單中的排名
    - 頻次權重 (30%)：新聞出現的次數
    - 熱度權重 (10%)：高排名出現的比例

    Args:
        news_data: 新聞數據字典，包含 ranks 和 count 字段
        rank_threshold: 高排名閾值，默認5

    Returns:
        權重分數（0-100之間的浮點數）
    """
    ranks = news_data.get("ranks", [])
    if not ranks:
        return 0.0

    count = news_data.get("count", len(ranks))

    # 權重配置（與 config.yaml 保持一致）
    RANK_WEIGHT = 0.6
    FREQUENCY_WEIGHT = 0.3
    HOTNESS_WEIGHT = 0.1

    # 1. 排名權重：Σ(11 - min(rank, 10)) / 出現次數
    rank_scores = []
    for rank in ranks:
        score = 11 - min(rank, 10)
        rank_scores.append(score)

    rank_weight = sum(rank_scores) / len(ranks) if ranks else 0

    # 2. 頻次權重：min(出現次數, 10) × 10
    frequency_weight = min(count, 10) * 10

    # 3. 熱度加成：高排名次數 / 總出現次數 × 100
    high_rank_count = sum(1 for rank in ranks if rank <= rank_threshold)
    hotness_ratio = high_rank_count / len(ranks) if ranks else 0
    hotness_weight = hotness_ratio * 100

    # 綜合權重
    total_weight = (
        rank_weight * RANK_WEIGHT
        + frequency_weight * FREQUENCY_WEIGHT
        + hotness_weight * HOTNESS_WEIGHT
    )

    return total_weight


class AnalyticsTools:
    """高級數據分析工具類"""

    def __init__(self, project_root: str = None):
        """
        初始化分析工具

        Args:
            project_root: 項目根目錄
        """
        self.data_service = DataService(project_root)

    def analyze_data_insights_unified(
        self,
        insight_type: str = "platform_compare",
        topic: Optional[str] = None,
        date_range: Optional[Dict[str, str]] = None,
        min_frequency: int = 3,
        top_n: int = 20
    ) -> Dict:
        """
        統一數據洞察分析工具 - 整合多種數據分析模式

        Args:
            insight_type: 洞察類型，可選值：
                - "platform_compare": 平臺對比分析（對比不同平臺對話題的關注度）
                - "platform_activity": 平臺活躍度統計（統計各平臺發佈頻率和活躍時間）
                - "keyword_cooccur": 關鍵詞共現分析（分析關鍵詞同時出現的模式）
            topic: 話題關鍵詞（可選，platform_compare模式適用）
            date_range: 日期範圍，格式: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
            min_frequency: 最小共現頻次（keyword_cooccur模式），默認3
            top_n: 返回TOP N結果（keyword_cooccur模式），默認20

        Returns:
            數據洞察分析結果字典

        Examples:
            - analyze_data_insights_unified(insight_type="platform_compare", topic="人工智能")
            - analyze_data_insights_unified(insight_type="platform_activity", date_range={...})
            - analyze_data_insights_unified(insight_type="keyword_cooccur", min_frequency=5)
        """
        try:
            # 參數驗證
            if insight_type not in ["platform_compare", "platform_activity", "keyword_cooccur"]:
                raise InvalidParameterError(
                    f"無效的洞察類型: {insight_type}",
                    suggestion="支持的類型: platform_compare, platform_activity, keyword_cooccur"
                )

            # 根據洞察類型調用相應方法
            if insight_type == "platform_compare":
                return self.compare_platforms(
                    topic=topic,
                    date_range=date_range
                )
            elif insight_type == "platform_activity":
                return self.get_platform_activity_stats(
                    date_range=date_range
                )
            else:  # keyword_cooccur
                return self.analyze_keyword_cooccurrence(
                    min_frequency=min_frequency,
                    top_n=top_n
                )

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

    def analyze_topic_trend_unified(
        self,
        topic: str,
        analysis_type: str = "trend",
        date_range: Optional[Dict[str, str]] = None,
        granularity: str = "day",
        threshold: float = 3.0,
        time_window: int = 24,
        lookahead_hours: int = 6,
        confidence_threshold: float = 0.7
    ) -> Dict:
        """
        統一話題趨勢分析工具 - 整合多種趨勢分析模式

        Args:
            topic: 話題關鍵詞（必需）
            analysis_type: 分析類型，可選值：
                - "trend": 熱度趨勢分析（追蹤話題的熱度變化）
                - "lifecycle": 生命週期分析（從出現到消失的完整週期）
                - "viral": 異常熱度檢測（識別突然爆火的話題）
                - "predict": 話題預測（預測未來可能的熱點）
            date_range: 日期範圍（trend和lifecycle模式），可選
                       - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **默認**: 不指定時默認分析最近7天
            granularity: 時間粒度（trend模式），默認"day"（hour/day）
            threshold: 熱度突增倍數閾值（viral模式），默認3.0
            time_window: 檢測時間窗口小時數（viral模式），默認24
            lookahead_hours: 預測未來小時數（predict模式），默認6
            confidence_threshold: 置信度閾值（predict模式），默認0.7

        Returns:
            趨勢分析結果字典

        Examples (假設今天是 2025-11-17):
            - 用戶："分析AI最近7天的趨勢" → analyze_topic_trend_unified(topic="人工智能", analysis_type="trend", date_range={"start": "2025-11-11", "end": "2025-11-17"})
            - 用戶："看看特斯拉本月的熱度" → analyze_topic_trend_unified(topic="特斯拉", analysis_type="lifecycle", date_range={"start": "2025-11-01", "end": "2025-11-17"})
            - analyze_topic_trend_unified(topic="比特幣", analysis_type="viral", threshold=3.0)
            - analyze_topic_trend_unified(topic="ChatGPT", analysis_type="predict", lookahead_hours=6)
        """
        try:
            # 參數驗證
            topic = validate_keyword(topic)

            if analysis_type not in ["trend", "lifecycle", "viral", "predict"]:
                raise InvalidParameterError(
                    f"無效的分析類型: {analysis_type}",
                    suggestion="支持的類型: trend, lifecycle, viral, predict"
                )

            # 根據分析類型調用相應方法
            if analysis_type == "trend":
                return self.get_topic_trend_analysis(
                    topic=topic,
                    date_range=date_range,
                    granularity=granularity
                )
            elif analysis_type == "lifecycle":
                return self.analyze_topic_lifecycle(
                    topic=topic,
                    date_range=date_range
                )
            elif analysis_type == "viral":
                # viral模式不需要topic參數，使用通用檢測
                return self.detect_viral_topics(
                    threshold=threshold,
                    time_window=time_window
                )
            else:  # predict
                # predict模式不需要topic參數，使用通用預測
                return self.predict_trending_topics(
                    lookahead_hours=lookahead_hours,
                    confidence_threshold=confidence_threshold
                )

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

    def get_topic_trend_analysis(
        self,
        topic: str,
        date_range: Optional[Dict[str, str]] = None,
        granularity: str = "day"
    ) -> Dict:
        """
        熱度趨勢分析 - 追蹤特定話題的熱度變化趨勢

        Args:
            topic: 話題關鍵詞
            date_range: 日期範圍（可選）
                       - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **默認**: 不指定時默認分析最近7天
            granularity: 時間粒度，僅支持 day（天）

        Returns:
            趨勢分析結果字典

        Examples:
            用戶詢問示例：
            - "幫我分析一下'人工智能'這個話題最近一週的熱度趨勢"
            - "查看'比特幣'過去一週的熱度變化"
            - "看看'iPhone'最近7天的趨勢如何"
            - "分析'特斯拉'最近一個月的熱度趨勢"
            - "查看'ChatGPT'2024年12月的趨勢變化"

            代碼調用示例：
            >>> tools = AnalyticsTools()
            >>> # 分析7天趨勢（假設今天是 2025-11-17）
            >>> result = tools.get_topic_trend_analysis(
            ...     topic="人工智能",
            ...     date_range={"start": "2025-11-11", "end": "2025-11-17"},
            ...     granularity="day"
            ... )
            >>> # 分析歷史月份趨勢
            >>> result = tools.get_topic_trend_analysis(
            ...     topic="特斯拉",
            ...     date_range={"start": "2024-12-01", "end": "2024-12-31"},
            ...     granularity="day"
            ... )
            >>> print(result['trend_data'])
        """
        try:
            # 驗證參數
            topic = validate_keyword(topic)

            # 驗證粒度參數（只支持day）
            if granularity != "day":
                from ..utils.errors import InvalidParameterError
                raise InvalidParameterError(
                    f"不支持的粒度參數: {granularity}",
                    suggestion="當前僅支持 'day' 粒度，因爲底層數據按天聚合"
                )

            # 處理日期範圍（不指定時默認最近7天）
            if date_range:
                from ..utils.validators import validate_date_range
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # 默認最近7天
                end_date = datetime.now()
                start_date = end_date - timedelta(days=6)

            # 收集趨勢數據
            trend_data = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    # 統計該時間點的話題出現次數
                    count = 0
                    matched_titles = []

                    for _, titles in all_titles.items():
                        for title in titles.keys():
                            if topic.lower() in title.lower():
                                count += 1
                                matched_titles.append(title)

                    trend_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": count,
                        "sample_titles": matched_titles[:3]  # 只保留前3個樣本
                    })

                except DataNotFoundError:
                    trend_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": 0,
                        "sample_titles": []
                    })

                # 按天增加時間
                current_date += timedelta(days=1)

            # 計算趨勢指標
            counts = [item["count"] for item in trend_data]
            total_days = (end_date - start_date).days + 1

            if len(counts) >= 2:
                # 計算漲跌幅度
                first_non_zero = next((c for c in counts if c > 0), 0)
                last_count = counts[-1]

                if first_non_zero > 0:
                    change_rate = ((last_count - first_non_zero) / first_non_zero) * 100
                else:
                    change_rate = 0

                # 找到峯值時間
                max_count = max(counts)
                peak_index = counts.index(max_count)
                peak_time = trend_data[peak_index]["date"]
            else:
                change_rate = 0
                peak_time = None
                max_count = 0

            return {
                "success": True,
                "topic": topic,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                    "total_days": total_days
                },
                "granularity": granularity,
                "trend_data": trend_data,
                "statistics": {
                    "total_mentions": sum(counts),
                    "average_mentions": round(sum(counts) / len(counts), 2) if counts else 0,
                    "peak_count": max_count,
                    "peak_time": peak_time,
                    "change_rate": round(change_rate, 2)
                },
                "trend_direction": "上升" if change_rate > 10 else "下降" if change_rate < -10 else "穩定"
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

    def compare_platforms(
        self,
        topic: Optional[str] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        平臺對比分析 - 對比不同平臺對同一話題的關注度

        Args:
            topic: 話題關鍵詞（可選，不指定則對比整體活躍度）
            date_range: 日期範圍，格式: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}

        Returns:
            平臺對比分析結果

        Examples:
            用戶詢問示例：
            - "對比一下各個平臺對'人工智能'話題的關注度"
            - "看看知乎和微博哪個平臺更關注科技新聞"
            - "分析各平臺今天的熱點分佈"

            代碼調用示例：
            >>> # 對比各平臺（假設今天是 2025-11-17）
            >>> result = tools.compare_platforms(
            ...     topic="人工智能",
            ...     date_range={"start": "2025-11-08", "end": "2025-11-17"}
            ... )
            >>> print(result['platform_stats'])
        """
        try:
            # 參數驗證
            if topic:
                topic = validate_keyword(topic)
            date_range_tuple = validate_date_range(date_range)

            # 確定日期範圍
            if date_range_tuple:
                start_date, end_date = date_range_tuple
            else:
                start_date = end_date = datetime.now()

            # 收集各平臺數據
            platform_stats = defaultdict(lambda: {
                "total_news": 0,
                "topic_mentions": 0,
                "unique_titles": set(),
                "top_keywords": Counter()
            })

            # 遍歷日期範圍
            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)

                        for title in titles.keys():
                            platform_stats[platform_name]["total_news"] += 1
                            platform_stats[platform_name]["unique_titles"].add(title)

                            # 如果指定了話題，統計包含話題的新聞
                            if topic and topic.lower() in title.lower():
                                platform_stats[platform_name]["topic_mentions"] += 1

                            # 提取關鍵詞（簡單分詞）
                            keywords = self._extract_keywords(title)
                            platform_stats[platform_name]["top_keywords"].update(keywords)

                except DataNotFoundError:
                    pass

                current_date += timedelta(days=1)

            # 轉換爲可序列化的格式
            result_stats = {}
            for platform, stats in platform_stats.items():
                coverage_rate = 0
                if stats["total_news"] > 0:
                    coverage_rate = (stats["topic_mentions"] / stats["total_news"]) * 100

                result_stats[platform] = {
                    "total_news": stats["total_news"],
                    "topic_mentions": stats["topic_mentions"],
                    "unique_titles": len(stats["unique_titles"]),
                    "coverage_rate": round(coverage_rate, 2),
                    "top_keywords": [
                        {"keyword": k, "count": v}
                        for k, v in stats["top_keywords"].most_common(5)
                    ]
                }

            # 找出各平臺獨有的熱點
            unique_topics = self._find_unique_topics(platform_stats)

            return {
                "success": True,
                "topic": topic,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "platform_stats": result_stats,
                "unique_topics": unique_topics,
                "total_platforms": len(result_stats)
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

    def analyze_keyword_cooccurrence(
        self,
        min_frequency: int = 3,
        top_n: int = 20
    ) -> Dict:
        """
        關鍵詞共現分析 - 分析哪些關鍵詞經常同時出現

        Args:
            min_frequency: 最小共現頻次
            top_n: 返回TOP N關鍵詞對

        Returns:
            關鍵詞共現分析結果

        Examples:
            用戶詢問示例：
            - "分析一下哪些關鍵詞經常一起出現"
            - "看看'人工智能'經常和哪些詞一起出現"
            - "找出今天新聞中的關鍵詞關聯"

            代碼調用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.analyze_keyword_cooccurrence(
            ...     min_frequency=5,
            ...     top_n=15
            ... )
            >>> print(result['cooccurrence_pairs'])
        """
        try:
            # 參數驗證
            min_frequency = validate_limit(min_frequency, default=3, max_limit=100)
            top_n = validate_top_n(top_n, default=20)

            # 讀取今天的數據
            all_titles, _, _ = self.data_service.parser.read_all_titles_for_date()

            # 關鍵詞共現統計
            cooccurrence = Counter()
            keyword_titles = defaultdict(list)

            for platform_id, titles in all_titles.items():
                for title in titles.keys():
                    # 提取關鍵詞
                    keywords = self._extract_keywords(title)

                    # 記錄每個關鍵詞出現的標題
                    for kw in keywords:
                        keyword_titles[kw].append(title)

                    # 計算兩兩共現
                    if len(keywords) >= 2:
                        for i, kw1 in enumerate(keywords):
                            for kw2 in keywords[i+1:]:
                                # 統一排序，避免重複
                                pair = tuple(sorted([kw1, kw2]))
                                cooccurrence[pair] += 1

            # 過濾低頻共現
            filtered_pairs = [
                (pair, count) for pair, count in cooccurrence.items()
                if count >= min_frequency
            ]

            # 排序並取TOP N
            top_pairs = sorted(filtered_pairs, key=lambda x: x[1], reverse=True)[:top_n]

            # 構建結果
            result_pairs = []
            for (kw1, kw2), count in top_pairs:
                # 找出同時包含兩個關鍵詞的標題樣本
                titles_with_both = [
                    title for title in keyword_titles[kw1]
                    if kw2 in self._extract_keywords(title)
                ]

                result_pairs.append({
                    "keyword1": kw1,
                    "keyword2": kw2,
                    "cooccurrence_count": count,
                    "sample_titles": titles_with_both[:3]
                })

            return {
                "success": True,
                "cooccurrence_pairs": result_pairs,
                "total_pairs": len(result_pairs),
                "min_frequency": min_frequency,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

    def analyze_sentiment(
        self,
        topic: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None,
        limit: int = 50,
        sort_by_weight: bool = True,
        include_url: bool = False
    ) -> Dict:
        """
        情感傾向分析 - 生成用於 AI 情感分析的結構化提示詞

        本工具收集新聞數據並生成優化的 AI 提示詞，你可以將其發送給 AI 進行深度情感分析。

        Args:
            topic: 話題關鍵詞（可選），只分析包含該關鍵詞的新聞
            platforms: 平臺過濾列表（可選），如 ['zhihu', 'weibo']
            date_range: 日期範圍（可選），格式: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       不指定則默認查詢今天的數據
            limit: 返回新聞數量限制，默認50，最大100
            sort_by_weight: 是否按權重排序，默認True（推薦）
            include_url: 是否包含URL鏈接，默認False（節省token）

        Returns:
            包含 AI 提示詞和新聞數據的結構化結果

        Examples:
            用戶詢問示例：
            - "分析一下今天新聞的情感傾向"
            - "看看'特斯拉'相關新聞是正面還是負面的"
            - "分析各平臺對'人工智能'的情感態度"
            - "看看'特斯拉'相關新聞是正面還是負面的，請選擇一週內的前10條新聞來分析"

            代碼調用示例：
            >>> tools = AnalyticsTools()
            >>> # 分析今天的特斯拉新聞，返回前10條
            >>> result = tools.analyze_sentiment(
            ...     topic="特斯拉",
            ...     limit=10
            ... )
            >>> # 分析一週內的特斯拉新聞（假設今天是 2025-11-17）
            >>> result = tools.analyze_sentiment(
            ...     topic="特斯拉",
            ...     date_range={"start": "2025-11-11", "end": "2025-11-17"},
            ...     limit=10
            ... )
            >>> print(result['ai_prompt'])  # 獲取生成的提示詞
        """
        try:
            # 參數驗證
            if topic:
                topic = validate_keyword(topic)
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # 處理日期範圍
            if date_range:
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # 默認今天
                start_date = end_date = datetime.now()

            # 收集新聞數據（支持多天）
            all_news_items = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date,
                        platform_ids=platforms
                    )

                    # 收集該日期的新聞
                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)
                        for title, info in titles.items():
                            # 如果指定了話題，只收集包含話題的標題
                            if topic and topic.lower() not in title.lower():
                                continue

                            news_item = {
                                "platform": platform_name,
                                "title": title,
                                "ranks": info.get("ranks", []),
                                "count": len(info.get("ranks", [])),
                                "date": current_date.strftime("%Y-%m-%d")
                            }

                            # 條件性添加 URL 字段
                            if include_url:
                                news_item["url"] = info.get("url", "")
                                news_item["mobileUrl"] = info.get("mobileUrl", "")

                            all_news_items.append(news_item)

                except DataNotFoundError:
                    # 該日期沒有數據，繼續下一天
                    pass

                # 下一天
                current_date += timedelta(days=1)

            if not all_news_items:
                time_desc = "今天" if start_date == end_date else f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
                raise DataNotFoundError(
                    f"未找到相關新聞（{time_desc}）",
                    suggestion="請嘗試其他話題、日期範圍或平臺"
                )

            # 去重（同一標題只保留一次）
            unique_news = {}
            for item in all_news_items:
                key = f"{item['platform']}::{item['title']}"
                if key not in unique_news:
                    unique_news[key] = item
                else:
                    # 合併 ranks（如果同一新聞在多天出現）
                    existing = unique_news[key]
                    existing["ranks"].extend(item["ranks"])
                    existing["count"] = len(existing["ranks"])

            deduplicated_news = list(unique_news.values())

            # 按權重排序（如果啓用）
            if sort_by_weight:
                deduplicated_news.sort(
                    key=lambda x: calculate_news_weight(x),
                    reverse=True
                )

            # 限制返回數量
            selected_news = deduplicated_news[:limit]

            # 生成 AI 提示詞
            ai_prompt = self._create_sentiment_analysis_prompt(
                news_data=selected_news,
                topic=topic
            )

            # 構建時間範圍描述
            if start_date == end_date:
                time_range_desc = start_date.strftime("%Y-%m-%d")
            else:
                time_range_desc = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"

            result = {
                "success": True,
                "method": "ai_prompt_generation",
                "summary": {
                    "total_found": len(deduplicated_news),
                    "returned_count": len(selected_news),
                    "requested_limit": limit,
                    "duplicates_removed": len(all_news_items) - len(deduplicated_news),
                    "topic": topic,
                    "time_range": time_range_desc,
                    "platforms": list(set(item["platform"] for item in selected_news)),
                    "sorted_by_weight": sort_by_weight
                },
                "ai_prompt": ai_prompt,
                "news_sample": selected_news,
                "usage_note": "請將 ai_prompt 字段的內容發送給 AI 進行情感分析"
            }

            # 如果返回數量少於請求數量，增加提示
            if len(selected_news) < limit and len(deduplicated_news) >= limit:
                result["note"] = "返回數量少於請求數量是因爲去重邏輯（同一標題在不同平臺只保留一次）"
            elif len(deduplicated_news) < limit:
                result["note"] = f"在指定時間範圍內僅找到 {len(deduplicated_news)} 條匹配的新聞"

            return result

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

    def _create_sentiment_analysis_prompt(
        self,
        news_data: List[Dict],
        topic: Optional[str]
    ) -> str:
        """
        創建情感分析的 AI 提示詞

        Args:
            news_data: 新聞數據列表（已排序和限制數量）
            topic: 話題關鍵詞

        Returns:
            格式化的 AI 提示詞
        """
        # 按平臺分組
        platform_news = defaultdict(list)
        for item in news_data:
            platform_news[item["platform"]].append({
                "title": item["title"],
                "date": item.get("date", "")
            })

        # 構建提示詞
        prompt_parts = []

        # 1. 任務說明
        if topic:
            prompt_parts.append(f"請分析以下關於「{topic}」的新聞標題的情感傾向。")
        else:
            prompt_parts.append("請分析以下新聞標題的情感傾向。")

        prompt_parts.append("")
        prompt_parts.append("分析要求：")
        prompt_parts.append("1. 識別每條新聞的情感傾向（正面/負面/中性）")
        prompt_parts.append("2. 統計各情感類別的數量和百分比")
        prompt_parts.append("3. 分析不同平臺的情感差異")
        prompt_parts.append("4. 總結整體情感趨勢")
        prompt_parts.append("5. 列舉典型的正面和負面新聞樣本")
        prompt_parts.append("")

        # 2. 數據概覽
        prompt_parts.append(f"數據概覽：")
        prompt_parts.append(f"- 總新聞數：{len(news_data)}")
        prompt_parts.append(f"- 覆蓋平臺：{len(platform_news)}")

        # 時間範圍
        dates = set(item.get("date", "") for item in news_data if item.get("date"))
        if dates:
            date_list = sorted(dates)
            if len(date_list) == 1:
                prompt_parts.append(f"- 時間範圍：{date_list[0]}")
            else:
                prompt_parts.append(f"- 時間範圍：{date_list[0]} 至 {date_list[-1]}")

        prompt_parts.append("")

        # 3. 按平臺展示新聞
        prompt_parts.append("新聞列表（按平臺分類，已按重要性排序）：")
        prompt_parts.append("")

        for platform, items in sorted(platform_news.items()):
            prompt_parts.append(f"【{platform}】({len(items)} 條)")
            for i, item in enumerate(items, 1):
                title = item["title"]
                date_str = f" [{item['date']}]" if item.get("date") else ""
                prompt_parts.append(f"{i}. {title}{date_str}")
            prompt_parts.append("")

        # 4. 輸出格式說明
        prompt_parts.append("請按以下格式輸出分析結果：")
        prompt_parts.append("")
        prompt_parts.append("## 情感分佈統計")
        prompt_parts.append("- 正面：XX條 (XX%)")
        prompt_parts.append("- 負面：XX條 (XX%)")
        prompt_parts.append("- 中性：XX條 (XX%)")
        prompt_parts.append("")
        prompt_parts.append("## 平臺情感對比")
        prompt_parts.append("[各平臺的情感傾向差異]")
        prompt_parts.append("")
        prompt_parts.append("## 整體情感趨勢")
        prompt_parts.append("[總體分析和關鍵發現]")
        prompt_parts.append("")
        prompt_parts.append("## 典型樣本")
        prompt_parts.append("正面新聞樣本：")
        prompt_parts.append("[列舉3-5條]")
        prompt_parts.append("")
        prompt_parts.append("負面新聞樣本：")
        prompt_parts.append("[列舉3-5條]")

        return "\n".join(prompt_parts)

    def find_similar_news(
        self,
        reference_title: str,
        threshold: float = 0.6,
        limit: int = 50,
        include_url: bool = False
    ) -> Dict:
        """
        相似新聞查找 - 基於標題相似度查找相關新聞

        Args:
            reference_title: 參考標題
            threshold: 相似度閾值（0-1之間）
            limit: 返回條數限制，默認50
            include_url: 是否包含URL鏈接，默認False（節省token）

        Returns:
            相似新聞列表

        Examples:
            用戶詢問示例：
            - "找出和'特斯拉降價'相似的新聞"
            - "查找關於iPhone發佈的類似報道"
            - "看看有沒有和這條新聞相似的報道"

            代碼調用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.find_similar_news(
            ...     reference_title="特斯拉宣佈降價",
            ...     threshold=0.6,
            ...     limit=10
            ... )
            >>> print(result['similar_news'])
        """
        try:
            # 參數驗證
            reference_title = validate_keyword(reference_title)

            if not 0 <= threshold <= 1:
                raise InvalidParameterError(
                    "threshold 必須在 0 到 1 之間",
                    suggestion="推薦值：0.5-0.8"
                )

            limit = validate_limit(limit, default=50)

            # 讀取數據
            all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date()

            # 計算相似度
            similar_items = []

            for platform_id, titles in all_titles.items():
                platform_name = id_to_name.get(platform_id, platform_id)

                for title, info in titles.items():
                    if title == reference_title:
                        continue

                    # 計算相似度
                    similarity = self._calculate_similarity(reference_title, title)

                    if similarity >= threshold:
                        news_item = {
                            "title": title,
                            "platform": platform_id,
                            "platform_name": platform_name,
                            "similarity": round(similarity, 3),
                            "rank": info["ranks"][0] if info["ranks"] else 0
                        }

                        # 條件性添加 URL 字段
                        if include_url:
                            news_item["url"] = info.get("url", "")

                        similar_items.append(news_item)

            # 按相似度排序
            similar_items.sort(key=lambda x: x["similarity"], reverse=True)

            # 限制數量
            result_items = similar_items[:limit]

            if not result_items:
                raise DataNotFoundError(
                    f"未找到相似度超過 {threshold} 的新聞",
                    suggestion="請降低相似度閾值或嘗試其他標題"
                )

            result = {
                "success": True,
                "summary": {
                    "total_found": len(similar_items),
                    "returned_count": len(result_items),
                    "requested_limit": limit,
                    "threshold": threshold,
                    "reference_title": reference_title
                },
                "similar_news": result_items
            }

            if len(similar_items) < limit:
                result["note"] = f"相似度閾值 {threshold} 下僅找到 {len(similar_items)} 條相似新聞"

            return result

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

    def search_by_entity(
        self,
        entity: str,
        entity_type: Optional[str] = None,
        limit: int = 50,
        sort_by_weight: bool = True
    ) -> Dict:
        """
        實體識別搜索 - 搜索包含特定人物/地點/機構的新聞

        Args:
            entity: 實體名稱
            entity_type: 實體類型（person/location/organization），可選
            limit: 返回條數限制，默認50，最大200
            sort_by_weight: 是否按權重排序，默認True

        Returns:
            實體相關新聞列表

        Examples:
            用戶詢問示例：
            - "搜索馬斯克相關的新聞"
            - "查找關於特斯拉公司的報道，返回前20條"
            - "看看北京有什麼新聞"

            代碼調用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.search_by_entity(
            ...     entity="馬斯克",
            ...     entity_type="person",
            ...     limit=20
            ... )
            >>> print(result['related_news'])
        """
        try:
            # 參數驗證
            entity = validate_keyword(entity)
            limit = validate_limit(limit, default=50)

            if entity_type and entity_type not in ["person", "location", "organization"]:
                raise InvalidParameterError(
                    f"無效的實體類型: {entity_type}",
                    suggestion="支持的類型: person, location, organization"
                )

            # 讀取數據
            all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date()

            # 搜索包含實體的新聞
            related_news = []
            entity_context = Counter()  # 統計實體周邊的詞

            for platform_id, titles in all_titles.items():
                platform_name = id_to_name.get(platform_id, platform_id)

                for title, info in titles.items():
                    if entity in title:
                        url = info.get("url", "")
                        mobile_url = info.get("mobileUrl", "")
                        ranks = info.get("ranks", [])
                        count = len(ranks)

                        related_news.append({
                            "title": title,
                            "platform": platform_id,
                            "platform_name": platform_name,
                            "url": url,
                            "mobileUrl": mobile_url,
                            "ranks": ranks,
                            "count": count,
                            "rank": ranks[0] if ranks else 999
                        })

                        # 提取實體周邊的關鍵詞
                        keywords = self._extract_keywords(title)
                        entity_context.update(keywords)

            if not related_news:
                raise DataNotFoundError(
                    f"未找到包含實體 '{entity}' 的新聞",
                    suggestion="請嘗試其他實體名稱"
                )

            # 移除實體本身
            if entity in entity_context:
                del entity_context[entity]

            # 按權重排序（如果啓用）
            if sort_by_weight:
                related_news.sort(
                    key=lambda x: calculate_news_weight(x),
                    reverse=True
                )
            else:
                # 按排名排序
                related_news.sort(key=lambda x: x["rank"])

            # 限制返回數量
            result_news = related_news[:limit]

            return {
                "success": True,
                "entity": entity,
                "entity_type": entity_type or "auto",
                "related_news": result_news,
                "total_found": len(related_news),
                "returned_count": len(result_news),
                "sorted_by_weight": sort_by_weight,
                "related_keywords": [
                    {"keyword": k, "count": v}
                    for k, v in entity_context.most_common(10)
                ]
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

    def generate_summary_report(
        self,
        report_type: str = "daily",
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        每日/每週摘要生成器 - 自動生成熱點摘要報告

        Args:
            report_type: 報告類型（daily/weekly）
            date_range: 自定義日期範圍（可選）

        Returns:
            Markdown格式的摘要報告

        Examples:
            用戶詢問示例：
            - "生成今天的新聞摘要報告"
            - "給我一份本週的熱點總結"
            - "生成過去7天的新聞分析報告"

            代碼調用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.generate_summary_report(
            ...     report_type="daily"
            ... )
            >>> print(result['markdown_report'])
        """
        try:
            # 參數驗證
            if report_type not in ["daily", "weekly"]:
                raise InvalidParameterError(
                    f"無效的報告類型: {report_type}",
                    suggestion="支持的類型: daily, weekly"
                )

            # 確定日期範圍
            if date_range:
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                if report_type == "daily":
                    start_date = end_date = datetime.now()
                else:  # weekly
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=6)

            # 收集數據
            all_keywords = Counter()
            all_platforms_news = defaultdict(int)
            all_titles_list = []

            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)
                        all_platforms_news[platform_name] += len(titles)

                        for title in titles.keys():
                            all_titles_list.append({
                                "title": title,
                                "platform": platform_name,
                                "date": current_date.strftime("%Y-%m-%d")
                            })

                            # 提取關鍵詞
                            keywords = self._extract_keywords(title)
                            all_keywords.update(keywords)

                except DataNotFoundError:
                    pass

                current_date += timedelta(days=1)

            # 生成報告
            report_title = f"{'每日' if report_type == 'daily' else '每週'}新聞熱點摘要"
            date_str = f"{start_date.strftime('%Y-%m-%d')}" if report_type == "daily" else f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"

            # 構建Markdown報告
            markdown = f"""# {report_title}

**報告日期**: {date_str}
**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 數據概覽

- **總新聞數**: {len(all_titles_list)}
- **覆蓋平臺**: {len(all_platforms_news)}
- **熱門關鍵詞數**: {len(all_keywords)}

## 🔥 TOP 10 熱門話題

"""

            # 添加TOP 10關鍵詞
            for i, (keyword, count) in enumerate(all_keywords.most_common(10), 1):
                markdown += f"{i}. **{keyword}** - 出現 {count} 次\n"

            # 平臺分析
            markdown += "\n## 📱 平臺活躍度\n\n"
            sorted_platforms = sorted(all_platforms_news.items(), key=lambda x: x[1], reverse=True)

            for platform, count in sorted_platforms:
                markdown += f"- **{platform}**: {count} 條新聞\n"

            # 趨勢變化（如果是週報）
            if report_type == "weekly":
                markdown += "\n## 📈 趨勢分析\n\n"
                markdown += "本週熱度持續的話題（樣本數據）：\n\n"

                # 簡單的趨勢分析
                top_keywords = [kw for kw, _ in all_keywords.most_common(5)]
                for keyword in top_keywords:
                    markdown += f"- **{keyword}**: 持續熱門\n"

            # 添加樣本新聞（按權重選擇，確保確定性）
            markdown += "\n## 📰 精選新聞樣本\n\n"

            # 確定性選取：按標題的權重排序，取前5條
            # 這樣相同輸入總是返回相同結果
            if all_titles_list:
                # 計算每條新聞的權重分數（基於關鍵詞出現次數）
                news_with_scores = []
                for news in all_titles_list:
                    # 簡單權重：統計包含TOP關鍵詞的次數
                    score = 0
                    title_lower = news['title'].lower()
                    for keyword, count in all_keywords.most_common(10):
                        if keyword.lower() in title_lower:
                            score += count
                    news_with_scores.append((news, score))

                # 按權重降序排序，權重相同則按標題字母順序（確保確定性）
                news_with_scores.sort(key=lambda x: (-x[1], x[0]['title']))

                # 取前5條
                sample_news = [item[0] for item in news_with_scores[:5]]

                for news in sample_news:
                    markdown += f"- [{news['platform']}] {news['title']}\n"

            markdown += "\n---\n\n*本報告由 TrendRadar MCP 自動生成*\n"

            return {
                "success": True,
                "report_type": report_type,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "markdown_report": markdown,
                "statistics": {
                    "total_news": len(all_titles_list),
                    "platforms_count": len(all_platforms_news),
                    "keywords_count": len(all_keywords),
                    "top_keyword": all_keywords.most_common(1)[0] if all_keywords else None
                }
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

    def get_platform_activity_stats(
        self,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        平臺活躍度統計 - 統計各平臺的發佈頻率和活躍時間段

        Args:
            date_range: 日期範圍（可選）

        Returns:
            平臺活躍度統計結果

        Examples:
            用戶詢問示例：
            - "統計各平臺今天的活躍度"
            - "看看哪個平臺更新最頻繁"
            - "分析各平臺的發佈時間規律"

            代碼調用示例：
            >>> # 查看各平臺活躍度（假設今天是 2025-11-17）
            >>> result = tools.get_platform_activity_stats(
            ...     date_range={"start": "2025-11-08", "end": "2025-11-17"}
            ... )
            >>> print(result['platform_activity'])
        """
        try:
            # 參數驗證
            date_range_tuple = validate_date_range(date_range)

            # 確定日期範圍
            if date_range_tuple:
                start_date, end_date = date_range_tuple
            else:
                start_date = end_date = datetime.now()

            # 統計各平臺活躍度
            platform_activity = defaultdict(lambda: {
                "total_updates": 0,
                "days_active": set(),
                "news_count": 0,
                "hourly_distribution": Counter()
            })

            # 遍歷日期範圍
            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, id_to_name, timestamps = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)

                        platform_activity[platform_name]["news_count"] += len(titles)
                        platform_activity[platform_name]["days_active"].add(current_date.strftime("%Y-%m-%d"))

                        # 統計更新次數（基於文件數量）
                        platform_activity[platform_name]["total_updates"] += len(timestamps)

                        # 統計時間分佈（基於文件名中的時間）
                        for filename in timestamps.keys():
                            # 解析文件名中的小時（格式：HHMM.txt）
                            match = re.match(r'(\d{2})(\d{2})\.txt', filename)
                            if match:
                                hour = int(match.group(1))
                                platform_activity[platform_name]["hourly_distribution"][hour] += 1

                except DataNotFoundError:
                    pass

                current_date += timedelta(days=1)

            # 轉換爲可序列化的格式
            result_activity = {}
            for platform, stats in platform_activity.items():
                days_count = len(stats["days_active"])
                avg_news_per_day = stats["news_count"] / days_count if days_count > 0 else 0

                # 找出最活躍的時間段
                most_active_hours = stats["hourly_distribution"].most_common(3)

                result_activity[platform] = {
                    "total_updates": stats["total_updates"],
                    "news_count": stats["news_count"],
                    "days_active": days_count,
                    "avg_news_per_day": round(avg_news_per_day, 2),
                    "most_active_hours": [
                        {"hour": f"{hour:02d}:00", "count": count}
                        for hour, count in most_active_hours
                    ],
                    "activity_score": round(stats["news_count"] / max(days_count, 1), 2)
                }

            # 按活躍度排序
            sorted_platforms = sorted(
                result_activity.items(),
                key=lambda x: x[1]["activity_score"],
                reverse=True
            )

            return {
                "success": True,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "platform_activity": dict(sorted_platforms),
                "most_active_platform": sorted_platforms[0][0] if sorted_platforms else None,
                "total_platforms": len(result_activity)
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

    def analyze_topic_lifecycle(
        self,
        topic: str,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        話題生命週期分析 - 追蹤話題從出現到消失的完整週期

        Args:
            topic: 話題關鍵詞
            date_range: 日期範圍（可選）
                       - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **默認**: 不指定時默認分析最近7天

        Returns:
            話題生命週期分析結果

        Examples:
            用戶詢問示例：
            - "分析'人工智能'這個話題的生命週期"
            - "看看'iPhone'話題是曇花一現還是持續熱點"
            - "追蹤'比特幣'話題的熱度變化"

            代碼調用示例：
            >>> # 分析話題生命週期（假設今天是 2025-11-17）
            >>> result = tools.analyze_topic_lifecycle(
            ...     topic="人工智能",
            ...     date_range={"start": "2025-10-19", "end": "2025-11-17"}
            ... )
            >>> print(result['lifecycle_stage'])
        """
        try:
            # 參數驗證
            topic = validate_keyword(topic)

            # 處理日期範圍（不指定時默認最近7天）
            if date_range:
                from ..utils.validators import validate_date_range
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # 默認最近7天
                end_date = datetime.now()
                start_date = end_date - timedelta(days=6)

            # 收集話題歷史數據
            lifecycle_data = []
            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    # 統計該日的話題出現次數
                    count = 0
                    for _, titles in all_titles.items():
                        for title in titles.keys():
                            if topic.lower() in title.lower():
                                count += 1

                    lifecycle_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": count
                    })

                except DataNotFoundError:
                    lifecycle_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": 0
                    })

                current_date += timedelta(days=1)

            # 計算分析天數
            total_days = (end_date - start_date).days + 1

            # 分析生命週期階段
            counts = [item["count"] for item in lifecycle_data]

            if not any(counts):
                time_desc = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
                raise DataNotFoundError(
                    f"在 {time_desc} 內未找到話題 '{topic}'",
                    suggestion="請嘗試其他話題或擴大時間範圍"
                )

            # 找到首次出現和最後出現
            first_appearance = next((item["date"] for item in lifecycle_data if item["count"] > 0), None)
            last_appearance = next((item["date"] for item in reversed(lifecycle_data) if item["count"] > 0), None)

            # 計算峯值
            max_count = max(counts)
            peak_index = counts.index(max_count)
            peak_date = lifecycle_data[peak_index]["date"]

            # 計算平均值和標準差（簡單實現）
            non_zero_counts = [c for c in counts if c > 0]
            avg_count = sum(non_zero_counts) / len(non_zero_counts) if non_zero_counts else 0

            # 判斷生命週期階段
            recent_counts = counts[-3:]  # 最近3天
            early_counts = counts[:3]    # 前3天

            if sum(recent_counts) > sum(early_counts):
                lifecycle_stage = "上升期"
            elif sum(recent_counts) < sum(early_counts) * 0.5:
                lifecycle_stage = "衰退期"
            elif max_count in recent_counts:
                lifecycle_stage = "爆發期"
            else:
                lifecycle_stage = "穩定期"

            # 分類：曇花一現 vs 持續熱點
            active_days = sum(1 for c in counts if c > 0)

            if active_days <= 2 and max_count > avg_count * 2:
                topic_type = "曇花一現"
            elif active_days >= total_days * 0.6:
                topic_type = "持續熱點"
            else:
                topic_type = "週期性熱點"

            return {
                "success": True,
                "topic": topic,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                    "total_days": total_days
                },
                "lifecycle_data": lifecycle_data,
                "analysis": {
                    "first_appearance": first_appearance,
                    "last_appearance": last_appearance,
                    "peak_date": peak_date,
                    "peak_count": max_count,
                    "active_days": active_days,
                    "avg_daily_mentions": round(avg_count, 2),
                    "lifecycle_stage": lifecycle_stage,
                    "topic_type": topic_type
                }
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

    def detect_viral_topics(
        self,
        threshold: float = 3.0,
        time_window: int = 24
    ) -> Dict:
        """
        異常熱度檢測 - 自動識別突然爆火的話題

        Args:
            threshold: 熱度突增倍數閾值
            time_window: 檢測時間窗口（小時）

        Returns:
            爆火話題列表

        Examples:
            用戶詢問示例：
            - "檢測今天有哪些突然爆火的話題"
            - "看看有沒有熱度異常的新聞"
            - "預警可能的重大事件"

            代碼調用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.detect_viral_topics(
            ...     threshold=3.0,
            ...     time_window=24
            ... )
            >>> print(result['viral_topics'])
        """
        try:
            # 參數驗證
            if threshold < 1.0:
                raise InvalidParameterError(
                    "threshold 必須大於等於 1.0",
                    suggestion="推薦值：2.0-5.0"
                )

            time_window = validate_limit(time_window, default=24, max_limit=72)

            # 讀取當前和之前的數據
            current_all_titles, _, _ = self.data_service.parser.read_all_titles_for_date()

            # 讀取昨天的數據作爲基準
            yesterday = datetime.now() - timedelta(days=1)
            try:
                previous_all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                    date=yesterday
                )
            except DataNotFoundError:
                previous_all_titles = {}

            # 統計當前的關鍵詞頻率
            current_keywords = Counter()
            current_keyword_titles = defaultdict(list)

            for _, titles in current_all_titles.items():
                for title in titles.keys():
                    keywords = self._extract_keywords(title)
                    current_keywords.update(keywords)

                    for kw in keywords:
                        current_keyword_titles[kw].append(title)

            # 統計之前的關鍵詞頻率
            previous_keywords = Counter()

            for _, titles in previous_all_titles.items():
                for title in titles.keys():
                    keywords = self._extract_keywords(title)
                    previous_keywords.update(keywords)

            # 檢測異常熱度
            viral_topics = []

            for keyword, current_count in current_keywords.items():
                previous_count = previous_keywords.get(keyword, 0)

                # 計算增長倍數
                if previous_count == 0:
                    # 新出現的話題
                    if current_count >= 5:  # 至少出現5次才認爲是爆火
                        growth_rate = float('inf')
                        is_viral = True
                    else:
                        continue
                else:
                    growth_rate = current_count / previous_count
                    is_viral = growth_rate >= threshold

                if is_viral:
                    viral_topics.append({
                        "keyword": keyword,
                        "current_count": current_count,
                        "previous_count": previous_count,
                        "growth_rate": round(growth_rate, 2) if growth_rate != float('inf') else "新話題",
                        "sample_titles": current_keyword_titles[keyword][:3],
                        "alert_level": "高" if growth_rate > threshold * 2 else "中"
                    })

            # 按增長率排序
            viral_topics.sort(
                key=lambda x: x["current_count"] if x["growth_rate"] == "新話題" else x["growth_rate"],
                reverse=True
            )

            if not viral_topics:
                return {
                    "success": True,
                    "viral_topics": [],
                    "total_detected": 0,
                    "message": f"未檢測到熱度增長超過 {threshold} 倍的話題"
                }

            return {
                "success": True,
                "viral_topics": viral_topics,
                "total_detected": len(viral_topics),
                "threshold": threshold,
                "time_window": time_window,
                "detection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

    def predict_trending_topics(
        self,
        lookahead_hours: int = 6,
        confidence_threshold: float = 0.7
    ) -> Dict:
        """
        話題預測 - 基於歷史數據預測未來可能的熱點

        Args:
            lookahead_hours: 預測未來多少小時
            confidence_threshold: 置信度閾值

        Returns:
            預測的潛力話題列表

        Examples:
            用戶詢問示例：
            - "預測接下來6小時可能的熱點話題"
            - "有哪些話題可能會火起來"
            - "早期發現潛力話題"

            代碼調用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.predict_trending_topics(
            ...     lookahead_hours=6,
            ...     confidence_threshold=0.7
            ... )
            >>> print(result['predicted_topics'])
        """
        try:
            # 參數驗證
            lookahead_hours = validate_limit(lookahead_hours, default=6, max_limit=48)

            if not 0 <= confidence_threshold <= 1:
                raise InvalidParameterError(
                    "confidence_threshold 必須在 0 到 1 之間",
                    suggestion="推薦值：0.6-0.8"
                )

            # 收集最近3天的數據用於預測
            keyword_trends = defaultdict(list)

            for days_ago in range(3, 0, -1):
                date = datetime.now() - timedelta(days=days_ago)

                try:
                    all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                        date=date
                    )

                    # 統計關鍵詞
                    keywords_count = Counter()
                    for _, titles in all_titles.items():
                        for title in titles.keys():
                            keywords = self._extract_keywords(title)
                            keywords_count.update(keywords)

                    # 記錄每個關鍵詞的歷史數據
                    for keyword, count in keywords_count.items():
                        keyword_trends[keyword].append(count)

                except DataNotFoundError:
                    pass

            # 添加今天的數據
            try:
                all_titles, _, _ = self.data_service.parser.read_all_titles_for_date()

                keywords_count = Counter()
                keyword_titles = defaultdict(list)

                for _, titles in all_titles.items():
                    for title in titles.keys():
                        keywords = self._extract_keywords(title)
                        keywords_count.update(keywords)

                        for kw in keywords:
                            keyword_titles[kw].append(title)

                for keyword, count in keywords_count.items():
                    keyword_trends[keyword].append(count)

            except DataNotFoundError:
                raise DataNotFoundError(
                    "未找到今天的數據",
                    suggestion="請等待爬蟲任務完成"
                )

            # 預測潛力話題
            predicted_topics = []

            for keyword, trend_data in keyword_trends.items():
                if len(trend_data) < 2:
                    continue

                # 簡單的線性趨勢預測
                # 計算增長率
                recent_value = trend_data[-1]
                previous_value = trend_data[-2] if len(trend_data) >= 2 else 0

                if previous_value == 0:
                    if recent_value >= 3:
                        growth_rate = 1.0
                    else:
                        continue
                else:
                    growth_rate = (recent_value - previous_value) / previous_value

                # 判斷是否是上升趨勢
                if growth_rate > 0.3:  # 增長超過30%
                    # 計算置信度（基於趨勢的穩定性）
                    if len(trend_data) >= 3:
                        # 檢查是否連續增長
                        is_consistent = all(
                            trend_data[i] <= trend_data[i+1]
                            for i in range(len(trend_data)-1)
                        )
                        confidence = 0.9 if is_consistent else 0.7
                    else:
                        confidence = 0.6

                    if confidence >= confidence_threshold:
                        predicted_topics.append({
                            "keyword": keyword,
                            "current_count": recent_value,
                            "growth_rate": round(growth_rate * 100, 2),
                            "confidence": round(confidence, 2),
                            "trend_data": trend_data,
                            "prediction": "上升趨勢，可能成爲熱點",
                            "sample_titles": keyword_titles.get(keyword, [])[:3]
                        })

            # 按置信度和增長率排序
            predicted_topics.sort(
                key=lambda x: (x["confidence"], x["growth_rate"]),
                reverse=True
            )

            return {
                "success": True,
                "predicted_topics": predicted_topics[:20],  # 返回TOP 20
                "total_predicted": len(predicted_topics),
                "lookahead_hours": lookahead_hours,
                "confidence_threshold": confidence_threshold,
                "prediction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "note": "預測基於歷史趨勢，實際結果可能有偏差"
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

    # ==================== 輔助方法 ====================

    def _extract_keywords(self, title: str, min_length: int = 2) -> List[str]:
        """
        從標題中提取關鍵詞（簡單實現）

        Args:
            title: 標題文本
            min_length: 最小關鍵詞長度

        Returns:
            關鍵詞列表
        """
        # 移除URL和特殊字符
        title = re.sub(r'http[s]?://\S+', '', title)
        title = re.sub(r'[^\w\s]', ' ', title)

        # 簡單分詞（按空格和常見分隔符）
        words = re.split(r'[\s，。！？、]+', title)

        # 過濾停用詞和短詞
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一個', '上', '也', '很', '到', '說', '要', '去', '你', '會', '着', '沒有', '看', '好', '自己', '這'}

        keywords = [
            word.strip() for word in words
            if word.strip() and len(word.strip()) >= min_length and word.strip() not in stopwords
        ]

        return keywords

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        計算兩個文本的相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度分數（0-1之間）
        """
        # 使用 SequenceMatcher 計算相似度
        return SequenceMatcher(None, text1, text2).ratio()

    def _find_unique_topics(self, platform_stats: Dict) -> Dict[str, List[str]]:
        """
        找出各平臺獨有的熱點話題

        Args:
            platform_stats: 平臺統計數據

        Returns:
            各平臺獨有話題字典
        """
        unique_topics = {}

        # 獲取每個平臺的TOP關鍵詞
        platform_keywords = {}
        for platform, stats in platform_stats.items():
            top_keywords = set([kw for kw, _ in stats["top_keywords"].most_common(10)])
            platform_keywords[platform] = top_keywords

        # 找出獨有關鍵詞
        for platform, keywords in platform_keywords.items():
            # 找出其他平臺的所有關鍵詞
            other_keywords = set()
            for other_platform, other_kws in platform_keywords.items():
                if other_platform != platform:
                    other_keywords.update(other_kws)

            # 找出獨有的
            unique = keywords - other_keywords
            if unique:
                unique_topics[platform] = list(unique)[:5]  # 最多5個

        return unique_topics
