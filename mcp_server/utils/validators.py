"""
參數驗證工具

提供統一的參數驗證功能。
"""

from datetime import datetime
from typing import List, Optional
import os
import yaml

from .errors import InvalidParameterError
from .date_parser import DateParser


def get_supported_platforms() -> List[str]:
    """
    從 config.yaml 動態獲取支持的平臺列表

    Returns:
        平臺ID列表

    Note:
        - 讀取失敗時返回空列表，允許所有平臺通過（降級策略）
        - 平臺列表來自 config/config.yaml 中的 platforms 配置
    """
    try:
        # 獲取 config.yaml 路徑（相對於當前文件）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "..", "..", "config", "config.yaml")
        config_path = os.path.normpath(config_path)

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            platforms = config.get('platforms', [])
            return [p['id'] for p in platforms if 'id' in p]
    except Exception as e:
        # 降級方案：返回空列表，允許所有平臺
        print(f"警告：無法加載平臺配置 ({config_path}): {e}")
        return []


def validate_platforms(platforms: Optional[List[str]]) -> List[str]:
    """
    驗證平臺列表

    Args:
        platforms: 平臺ID列表，None表示使用 config.yaml 中配置的所有平臺

    Returns:
        驗證後的平臺列表

    Raises:
        InvalidParameterError: 平臺不支持

    Note:
        - platforms=None 時，返回 config.yaml 中配置的平臺列表
        - 會驗證平臺ID是否在 config.yaml 的 platforms 配置中
        - 配置加載失敗時，允許所有平臺通過（降級策略）
    """
    supported_platforms = get_supported_platforms()

    if platforms is None:
        # 返回配置文件中的平臺列表（用戶的默認配置）
        return supported_platforms if supported_platforms else []

    if not isinstance(platforms, list):
        raise InvalidParameterError("platforms 參數必須是列表類型")

    if not platforms:
        # 空列表時，返回配置文件中的平臺列表
        return supported_platforms if supported_platforms else []

    # 如果配置加載失敗（supported_platforms爲空），允許所有平臺通過
    if not supported_platforms:
        print("警告：平臺配置未加載，跳過平臺驗證")
        return platforms

    # 驗證每個平臺是否在配置中
    invalid_platforms = [p for p in platforms if p not in supported_platforms]
    if invalid_platforms:
        raise InvalidParameterError(
            f"不支持的平臺: {', '.join(invalid_platforms)}",
            suggestion=f"支持的平臺（來自config.yaml）: {', '.join(supported_platforms)}"
        )

    return platforms


def validate_limit(limit: Optional[int], default: int = 20, max_limit: int = 1000) -> int:
    """
    驗證數量限制參數

    Args:
        limit: 限制數量
        default: 默認值
        max_limit: 最大限制

    Returns:
        驗證後的限制值

    Raises:
        InvalidParameterError: 參數無效
    """
    if limit is None:
        return default

    if not isinstance(limit, int):
        raise InvalidParameterError("limit 參數必須是整數類型")

    if limit <= 0:
        raise InvalidParameterError("limit 必須大於0")

    if limit > max_limit:
        raise InvalidParameterError(
            f"limit 不能超過 {max_limit}",
            suggestion=f"請使用分頁或降低limit值"
        )

    return limit


