import re

from nonebot.adapters.cqhttp.exception import NetworkError

from .mediawiki import MediaWiki

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
            page_content: str = MediaWiki.get_page_content(api_url, title)
            content: str = re.split("==", page_content)[0] if "==" in page_content else page_content
            return content + f"完整文档：" + MediaWiki.opensearch(api_url, title, results=1)[0][2]
        except RuntimeError as e:
            return "获取帮助信息失败：未找到帮助条目或api出错"
        except NetworkError as e:
            return "获取帮助信息失败：网络错误"
