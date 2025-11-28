"""
日期解析工具

支持多種自然語言日期格式解析，包括相對日期和絕對日期。
"""

import re
from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional

from .errors import InvalidParameterError


class DateParser:
    """日期解析器類"""

    # 中文日期映射
    CN_DATE_MAPPING = {
        "今天": 0,
        "昨天": 1,
        "前天": 2,
        "大前天": 3,
    }

    # 英文日期映射
    EN_DATE_MAPPING = {
        "today": 0,
        "yesterday": 1,
    }

    # 日期範圍表達式（用於 resolve_date_range_expression）
    RANGE_EXPRESSIONS = {
        # 中文表達式
        "今天": "today",
        "昨天": "yesterday",
        "本週": "this_week",
        "這周": "this_week",
        "當前周": "this_week",
        "上週": "last_week",
        "本月": "this_month",
        "這個月": "this_month",
        "當前月": "this_month",
        "上月": "last_month",
        "上個月": "last_month",
        "最近3天": "last_3_days",
        "近3天": "last_3_days",
        "最近7天": "last_7_days",
        "近7天": "last_7_days",
        "最近一週": "last_7_days",
        "過去一週": "last_7_days",
        "最近14天": "last_14_days",
        "近14天": "last_14_days",
        "最近兩週": "last_14_days",
        "過去兩週": "last_14_days",
        "最近30天": "last_30_days",
        "近30天": "last_30_days",
        "最近一個月": "last_30_days",
        "過去一個月": "last_30_days",
        # 英文表達式
        "today": "today",
        "yesterday": "yesterday",
        "this week": "this_week",
        "current week": "this_week",
        "last week": "last_week",
        "this month": "this_month",
        "current month": "this_month",
        "last month": "last_month",
        "last 3 days": "last_3_days",
        "past 3 days": "last_3_days",
        "last 7 days": "last_7_days",
        "past 7 days": "last_7_days",
        "past week": "last_7_days",
        "last 14 days": "last_14_days",
        "past 14 days": "last_14_days",
        "last 30 days": "last_30_days",
        "past 30 days": "last_30_days",
        "past month": "last_30_days",
    }

    # 星期映射
    WEEKDAY_CN = {
        "一": 0, "二": 1, "三": 2, "四": 3,
        "五": 4, "六": 5, "日": 6, "天": 6
    }

    WEEKDAY_EN = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }

    @staticmethod
    def parse_date_query(date_query: str) -> datetime:
        """
        解析日期查詢字符串

        支持的格式：
        - 相對日期（中文）：今天、昨天、前天、大前天、N天前
        - 相對日期（英文）：today、yesterday、N days ago
        - 星期（中文）：上週一、上週二、本週三
        - 星期（英文）：last monday、this friday
        - 絕對日期：2025-10-10、10月10日、2025年10月10日

        Args:
            date_query: 日期查詢字符串

        Returns:
            datetime對象

        Raises:
            InvalidParameterError: 日期格式無法識別

        Examples:
            >>> DateParser.parse_date_query("今天")
            datetime(2025, 10, 11)
            >>> DateParser.parse_date_query("昨天")
            datetime(2025, 10, 10)
            >>> DateParser.parse_date_query("3天前")
            datetime(2025, 10, 8)
            >>> DateParser.parse_date_query("2025-10-10")
            datetime(2025, 10, 10)
        """
        if not date_query or not isinstance(date_query, str):
            raise InvalidParameterError(
                "日期查詢字符串不能爲空",
                suggestion="請提供有效的日期查詢，如：今天、昨天、2025-10-10"
            )

        date_query = date_query.strip().lower()

        # 1. 嘗試解析中文常用相對日期
        if date_query in DateParser.CN_DATE_MAPPING:
            days_ago = DateParser.CN_DATE_MAPPING[date_query]
            return datetime.now() - timedelta(days=days_ago)

        # 2. 嘗試解析英文常用相對日期
        if date_query in DateParser.EN_DATE_MAPPING:
            days_ago = DateParser.EN_DATE_MAPPING[date_query]
            return datetime.now() - timedelta(days=days_ago)

        # 3. 嘗試解析 "N天前" 或 "N days ago"
        cn_days_ago_match = re.match(r'(\d+)\s*天前', date_query)
        if cn_days_ago_match:
            days = int(cn_days_ago_match.group(1))
            if days > 365:
                raise InvalidParameterError(
                    f"天數過大: {days}天",
                    suggestion="請使用小於365天的相對日期或使用絕對日期"
                )
            return datetime.now() - timedelta(days=days)

        en_days_ago_match = re.match(r'(\d+)\s*days?\s+ago', date_query)
        if en_days_ago_match:
            days = int(en_days_ago_match.group(1))
            if days > 365:
                raise InvalidParameterError(
                    f"天數過大: {days}天",
                    suggestion="請使用小於365天的相對日期或使用絕對日期"
                )
            return datetime.now() - timedelta(days=days)

        # 4. 嘗試解析星期（中文）：上週一、本週三
        cn_weekday_match = re.match(r'(上|本)周([一二三四五六日天])', date_query)
        if cn_weekday_match:
            week_type = cn_weekday_match.group(1)  # 上 或 本
            weekday_str = cn_weekday_match.group(2)
            target_weekday = DateParser.WEEKDAY_CN[weekday_str]
            return DateParser._get_date_by_weekday(target_weekday, week_type == "上")

        # 5. 嘗試解析星期（英文）：last monday、this friday
        en_weekday_match = re.match(r'(last|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', date_query)
        if en_weekday_match:
            week_type = en_weekday_match.group(1)  # last 或 this
            weekday_str = en_weekday_match.group(2)
            target_weekday = DateParser.WEEKDAY_EN[weekday_str]
            return DateParser._get_date_by_weekday(target_weekday, week_type == "last")

        # 6. 嘗試解析絕對日期：YYYY-MM-DD
        iso_date_match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_query)
        if iso_date_match:
            year = int(iso_date_match.group(1))
            month = int(iso_date_match.group(2))
            day = int(iso_date_match.group(3))
            try:
                return datetime(year, month, day)
            except ValueError as e:
                raise InvalidParameterError(
                    f"無效的日期: {date_query}",
                    suggestion=f"日期值錯誤: {str(e)}"
                )

        # 7. 嘗試解析中文日期：MM月DD日 或 YYYY年MM月DD日
        cn_date_match = re.match(r'(?:(\d{4})年)?(\d{1,2})月(\d{1,2})日', date_query)
        if cn_date_match:
            year_str = cn_date_match.group(1)
            month = int(cn_date_match.group(2))
            day = int(cn_date_match.group(3))

            # 如果沒有年份，使用當前年份
            if year_str:
                year = int(year_str)
            else:
                year = datetime.now().year
                # 如果月份大於當前月份，說明是去年
                current_month = datetime.now().month
                if month > current_month:
                    year -= 1

            try:
                return datetime(year, month, day)
            except ValueError as e:
                raise InvalidParameterError(
                    f"無效的日期: {date_query}",
                    suggestion=f"日期值錯誤: {str(e)}"
                )

        # 8. 嘗試解析斜槓格式：YYYY/MM/DD 或 MM/DD
        slash_date_match = re.match(r'(?:(\d{4})/)?(\d{1,2})/(\d{1,2})', date_query)
        if slash_date_match:
            year_str = slash_date_match.group(1)
            month = int(slash_date_match.group(2))
            day = int(slash_date_match.group(3))

            if year_str:
                year = int(year_str)
            else:
                year = datetime.now().year
                current_month = datetime.now().month
                if month > current_month:
                    year -= 1

            try:
                return datetime(year, month, day)
            except ValueError as e:
                raise InvalidParameterError(
                    f"無效的日期: {date_query}",
                    suggestion=f"日期值錯誤: {str(e)}"
                )

        # 如果所有格式都不匹配
        raise InvalidParameterError(
            f"無法識別的日期格式: {date_query}",
            suggestion=(
                "支持的格式:\n"
                "- 相對日期: 今天、昨天、前天、3天前、today、yesterday、3 days ago\n"
                "- 星期: 上週一、本週三、last monday、this friday\n"
                "- 絕對日期: 2025-10-10、10月10日、2025年10月10日"
            )
        )

    @staticmethod
    def _get_date_by_weekday(target_weekday: int, is_last_week: bool) -> datetime:
        """
        根據星期幾獲取日期

        Args:
            target_weekday: 目標星期 (0=週一, 6=週日)
            is_last_week: 是否是上週

        Returns:
            datetime對象
        """
        today = datetime.now()
        current_weekday = today.weekday()

        # 計算天數差
        if is_last_week:
            # 上週的某一天
            days_diff = current_weekday - target_weekday + 7
        else:
            # 本週的某一天
            days_diff = current_weekday - target_weekday
            if days_diff < 0:
                days_diff += 7

        return today - timedelta(days=days_diff)

    @staticmethod
    def format_date_folder(date: datetime) -> str:
        """
        將日期格式化爲文件夾名稱

        Args:
            date: datetime對象

        Returns:
            文件夾名稱，格式: YYYY年MM月DD日

        Examples:
            >>> DateParser.format_date_folder(datetime(2025, 10, 11))
            '2025年10月11日'
        """
        return date.strftime("%Y年%m月%d日")

    @staticmethod
    def validate_date_not_future(date: datetime) -> None:
        """
        驗證日期不在未來

        Args:
            date: 待驗證的日期

        Raises:
            InvalidParameterError: 日期在未來
        """
        if date.date() > datetime.now().date():
            raise InvalidParameterError(
                f"不能查詢未來的日期: {date.strftime('%Y-%m-%d')}",
                suggestion="請使用今天或過去的日期"
            )

    @staticmethod
    def validate_date_not_too_old(date: datetime, max_days: int = 365) -> None:
        """
        驗證日期不太久遠

        Args:
            date: 待驗證的日期
            max_days: 最大天數

        Raises:
            InvalidParameterError: 日期太久遠
        """
        days_ago = (datetime.now().date() - date.date()).days
        if days_ago > max_days:
            raise InvalidParameterError(
                f"日期太久遠: {date.strftime('%Y-%m-%d')} ({days_ago}天前)",
                suggestion=f"請查詢{max_days}天內的數據"
            )

    @staticmethod
    def resolve_date_range_expression(expression: str) -> Dict:
        """
        將自然語言日期表達式解析爲標準日期範圍

        這是專門爲 MCP 工具設計的方法，用於在服務器端解析日期表達式，
        避免 AI 模型自己計算日期導致的不一致問題。

        Args:
            expression: 自然語言日期表達式，支持：
                - 單日: "今天", "昨天", "today", "yesterday"
                - 本週/上週: "本週", "上週", "this week", "last week"
                - 本月/上月: "本月", "上月", "this month", "last month"
                - 最近N天: "最近7天", "最近30天", "last 7 days", "last 30 days"
                - 動態N天: "最近5天", "last 10 days"

        Returns:
            解析結果字典：
            {
                "success": True,
                "expression": "本週",
                "normalized": "this_week",
                "date_range": {
                    "start": "2025-11-18",
                    "end": "2025-11-24"
                },
                "current_date": "2025-11-26",
                "description": "本週（週一到週日）"
            }

        Raises:
            InvalidParameterError: 無法識別的日期表達式

        Examples:
            >>> DateParser.resolve_date_range_expression("本週")
            {"success": True, "date_range": {"start": "2025-11-18", "end": "2025-11-24"}, ...}

            >>> DateParser.resolve_date_range_expression("最近7天")
            {"success": True, "date_range": {"start": "2025-11-20", "end": "2025-11-26"}, ...}
        """
        if not expression or not isinstance(expression, str):
            raise InvalidParameterError(
                "日期表達式不能爲空",
                suggestion="請提供有效的日期表達式，如：本週、最近7天、last week"
            )

        expression_lower = expression.strip().lower()
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")

        # 1. 嘗試匹配預定義表達式
        normalized = DateParser.RANGE_EXPRESSIONS.get(expression_lower)

        # 2. 嘗試匹配動態 "最近N天" / "last N days" 模式
        if not normalized:
            # 中文: 最近N天
            cn_match = re.match(r'最近(\d+)天', expression_lower)
            if cn_match:
                days = int(cn_match.group(1))
                normalized = f"last_{days}_days"

            # 英文: last N days
            en_match = re.match(r'(?:last|past)\s+(\d+)\s+days?', expression_lower)
            if en_match:
                days = int(en_match.group(1))
                normalized = f"last_{days}_days"

        if not normalized:
            # 提供支持的表達式列表
            supported_cn = ["今天", "昨天", "本週", "上週", "本月", "上月",
                           "最近7天", "最近30天", "最近N天"]
            supported_en = ["today", "yesterday", "this week", "last week",
                           "this month", "last month", "last 7 days", "last N days"]
            raise InvalidParameterError(
                f"無法識別的日期表達式: {expression}",
                suggestion=f"支持的表達式:\n中文: {', '.join(supported_cn)}\n英文: {', '.join(supported_en)}"
            )

        # 3. 根據 normalized 類型計算日期範圍
        start_date, end_date, description = DateParser._calculate_date_range(
            normalized, today
        )

        return {
            "success": True,
            "expression": expression,
            "normalized": normalized,
            "date_range": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d")
            },
            "current_date": today_str,
            "description": description
        }

    @staticmethod
    def _calculate_date_range(
        normalized: str,
        today: datetime
    ) -> Tuple[datetime, datetime, str]:
        """
        根據標準化的日期類型計算實際日期範圍

        Args:
            normalized: 標準化的日期類型
            today: 當前日期

        Returns:
            (start_date, end_date, description) 元組
        """
        # 單日類型
        if normalized == "today":
            return today, today, "今天"

        if normalized == "yesterday":
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday, "昨天"

        # 本週（週一到週日）
        if normalized == "this_week":
            # 計算本週一
            weekday = today.weekday()  # 0=週一, 6=週日
            start = today - timedelta(days=weekday)
            end = start + timedelta(days=6)
            # 如果本週還沒結束，end 不能超過今天
            if end > today:
                end = today
            return start, end, f"本週（週一到週日，{start.strftime('%m-%d')} 至 {end.strftime('%m-%d')}）"

        # 上週（上週一到上週日）
        if normalized == "last_week":
            weekday = today.weekday()
            # 本週一
            this_monday = today - timedelta(days=weekday)
            # 上週一
            start = this_monday - timedelta(days=7)
            end = start + timedelta(days=6)
            return start, end, f"上週（{start.strftime('%m-%d')} 至 {end.strftime('%m-%d')}）"

        # 本月（本月1日到今天）
        if normalized == "this_month":
            start = today.replace(day=1)
            return start, today, f"本月（{start.strftime('%m-%d')} 至 {today.strftime('%m-%d')}）"

        # 上月（上月1日到上月最後一天）
        if normalized == "last_month":
            # 上月最後一天 = 本月1日 - 1天
            first_of_this_month = today.replace(day=1)
            end = first_of_this_month - timedelta(days=1)
            start = end.replace(day=1)
            return start, end, f"上月（{start.strftime('%Y-%m-%d')} 至 {end.strftime('%Y-%m-%d')}）"

        # 最近N天 (last_N_days 格式)
        match = re.match(r'last_(\d+)_days', normalized)
        if match:
            days = int(match.group(1))
            start = today - timedelta(days=days - 1)  # 包含今天，所以是 days-1
            return start, today, f"最近{days}天（{start.strftime('%m-%d')} 至 {today.strftime('%m-%d')}）"

        # 兜底：返回今天
        return today, today, "今天（默認）"

    @staticmethod
    def get_supported_expressions() -> Dict[str, list]:
        """
        獲取支持的日期表達式列表

        Returns:
            分類的表達式列表
        """
        return {
            "單日": ["今天", "昨天", "today", "yesterday"],
            "周": ["本週", "上週", "this week", "last week"],
            "月": ["本月", "上月", "this month", "last month"],
            "最近N天": ["最近3天", "最近7天", "最近14天", "最近30天",
                      "last 3 days", "last 7 days", "last 14 days", "last 30 days"],
            "動態天數": ["最近N天", "last N days"]
        }
