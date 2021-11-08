import re

from nonebot.adapters.cqhttp.exception import NetworkError
from nonebot.plugin import require

get_wiki = require('wiki').get_wiki
opensearch = require('wiki').opensearch

api_url = "https://wiki.koishichan.top/api.php"


class Helper:

    @staticmethod
    def main_menu() -> str:
        return Helper.get_title("Flandre:帮助")

    @staticmethod
    def about_me() -> str:
        return Helper.get_title("Flandre:关于")

    @staticmethod
    def service_list() -> str:
        return Helper.get_title("Flandre:功能列表")

    @staticmethod
    def get_title(title: str) -> str:
        try:
            page_content: tuple = get_wiki(api_url, title)
            content: str = re.split("==", page_content[0])[0] if "==" in page_content[0] else page_content[0]
            return content + f"完整文档：" + page_content[1]
        except RuntimeError as e:
            return f"获取帮助信息失败：{e}"
        except NetworkError as e:
            return "获取帮助信息失败：网络错误"
