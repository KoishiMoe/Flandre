import re

from nonebot import on_regex
from nonebot.adapters.cqhttp import Bot, utils, GroupMessageEvent
from nonebot.adapters.cqhttp.permission import GROUP

from . import config_manager
from .config import Config
from .config import NoDefaultPrefixException, NoSuchPrefixException
from .data_source import Wiki

ARTICLE_RAW = r"&#91;&#91;(.*?)&#93;&#93;"  # 似乎是adapter出于安全原因会把中括号转义
ARTICLE = r"\[\[(.*?)\]\]"
TEMPLATE = r"\{\{(.*?)\}\}"
RAW = r"\(\((.*?)\)\)"

# DONE：将wiki地址存入配置文件中
# WIKIURL = "https://zh.wikipedia.org/wiki/"
# WIKIAPI = "https://zh.wikipedia.org/w/api.php"

wiki = on_regex(ARTICLE_RAW, permission=GROUP)
wiki_template = on_regex(TEMPLATE, permission=GROUP)
wiki_raw = on_regex(RAW, permission=GROUP)


# FIXED:消息被错误转换为转义字符导致无法匹配
@wiki.handle()
async def _wiki(bot: Bot, event: GroupMessageEvent):
    msg = str(event.message).strip()
    msg = utils.unescape(msg)  # 将消息处理为正常格式，以防搜索出错
    temp_config: Config = Config(event.group_id)
    titles = re.findall(ARTICLE, msg)
    for title in titles:
        title = str(title)
        prefix = re.match('\w+:|\w+：', title)
        if not prefix:
            prefix = ''
        else:
            prefix = prefix.group(0).lower().rstrip(":：")
            if prefix in temp_config.prefixes:
                title = re.sub(prefix + ":|：", '', title, count=1, flags=re.I)
            else:
                prefix = ''
        try:
            wikiapi = temp_config.get_from_prefix(prefix)[0]
            wikiurl = temp_config.get_from_prefix(prefix)[1]

            wiki = Wiki(wikiapi, wikiurl)
            url = await wiki.get_from_api(title, False)

            await bot.send(event, url)
        except NoDefaultPrefixException as e:
            await bot.send(event, message="没有找到默认前缀，请群管或bot管理员先设置默认前缀")
        except NoSuchPrefixException as e:
            await bot.send(event, message="指定的默认前缀对应的wiki不存在，请管理员检查设置")


@wiki_template.handle()
async def _wiki_template(bot: Bot, event: GroupMessageEvent):
    msg = str(event.message).strip()
    msg = utils.unescape(msg)  # 将消息处理为正常格式，以防搜索出错
    temp_config: Config = Config(event.group_id)
    titles = re.findall(ARTICLE, msg)
    for title in titles:
        title = str(title)
        prefix = re.match('\w+:|\w+：', title)
        if not prefix:
            prefix = ''
        else:
            prefix = prefix.group(0).lower().rstrip(":：")
            if prefix in temp_config.prefixes:
                title = re.sub(prefix + ":|：", '', title, count=1, flags=re.I)
            else:
                prefix = ''
        try:
            wikiapi = temp_config.get_from_prefix(prefix)[0]
            wikiurl = temp_config.get_from_prefix(prefix)[1]

            wiki = Wiki(wikiapi, wikiurl)
            url = await wiki.get_from_api(title, True)

            await bot.send(event, url)
        except NoDefaultPrefixException as e:
            await bot.send("没有找到默认前缀，请群管或bot管理员先设置默认前缀")
        except NoSuchPrefixException as e:
            await bot.send("指定的默认前缀对应的wiki不存在，请管理员检查设置")


@wiki_raw.handle()
async def _wiki_raw(bot: Bot, event: GroupMessageEvent):
    msg = str(event.message).strip()
    msg = utils.unescape(msg)  # 将消息处理为正常格式，以防搜索出错
    temp_config: Config = Config(event.group_id)
    titles = re.findall(ARTICLE, msg)
    for title in titles:
        title = str(title)
        prefix = re.match('\w+:|\w+：', title)
        if not prefix:
            prefix = ''
        else:
            prefix = prefix.group(0).lower().rstrip(":：")
            if prefix in temp_config.prefixes:
                title = re.sub(prefix + ":|：", '', title, count=1, flags=re.I)
            else:
                prefix = ''
        try:
            wikiapi = temp_config.get_from_prefix(prefix)[0]
            wikiurl = temp_config.get_from_prefix(prefix)[1]

            wiki = Wiki(wikiapi, wikiurl)
            url = await wiki.url_parse(title)

            await bot.send(event, url)
        except NoDefaultPrefixException as e:
            await bot.send("没有找到默认前缀，请群管或bot管理员先设置默认前缀")
        except NoSuchPrefixException as e:
            await bot.send("指定的默认前缀对应的wiki不存在，请管理员检查设置")
