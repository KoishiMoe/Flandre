# import re
from urllib import parse

# from aiohttp import ClientSession

from .mediawiki import MediaWiki


class Wiki:

    def __init__(self, api_url: str, fallback_url: str):
        self.__url = fallback_url
        self.__api_url = api_url

    async def get_from_api(self, title: str, is_template: bool) -> str:
        if is_template:
            title = "T:" + title
        if self.__api_url == '':
            result = await self.url_parse(title)
            return result
        try:
            result = await MediaWiki.opensearch(self.__api_url, title, results=1)
        except:  # 针对无法正常调用API的情况的回落，例如WAF
            result = await self.url_parse(title)
            result = f"Api调用出错，以下是由条目名直接生成的链接：\n{result}"
            return result
        if result:
            # title0 = title  # 后续检查ip要用原始title,先备份下……（历史遗留问题）
            title = result[0][0]
            url = result[0][2]
            result = f"标题：{title}\n链接：{url}"

            # 小丑了，opensearch api并不会直接将这些特殊页面转换成具体的用户页地址，不过出于以后可能有用的原因暂时保留
            #
            # # 检查条目名中是否有自己的公网ip,防止恶意用户用特殊页面搞事
            # if re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
            #             title):
            #     if not self.check_ip(title, 4):
            #         result = await self.url_parse(title0)
            # if re.match(r"^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}$", title, re.I):
            #     if not self.check_ip(title, 6):
            #         result = await self.url_parse(title0)

        else:
            result = await self.url_parse(title)
            result = f"没有找到该条目，以下是由条目名直接生成的链接\n{result}"
        return result

    async def url_parse(self, title: str) -> str:
        result = f"标题：{title}\n链接：{self.__url}/{parse.quote(title)}"
        return result

    # 暂时无用的ip检查代码
    # @staticmethod
    # async def check_ip(title: str, ipv: int):
    #     try:
    #         async with ClientSession() as session:
    #             if ipv == 4:
    #                 resp = await session.get('https://v4.ident.me/')
    #             else:
    #                 resp = await session.get('https://v6.ident.me/')
    #             ip = resp.text()
    #         if ip in title:
    #             return False
    #         else:
    #             return True
    #     except:
    #         return False
