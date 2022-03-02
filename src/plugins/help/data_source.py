import re

from nonebot.adapters.onebot.v11.exception import NetworkError
from nonebot.plugin import require

get_wiki = require('wiki').get_wiki
# opensearch = require('wiki').opensearch

api_url = "https://wiki.koishichan.top/api.php"


class Helper:

    @staticmethod
    async def main_menu() -> str:
        return await Helper.get_title("Flandre:帮助")

    @staticmethod
    async def about_me() -> str:
        return await Helper.get_title("Flandre:关于")

    @staticmethod
    async def service_list() -> str:
        return await Helper.get_title("Flandre:功能列表")

    @staticmethod
    async def get_title(title: str) -> str:
        try:
            page_content: tuple = await get_wiki(api_url, title if title.startswith('Flandre:') else f"Flandre:{title}")
            content: str = re.split("==", page_content[0])[0] if "==" in page_content[0] else page_content[0]
            return content + "\n完整文档：" + page_content[1]
        except RuntimeError as e:
            return f"获取帮助信息失败：{e}"
        except NetworkError:
            return "获取帮助信息失败：网络错误"