def validate_date(date_str: str) -> datetime:
    """
    驗證日期格式

    Args:
        date_str: 日期字符串 (YYYY-MM-DD)

    Returns:
        datetime對象

    Raises:
        InvalidParameterError: 日期格式錯誤
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise InvalidParameterError(
            f"日期格式錯誤: {date_str}",
            suggestion="請使用 YYYY-MM-DD 格式，例如: 2025-10-11"
        )


def validate_date_range(date_range: Optional[dict]) -> Optional[tuple]:
    """
    驗證日期範圍

    Args:
        date_range: 日期範圍字典 {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}

    Returns:
        (start_date, end_date) 元組，或 None

    Raises:
        InvalidParameterError: 日期範圍無效
    """
    if date_range is None:
        return None

    if not isinstance(date_range, dict):
        raise InvalidParameterError("date_range 必須是字典類型")

    start_str = date_range.get("start")
    end_str = date_range.get("end")

    if not start_str or not end_str:
        raise InvalidParameterError(
            "date_range 必須包含 start 和 end 字段",
            suggestion='例如: {"start": "2025-10-01", "end": "2025-10-11"}'
        )

    start_date = validate_date(start_str)
    end_date = validate_date(end_str)

    if start_date > end_date:
        raise InvalidParameterError(
            "開始日期不能晚於結束日期",
            suggestion=f"start: {start_str}, end: {end_str}"
        )

    # 檢查日期是否在未來
    today = datetime.now().date()
    if start_date.date() > today or end_date.date() > today:
        # 獲取可用日期範圍提示
        try:
            from ..services.data_service import DataService
            data_service = DataService()
            earliest, latest = data_service.get_available_date_range()

            if earliest and latest:
                available_range = f"{earliest.strftime('%Y-%m-%d')} 至 {latest.strftime('%Y-%m-%d')}"
            else:
                available_range = "無可用數據"
        except Exception:
            available_range = "未知（請檢查 output 目錄）"

        future_dates = []
        if start_date.date() > today:
            future_dates.append(start_str)
        if end_date.date() > today and end_str != start_str:
            future_dates.append(end_str)

        raise InvalidParameterError(
            f"不允許查詢未來日期: {', '.join(future_dates)}（當前日期: {today.strftime('%Y-%m-%d')}）",
            suggestion=f"當前可用數據範圍: {available_range}"
        )

    return (start_date, end_date)


def validate_keyword(keyword: str) -> str:
    """
    驗證關鍵詞

    Args:
        keyword: 搜索關鍵詞

    Returns:
        處理後的關鍵詞

    Raises:
        InvalidParameterError: 關鍵詞無效
    """
    if not keyword:
        raise InvalidParameterError("keyword 不能爲空")

    if not isinstance(keyword, str):
        raise InvalidParameterError("keyword 必須是字符串類型")

    keyword = keyword.strip()

    if not keyword:
        raise InvalidParameterError("keyword 不能爲空白字符")

    if len(keyword) > 100:
        raise InvalidParameterError(
            "keyword 長度不能超過100個字符",
            suggestion="請使用更簡潔的關鍵詞"
        )

    return keyword


def validate_top_n(top_n: Optional[int], default: int = 10) -> int:
    """
    驗證TOP N參數

    Args:
        top_n: TOP N數量
        default: 默認值

    Returns:
        驗證後的值

    Raises:
        InvalidParameterError: 參數無效
    """
    return validate_limit(top_n, default=default, max_limit=100)


def validate_mode(mode: Optional[str], valid_modes: List[str], default: str) -> str:
    """
    驗證模式參數

    Args:
        mode: 模式字符串
        valid_modes: 有效模式列表
        default: 默認模式

    Returns:
        驗證後的模式

    Raises:
        InvalidParameterError: 模式無效
    """
    if mode is None:
        return default

    if not isinstance(mode, str):
        raise InvalidParameterError("mode 必須是字符串類型")

    if mode not in valid_modes:
        raise InvalidParameterError(
            f"無效的模式: {mode}",
            suggestion=f"支持的模式: {', '.join(valid_modes)}"
        )

    return mode


def validate_config_section(section: Optional[str]) -> str:
    """
    驗證配置節參數

    Args:
        section: 配置節名稱

    Returns:
        驗證後的配置節

    Raises:
        InvalidParameterError: 配置節無效
    """
    valid_sections = ["all", "crawler", "push", "keywords", "weights"]
    return validate_mode(section, valid_sections, "all")


def validate_date_query(
    date_query: str,
    allow_future: bool = False,
    max_days_ago: int = 365
) -> datetime:
    """
    驗證並解析日期查詢字符串

    Args:
        date_query: 日期查詢字符串
        allow_future: 是否允許未來日期
        max_days_ago: 允許查詢的最大天數

    Returns:
        解析後的datetime對象

    Raises:
        InvalidParameterError: 日期查詢無效

    Examples:
        >>> validate_date_query("昨天")
        datetime(2025, 10, 10)
        >>> validate_date_query("2025-10-10")
        datetime(2025, 10, 10)
    """
    if not date_query:
        raise InvalidParameterError(
            "日期查詢字符串不能爲空",
            suggestion="請提供日期查詢，如：今天、昨天、2025-10-10"
        )

    # 使用DateParser解析日期
    parsed_date = DateParser.parse_date_query(date_query)

    # 驗證日期不在未來
    if not allow_future:
        DateParser.validate_date_not_future(parsed_date)

    # 驗證日期不太久遠
    DateParser.validate_date_not_too_old(parsed_date, max_days=max_days_ago)

    return parsed_date

