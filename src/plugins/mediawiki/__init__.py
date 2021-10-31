import re

from .data_source import Wiki

from nonebot.adapters.cqhttp import Bot, Message, MessageEvent
from nonebot import on_regex, on_command


ARTICLE = r"&#91;&#91;(.*?)&#93;&#93;" #似乎是adapter出于安全原因会把中括号转义
TEMPLATE = r"\{\{(.*?)\}\}"

# TODO:将wiki地址存入配置文件中
WIKIURL = "https://zh.wikipedia.org/wiki/"
WIKIAPI = "https://zh.wikipedia.org/w/api.php"

wiki = on_regex(ARTICLE)
wiki_template = on_regex(TEMPLATE)

# FIXED:消息被错误转换为转义字符导致无法匹配
@wiki.handle()
async def _wiki(bot: Bot, event: MessageEvent):
    msg = str(event.message).strip()
    title = re.findall(ARTICLE, msg)[0]
    wiki = Wiki(WIKIAPI, WIKIURL)
    url = await wiki.get_from_api(title, False)

    await bot.send(event, url)

@wiki_template.handle()
async def _wiki_template(bot: Bot, event: MessageEvent):
    msg = str(event.message).strip()
    title = re.findall(TEMPLATE, msg)[0]
    wiki = Wiki(WIKIAPI, WIKIURL)
    url = await wiki.get_from_api(title, True)

    await bot.send(event, url)
