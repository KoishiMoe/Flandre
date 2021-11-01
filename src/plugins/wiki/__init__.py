import re

from nonebot import on_regex
from nonebot.adapters.cqhttp import Bot, MessageEvent, utils
from nonebot.permission import SUPERUSER
from nonebot.adapters.cqhttp.permission import GROUP_OWNER, GROUP_ADMIN, GROUP

from .data_source import Wiki

ARTICLE_RAW = r"&#91;&#91;(.*?)&#93;&#93;"  # 似乎是adapter出于安全原因会把中括号转义
ARTICLE = r"\[\[(.*?)\]\]"
TEMPLATE = r"\{\{(.*?)\}\}"
RAW = r"\(\((.*?)\)\)"

# TODO:将wiki地址存入配置文件中
WIKIURL = "https://zh.wikipedia.org/wiki/"
WIKIAPI = "https://zh.wikipedia.org/w/api.php"

wiki = on_regex(ARTICLE_RAW, permission=GROUP)
wiki_template = on_regex(TEMPLATE, permission=GROUP)
wiki_raw = on_regex(RAW, permission=GROUP)

# FIXED:消息被错误转换为转义字符导致无法匹配
@wiki.handle()
async def _wiki(bot: Bot, event: MessageEvent):
    msg = str(event.message).strip()
    msg = utils.unescape(msg) # 将消息处理为正常格式，以防搜索出错
    titles = re.findall(ARTICLE, msg)
    for title in titles:
        wiki = Wiki(WIKIAPI, WIKIURL)
        url = await wiki.get_from_api(title, False)

        await bot.send(event, url)


@wiki_template.handle()
async def _wiki_template(bot: Bot, event: MessageEvent):
    msg = str(event.message).strip()
    msg = utils.unescape(msg) # 将消息处理为正常格式，以防搜索出错
    titles = re.findall(TEMPLATE, msg)
    for title in titles:
        wiki = Wiki(WIKIAPI, WIKIURL)
        url = await wiki.get_from_api(title, True)

        await bot.send(event, url)


@wiki_raw.handle()
async def _wiki_raw(bot: Bot, event: MessageEvent):
    msg = str(event.message).strip()
    msg = utils.unescape(msg) # 将消息处理为正常格式，以防搜索出错
    titles = re.findall(RAW, msg)
    for title in titles:
        wiki = Wiki(WIKIAPI, WIKIURL)
        url = await wiki.url_parse(title)

        await bot.send(event, url)

'''
针对特定群组设置
'''

