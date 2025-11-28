"""
自定義錯誤類

定義MCP Server使用的所有自定義異常類型。
"""

from typing import Optional


class MCPError(Exception):
    """MCP工具錯誤基類"""

    def __init__(self, message: str, code: str = "MCP_ERROR", suggestion: Optional[str] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.suggestion = suggestion

    def to_dict(self) -> dict:
        """轉換爲字典格式"""
        error_dict = {
            "code": self.code,
            "message": self.message
        }
        if self.suggestion:
            error_dict["suggestion"] = self.suggestion
        return error_dict


class DataNotFoundError(MCPError):
    """數據不存在錯誤"""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(
            message=message,
            code="DATA_NOT_FOUND",
            suggestion=suggestion or "請檢查日期範圍或等待爬取任務完成"
        )


class InvalidParameterError(MCPError):
    """參數無效錯誤"""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(
            message=message,
            code="INVALID_PARAMETER",
            suggestion=suggestion or "請檢查參數格式是否正確"
        )


class ConfigurationError(MCPError):
    """配置錯誤"""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            suggestion=suggestion or "請檢查配置文件是否正確"
        )


class PlatformNotSupportedError(MCPError):
    """平臺不支持錯誤"""

    def __init__(self, platform: str):
        super().__init__(
            message=f"平臺 '{platform}' 不受支持",
            code="PLATFORM_NOT_SUPPORTED",
            suggestion="支持的平臺: zhihu, weibo, douyin, bilibili, baidu, toutiao, qq, 36kr, sspai, hellogithub, thepaper"
        )


class CrawlTaskError(MCPError):
    """爬取任務錯誤"""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(
            message=message,
            code="CRAWL_TASK_ERROR",
            suggestion=suggestion or "請稍後重試或查看日誌"
        )


class FileParseError(MCPError):
    """文件解析錯誤"""

    def __init__(self, file_path: str, reason: str):
        super().__init__(
            message=f"解析文件 {file_path} 失敗: {reason}",
            code="FILE_PARSE_ERROR",
            suggestion="請檢查文件格式是否正確"
        )
