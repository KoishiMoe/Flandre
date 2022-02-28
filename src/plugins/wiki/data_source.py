# import re
from urllib import parse

# from aiohttp import ClientSession
import nonebot

# from .mediawiki import MediaWiki
from .mwapi import Mwapi
from .exceptions import *


class Wiki:

    def __init__(self, api_url: str, fallback_url: str):
        self.__url = fallback_url
        self.__api_url = api_url

    async def get_from_api(self, title: str, is_template: bool, anchor: str = '') -> str:
        if is_template:
            title = "Template:" + title
        if self.__api_url == '':
            url = await self.url_parse(title)
            result = f"标题：{title}\n链接：{url}{anchor}"
            return result

        # 旧接口的处理逻辑
        # try:
        #     result = await MediaWiki.opensearch(self.__api_url, title, results=1)
        # except:  # 针对无法正常调用API的情况的回落，例如WAF
        #     result = await self.url_parse(title)
        #     result = f"Api调用出错，以下是由条目名直接生成的链接：\n{result}"
        #     return result
        # if result:
        #     # title0 = title  # 后续检查ip要用原始title,先备份下……（历史遗留问题）
        #     title = result[0][0]
        #     url = result[0][2]
        #     result = f"标题：{title}\n链接：{url}"

        try:
            mediawiki = Mwapi(url=self.__url, api_url=self.__api_url)
            result_dict = await mediawiki.get_page_info(title)
        except HTTPTimeoutError:
            exception = "连接超时"
        except MediaWikiException or MediaWikiGeoCoordError as e:
            exception = f"Api调用出错"
            nonebot.logger.log("warning", e)
        except PageError:
            exception = "未找到页面"
        if "exception" in locals():
            url = await self.url_parse(title)
            result_dict = {
                "exception": True,
                "title": title,
                "url": url,
                "notes": exception,
            }

        # 根据返回的result_dict生成结果字符串
        # if result_dict["state"] == "success":
        #     result = f"标题：{result_dict['title']}\n" \
        #              f"链接：{result_dict['url']}"
        # elif result_dict["state"] == "exception":
        #     # TODO: 对未找到页面的情况进行单独处理
        #     result = f"{result_dict['exception']}，以下是由条目名直接生成的链接\n" \
        #              f"标题：{result_dict['title']}\n" \
        #              f"链接：{result_dict['url']}"
        # elif result_dict["state"] == "redirect":
        #     result = f"重定向：{result_dict['from_title']} -> {result_dict['title']}\n" \
        #              f"链接：{result_dict['url']}"
        # elif result_dict["state"] == "disambiguation":
        #     # TODO: 消歧义页通过数字选择条目
        #     options = '\n '.join(result_dict['options'])
        #     result = f"{result_dict['title']}可以指：\n{options}"
        # elif result_dict["state"] == "redirect-disambiguation":
        #     options = '\n '.join(result_dict['options'])
        #     result = f"由{result_dict['title']}重定向到了消歧义页面{result_dict['title']}，" \
        #              f"它可以指：\n{options}"
        # else:
        #     result = "wiki推送模块出现了未知错误……这应当是bot的bug,请更新到最新版本再试；如果问题仍存在，请到项目的github页面提交issue"

        if result_dict["exception"]:
            result = f"错误：{result_dict['notes']}\n" \
                     f"由条目名直接生成的链接：\n" \
                     f"标题：{result_dict['title']}\n链接：{result_dict['url']}{anchor}"
            return result

        match (result_dict["redirected"], result_dict["disambiguation"]):
            case (False, False):
                result = f"标题：{result_dict['title']}\n" \
                             f"链接：{result_dict['url']}{anchor}"
            case (True, False):
                result = f"重定向：{result_dict['from_title']} → {result_dict['title']}\n" \
                         f"链接：{result_dict['url']}{anchor}"
            case (False, True):
                # TODO: 消歧义页通过数字选择条目
                options = '\n'.join(result_dict['notes'])
                result = f"{result_dict['title']}可以指：\n{options}\n请使用具体条目名重新查询"
                # result = f"消歧义页面：{result_dict['title']}\n" \
                #             f"链接：{result_dict['url']}"
            case (True, True):
                options = '\n'.join(result_dict['notes'])
                result = f"由{result_dict['title']}重定向到了消歧义页面{result_dict['title']}，" \
                         f"它可以指：\n{options}\n请使用具体条目名重新查询"
                # result = f"由「{result_dict['from_title']}」重定向到了消歧义页面「{result_dict['title']}」:\n" \
                #          f"链接：{result_dict['url']}"

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

        # else:
        #     result = await self.url_parse(title)
        #     result = f"没有找到该条目，以下是由条目名直接生成的链接\n{result}"
        return result

    async def url_parse(self, title: str) -> str:
        result = f"{self.__url}/{parse.quote(title)}"
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
