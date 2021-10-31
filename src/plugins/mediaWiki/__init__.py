import re

from nonebot.adapters.cqhttp import Bot, Message, MessageEvent
from nonebot.typing import T_State
from nonebot import on_regex, on_command

from urllib import parse

ARTICLE = r"&#91;&#91;(.*?)&#93;&#93;" #似乎是adapter出于安全原因会把中括号转义
TEMPLATE = r"\{\{(.*?)\}\}"

# TODO:将wiki地址存入配置文件中
WIKIURL = "https://zh.wikipedia.org/wiki/"

wiki = on_regex(ARTICLE)
wiki_template = on_regex(TEMPLATE)

# FIXED:消息被错误转换为转义字符导致无法匹配
@wiki.handle()
async def _wiki(bot: Bot, event: MessageEvent):
    msg = str(event.message).strip()
    title = re.findall(ARTICLE, msg)[0]
    url = WIKIURL + parse.quote(title)

    await bot.send(event, url)

@wiki_template.handle()
async def _wiki_template(bot: Bot, event: MessageEvent):
    msg = str(event.message).strip()
    title = re.findall(TEMPLATE, msg)[0]
    url = WIKIURL + "Template:" +parse.quote(title)

    await bot.send(event, url)
