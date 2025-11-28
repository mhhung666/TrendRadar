"""
智能新聞檢索工具

提供模糊搜索、鏈接查詢、歷史相關新聞檢索等高級搜索功能。
"""

import re
from collections import Counter
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

from ..services.data_service import DataService
from ..utils.validators import validate_keyword, validate_limit
from ..utils.errors import MCPError, InvalidParameterError, DataNotFoundError


class SearchTools:
    """智能新聞檢索工具類"""

    def __init__(self, project_root: str = None):
        """
        初始化智能檢索工具

        Args:
            project_root: 項目根目錄
        """
        self.data_service = DataService(project_root)
        # 中文停用詞列表
        self.stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
            '一個', '上', '也', '很', '到', '說', '要', '去', '你', '會', '着', '沒有',
            '看', '好', '自己', '這', '那', '來', '被', '與', '爲', '對', '將', '從',
            '以', '及', '等', '但', '或', '而', '於', '中', '由', '可', '可以', '已',
            '已經', '還', '更', '最', '再', '因爲', '所以', '如果', '雖然', '然而'
        }

    def search_news_unified(
        self,
        query: str,
        search_mode: str = "keyword",
        date_range: Optional[Dict[str, str]] = None,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
        sort_by: str = "relevance",
        threshold: float = 0.6,
        include_url: bool = False
    ) -> Dict:
        """
        統一新聞搜索工具 - 整合多種搜索模式

        Args:
            query: 查詢內容（必需）- 關鍵詞、內容片段或實體名稱
            search_mode: 搜索模式，可選值：
                - "keyword": 精確關鍵詞匹配（默認）
                - "fuzzy": 模糊內容匹配（使用相似度算法）
                - "entity": 實體名稱搜索（自動按權重排序）
            date_range: 日期範圍（可選）
                       - **格式**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **示例**: {"start": "2025-01-01", "end": "2025-01-07"}
                       - **默認**: 不指定時默認查詢今天
                       - **注意**: start和end可以相同（表示單日查詢）
            platforms: 平臺過濾列表，如 ['zhihu', 'weibo']
            limit: 返回條數限制，默認50
            sort_by: 排序方式，可選值：
                - "relevance": 按相關度排序（默認）
                - "weight": 按新聞權重排序
                - "date": 按日期排序
            threshold: 相似度閾值（僅fuzzy模式有效），0-1之間，默認0.6
            include_url: 是否包含URL鏈接，默認False（節省token）

        Returns:
            搜索結果字典，包含匹配的新聞列表

        Examples:
            - search_news_unified(query="人工智能", search_mode="keyword")
            - search_news_unified(query="特斯拉降價", search_mode="fuzzy", threshold=0.4)
            - search_news_unified(query="馬斯克", search_mode="entity", limit=20)
            - search_news_unified(query="iPhone 16", date_range={"start": "2025-01-01", "end": "2025-01-07"})
        """
        try:
            # 參數驗證
            query = validate_keyword(query)

            if search_mode not in ["keyword", "fuzzy", "entity"]:
                raise InvalidParameterError(
                    f"無效的搜索模式: {search_mode}",
                    suggestion="支持的模式: keyword, fuzzy, entity"
                )

            if sort_by not in ["relevance", "weight", "date"]:
                raise InvalidParameterError(
                    f"無效的排序方式: {sort_by}",
                    suggestion="支持的排序: relevance, weight, date"
                )

            limit = validate_limit(limit, default=50)
            threshold = max(0.0, min(1.0, threshold))

            # 處理日期範圍
            if date_range:
                from ..utils.validators import validate_date_range
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # 不指定日期時，使用最新可用數據日期（而非 datetime.now()）
                earliest, latest = self.data_service.get_available_date_range()

                if latest is None:
                    # 沒有任何可用數據
                    return {
                        "success": False,
                        "error": {
                            "code": "NO_DATA_AVAILABLE",
                            "message": "output 目錄下沒有可用的新聞數據",
                            "suggestion": "請先運行爬蟲生成數據，或檢查 output 目錄"
                        }
                    }

                # 使用最新可用日期
                start_date = end_date = latest

            # 收集所有匹配的新聞
            all_matches = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    all_titles, id_to_name, timestamps = self.data_service.parser.read_all_titles_for_date(
                        date=current_date,
                        platform_ids=platforms
                    )

                    # 根據搜索模式執行不同的搜索邏輯
                    if search_mode == "keyword":
                        matches = self._search_by_keyword_mode(
                            query, all_titles, id_to_name, current_date, include_url
                        )
                    elif search_mode == "fuzzy":
                        matches = self._search_by_fuzzy_mode(
                            query, all_titles, id_to_name, current_date, threshold, include_url
                        )
                    else:  # entity
                        matches = self._search_by_entity_mode(
                            query, all_titles, id_to_name, current_date, include_url
                        )

                    all_matches.extend(matches)

                except DataNotFoundError:
                    # 該日期沒有數據，繼續下一天
                    pass

                current_date += timedelta(days=1)

            if not all_matches:
                # 獲取可用日期範圍用於錯誤提示
                earliest, latest = self.data_service.get_available_date_range()

                # 判斷時間範圍描述
                if start_date.date() == datetime.now().date() and start_date == end_date:
                    time_desc = "今天"
                elif start_date == end_date:
                    time_desc = start_date.strftime("%Y-%m-%d")
                else:
                    time_desc = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"

                # 構建錯誤消息
                if earliest and latest:
                    available_desc = f"{earliest.strftime('%Y-%m-%d')} 至 {latest.strftime('%Y-%m-%d')}"
                    message = f"未找到匹配的新聞（查詢範圍: {time_desc}，可用數據: {available_desc}）"
                else:
                    message = f"未找到匹配的新聞（{time_desc}）"

                result = {
                    "success": True,
                    "results": [],
                    "total": 0,
                    "query": query,
                    "search_mode": search_mode,
                    "time_range": time_desc,
                    "message": message
                }
                return result

            # 統一排序邏輯
            if sort_by == "relevance":
                all_matches.sort(key=lambda x: x.get("similarity_score", 1.0), reverse=True)
            elif sort_by == "weight":
                from .analytics import calculate_news_weight
                all_matches.sort(key=lambda x: calculate_news_weight(x), reverse=True)
            elif sort_by == "date":
                all_matches.sort(key=lambda x: x.get("date", ""), reverse=True)

            # 限制返回數量
            results = all_matches[:limit]

            # 構建時間範圍描述（正確判斷是否爲今天）
            if start_date.date() == datetime.now().date() and start_date == end_date:
                time_range_desc = "今天"
            elif start_date == end_date:
                time_range_desc = start_date.strftime("%Y-%m-%d")
            else:
                time_range_desc = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"

            result = {
                "success": True,
                "summary": {
                    "total_found": len(all_matches),
                    "returned_count": len(results),
                    "requested_limit": limit,
                    "search_mode": search_mode,
                    "query": query,
                    "platforms": platforms or "所有平臺",
                    "time_range": time_range_desc,
                    "sort_by": sort_by
                },
                "results": results
            }

            if search_mode == "fuzzy":
                result["summary"]["threshold"] = threshold
                if len(all_matches) < limit:
                    result["note"] = f"模糊搜索模式下，相似度閾值 {threshold} 僅匹配到 {len(all_matches)} 條結果"

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

    def _search_by_keyword_mode(
        self,
        query: str,
        all_titles: Dict,
        id_to_name: Dict,
        current_date: datetime,
        include_url: bool
    ) -> List[Dict]:
        """
        關鍵詞搜索模式（精確匹配）

        Args:
            query: 搜索關鍵詞
            all_titles: 所有標題字典
            id_to_name: 平臺ID到名稱映射
            current_date: 當前日期

        Returns:
            匹配的新聞列表
        """
        matches = []
        query_lower = query.lower()

        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # 精確包含判斷
                if query_lower in title.lower():
                    news_item = {
                        "title": title,
                        "platform": platform_id,
                        "platform_name": platform_name,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "similarity_score": 1.0,  # 精確匹配，相似度爲1
                        "ranks": info.get("ranks", []),
                        "count": len(info.get("ranks", [])),
                        "rank": info["ranks"][0] if info["ranks"] else 999
                    }

                    # 條件性添加 URL 字段
                    if include_url:
                        news_item["url"] = info.get("url", "")
                        news_item["mobileUrl"] = info.get("mobileUrl", "")

                    matches.append(news_item)

        return matches

    def _search_by_fuzzy_mode(
        self,
        query: str,
        all_titles: Dict,
        id_to_name: Dict,
        current_date: datetime,
        threshold: float,
        include_url: bool
    ) -> List[Dict]:
        """
        模糊搜索模式（使用相似度算法）

        Args:
            query: 搜索內容
            all_titles: 所有標題字典
            id_to_name: 平臺ID到名稱映射
            current_date: 當前日期
            threshold: 相似度閾值

        Returns:
            匹配的新聞列表
        """
        matches = []

        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # 模糊匹配
                is_match, similarity = self._fuzzy_match(query, title, threshold)

                if is_match:
                    news_item = {
                        "title": title,
                        "platform": platform_id,
                        "platform_name": platform_name,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "similarity_score": round(similarity, 4),
                        "ranks": info.get("ranks", []),
                        "count": len(info.get("ranks", [])),
                        "rank": info["ranks"][0] if info["ranks"] else 999
                    }

                    # 條件性添加 URL 字段
                    if include_url:
                        news_item["url"] = info.get("url", "")
                        news_item["mobileUrl"] = info.get("mobileUrl", "")

                    matches.append(news_item)

        return matches

    def _search_by_entity_mode(
        self,
        query: str,
        all_titles: Dict,
        id_to_name: Dict,
        current_date: datetime,
        include_url: bool
    ) -> List[Dict]:
        """
        實體搜索模式（自動按權重排序）

        Args:
            query: 實體名稱
            all_titles: 所有標題字典
            id_to_name: 平臺ID到名稱映射
            current_date: 當前日期

        Returns:
            匹配的新聞列表
        """
        matches = []

        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # 實體搜索：精確包含實體名稱
                if query in title:
                    news_item = {
                        "title": title,
                        "platform": platform_id,
                        "platform_name": platform_name,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "similarity_score": 1.0,
                        "ranks": info.get("ranks", []),
                        "count": len(info.get("ranks", [])),
                        "rank": info["ranks"][0] if info["ranks"] else 999
                    }

                    # 條件性添加 URL 字段
                    if include_url:
                        news_item["url"] = info.get("url", "")
                        news_item["mobileUrl"] = info.get("mobileUrl", "")

                    matches.append(news_item)

        return matches

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        計算兩個文本的相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度分數 (0-1之間)
        """
        # 使用 difflib.SequenceMatcher 計算序列相似度
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _fuzzy_match(self, query: str, text: str, threshold: float = 0.3) -> Tuple[bool, float]:
        """
        模糊匹配函數

        Args:
            query: 查詢文本
            text: 待匹配文本
            threshold: 匹配閾值

        Returns:
            (是否匹配, 相似度分數)
        """
        # 直接包含判斷
        if query.lower() in text.lower():
            return True, 1.0

        # 計算整體相似度
        similarity = self._calculate_similarity(query, text)
        if similarity >= threshold:
            return True, similarity

        # 分詞後的部分匹配
        query_words = set(self._extract_keywords(query))
        text_words = set(self._extract_keywords(text))

        if not query_words or not text_words:
            return False, 0.0

        # 計算關鍵詞重合度
        common_words = query_words & text_words
        keyword_overlap = len(common_words) / len(query_words)

        if keyword_overlap >= 0.5:  # 50%的關鍵詞重合
            return True, keyword_overlap

        return False, similarity

    def _extract_keywords(self, text: str, min_length: int = 2) -> List[str]:
        """
        從文本中提取關鍵詞

        Args:
            text: 輸入文本
            min_length: 最小詞長

        Returns:
            關鍵詞列表
        """
        # 移除URL和特殊字符
        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'\[.*?\]', '', text)  # 移除方括號內容

        # 使用正則表達式分詞（中文和英文）
        words = re.findall(r'[\w]+', text)

        # 過濾停用詞和短詞
        keywords = [
            word for word in words
            if word and len(word) >= min_length and word not in self.stopwords
        ]

        return keywords

    def _calculate_keyword_overlap(self, keywords1: List[str], keywords2: List[str]) -> float:
        """
        計算兩個關鍵詞列表的重合度

        Args:
            keywords1: 關鍵詞列表1
            keywords2: 關鍵詞列表2

        Returns:
            重合度分數 (0-1之間)
        """
        if not keywords1 or not keywords2:
            return 0.0

        set1 = set(keywords1)
        set2 = set(keywords2)

        # Jaccard 相似度
        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def search_related_news_history(
        self,
        reference_text: str,
        time_preset: str = "yesterday",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        threshold: float = 0.4,
        limit: int = 50,
        include_url: bool = False
    ) -> Dict:
        """
        在歷史數據中搜索與給定新聞相關的新聞

        Args:
            reference_text: 參考新聞標題或內容
            time_preset: 時間範圍預設值，可選：
                - "yesterday": 昨天
                - "last_week": 上週 (7天)
                - "last_month": 上個月 (30天)
                - "custom": 自定義日期範圍（需要提供 start_date 和 end_date）
            start_date: 自定義開始日期（僅當 time_preset="custom" 時有效）
            end_date: 自定義結束日期（僅當 time_preset="custom" 時有效）
            threshold: 相似度閾值 (0-1之間)，默認0.4
            limit: 返回條數限制，默認50
            include_url: 是否包含URL鏈接，默認False（節省token）

        Returns:
            搜索結果字典，包含相關新聞列表

        Example:
            >>> tools = SearchTools()
            >>> result = tools.search_related_news_history(
            ...     reference_text="人工智能技術突破",
            ...     time_preset="last_week",
            ...     threshold=0.4,
            ...     limit=50
            ... )
            >>> for news in result['results']:
            ...     print(f"{news['date']}: {news['title']} (相似度: {news['similarity_score']})")
        """
        try:
            # 參數驗證
            reference_text = validate_keyword(reference_text)
            threshold = max(0.0, min(1.0, threshold))
            limit = validate_limit(limit, default=50)

            # 確定查詢日期範圍
            today = datetime.now()

            if time_preset == "yesterday":
                search_start = today - timedelta(days=1)
                search_end = today - timedelta(days=1)
            elif time_preset == "last_week":
                search_start = today - timedelta(days=7)
                search_end = today - timedelta(days=1)
            elif time_preset == "last_month":
                search_start = today - timedelta(days=30)
                search_end = today - timedelta(days=1)
            elif time_preset == "custom":
                if not start_date or not end_date:
                    raise InvalidParameterError(
                        "自定義時間範圍需要提供 start_date 和 end_date",
                        suggestion="請提供 start_date 和 end_date 參數"
                    )
                search_start = start_date
                search_end = end_date
            else:
                raise InvalidParameterError(
                    f"不支持的時間範圍: {time_preset}",
                    suggestion="請使用 'yesterday', 'last_week', 'last_month' 或 'custom'"
                )

            # 提取參考文本的關鍵詞
            reference_keywords = self._extract_keywords(reference_text)

            if not reference_keywords:
                raise InvalidParameterError(
                    "無法從參考文本中提取關鍵詞",
                    suggestion="請提供更詳細的文本內容"
                )

            # 收集所有相關新聞
            all_related_news = []
            current_date = search_start

            while current_date <= search_end:
                try:
                    # 讀取該日期的數據
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(current_date)

                    # 搜索相關新聞
                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)

                        for title, info in titles.items():
                            # 計算標題相似度
                            title_similarity = self._calculate_similarity(reference_text, title)

                            # 提取標題關鍵詞
                            title_keywords = self._extract_keywords(title)

                            # 計算關鍵詞重合度
                            keyword_overlap = self._calculate_keyword_overlap(
                                reference_keywords,
                                title_keywords
                            )

                            # 綜合相似度 (70% 關鍵詞重合 + 30% 文本相似度)
                            combined_score = keyword_overlap * 0.7 + title_similarity * 0.3

                            if combined_score >= threshold:
                                news_item = {
                                    "title": title,
                                    "platform": platform_id,
                                    "platform_name": platform_name,
                                    "date": current_date.strftime("%Y-%m-%d"),
                                    "similarity_score": round(combined_score, 4),
                                    "keyword_overlap": round(keyword_overlap, 4),
                                    "text_similarity": round(title_similarity, 4),
                                    "common_keywords": list(set(reference_keywords) & set(title_keywords)),
                                    "rank": info["ranks"][0] if info["ranks"] else 0
                                }

                                # 條件性添加 URL 字段
                                if include_url:
                                    news_item["url"] = info.get("url", "")
                                    news_item["mobileUrl"] = info.get("mobileUrl", "")

                                all_related_news.append(news_item)

                except DataNotFoundError:
                    # 該日期沒有數據，繼續下一天
                    pass
                except Exception as e:
                    # 記錄錯誤但繼續處理其他日期
                    print(f"Warning: 處理日期 {current_date.strftime('%Y-%m-%d')} 時出錯: {e}")

                # 移動到下一天
                current_date += timedelta(days=1)

            if not all_related_news:
                return {
                    "success": True,
                    "results": [],
                    "total": 0,
                    "query": reference_text,
                    "time_preset": time_preset,
                    "date_range": {
                        "start": search_start.strftime("%Y-%m-%d"),
                        "end": search_end.strftime("%Y-%m-%d")
                    },
                    "message": "未找到相關新聞"
                }

            # 按相似度排序
            all_related_news.sort(key=lambda x: x["similarity_score"], reverse=True)

            # 限制返回數量
            results = all_related_news[:limit]

            # 統計信息
            platform_distribution = Counter([news["platform"] for news in all_related_news])
            date_distribution = Counter([news["date"] for news in all_related_news])

            result = {
                "success": True,
                "summary": {
                    "total_found": len(all_related_news),
                    "returned_count": len(results),
                    "requested_limit": limit,
                    "threshold": threshold,
                    "reference_text": reference_text,
                    "reference_keywords": reference_keywords,
                    "time_preset": time_preset,
                    "date_range": {
                        "start": search_start.strftime("%Y-%m-%d"),
                        "end": search_end.strftime("%Y-%m-%d")
                    }
                },
                "results": results,
                "statistics": {
                    "platform_distribution": dict(platform_distribution),
                    "date_distribution": dict(date_distribution),
                    "avg_similarity": round(
                        sum([news["similarity_score"] for news in all_related_news]) / len(all_related_news),
                        4
                    ) if all_related_news else 0.0
                }
            }

            if len(all_related_news) < limit:
                result["note"] = f"相關性閾值 {threshold} 下僅找到 {len(all_related_news)} 條相關新聞"

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
