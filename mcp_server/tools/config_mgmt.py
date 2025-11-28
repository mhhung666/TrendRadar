"""
配置管理工具

實現配置查詢和管理功能。
"""

from typing import Dict, Optional

from ..services.data_service import DataService
from ..utils.validators import validate_config_section
from ..utils.errors import MCPError


class ConfigManagementTools:
    """配置管理工具類"""

    def __init__(self, project_root: str = None):
        """
        初始化配置管理工具

        Args:
            project_root: 項目根目錄
        """
        self.data_service = DataService(project_root)

    def get_current_config(self, section: Optional[str] = None) -> Dict:
        """
        獲取當前系統配置

        Args:
            section: 配置節 - all/crawler/push/keywords/weights，默認all

        Returns:
            配置字典

        Example:
            >>> tools = ConfigManagementTools()
            >>> result = tools.get_current_config(section="crawler")
            >>> print(result['crawler']['platforms'])
        """
        try:
            # 參數驗證
            section = validate_config_section(section)

            # 獲取配置
            config = self.data_service.get_current_config(section=section)

            return {
                "config": config,
                "section": section,
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
