import re

from nonebot import on_regex
from nonebot.plugin import export
from nonebot.adapters.cqhttp import Bot, utils, GroupMessageEvent
from nonebot.adapters.cqhttp.permission import GROUP

from . import config_manager
from .config import Config
from .config import NoDefaultPrefixException, NoSuchPrefixException
from .data_source import Wiki
from .mediawiki import MediaWiki


# 导出获取wiki内容的方法，供帮助插件使用
export().get_wiki = MediaWiki.get_page_content
export().opensearch = MediaWiki.opensearch


'''
用于正则匹配的模板字符串
'''
ARTICLE_RAW = r"&#91;&#91;(.*?)&#93;&#93;"  # 似乎是adapter出于安全原因会把中括号转义，此处用于让事件响应器能正确响应事件
ARTICLE = r"\[\[(.*?)\]\]"
TEMPLATE = r"\{\{(.*?)\}\}"
RAW = r"\(\((.*?)\)\)"

'''
响应器
'''
wiki = on_regex(ARTICLE_RAW, permission=GROUP)
wiki_template = on_regex(TEMPLATE, permission=GROUP)
wiki_raw = on_regex(RAW, permission=GROUP)


@wiki.handle()
async def _wiki(bot: Bot, event: GroupMessageEvent):
    await wiki_parse(ARTICLE, False, False, bot, event)


@wiki_template.handle()
async def _wiki_template(bot: Bot, event: GroupMessageEvent):
    await wiki_parse(TEMPLATE, True, False, bot, event)


@wiki_raw.handle()
async def _wiki_raw(bot: Bot, event: GroupMessageEvent):
    await wiki_parse(RAW, False, True, bot, event)


'''
公用函数
'''


async def wiki_parse(pattern: str, is_template: bool, is_raw: bool, bot: Bot, event: GroupMessageEvent):
    msg = str(event.message).strip()
    msg = utils.unescape(msg)  # 将消息处理为正常格式，以防搜索出错
    temp_config: Config = Config(event.group_id)
    titles = re.findall(pattern, msg)
    for title in titles:
        title = str(title)
        prefix = re.match('\w+:|\w+：', title)
        if not prefix:
            prefix = ''
        else:
            prefix = prefix.group(0).lower().rstrip(":：")  # 删掉右侧冒号以进行匹配
            if prefix in temp_config.prefixes:
                title = re.sub(f"{prefix}:|{prefix}：", '', title, count=1, flags=re.I)  # 去除标题左侧的前缀
            else:
                prefix = ''  # 如果不在前缀列表里，视为名字空间标识，回落到默认前缀
        try:
            if title is None or title.strip() == "":
                continue
            wiki_api = temp_config.get_from_prefix(prefix)[0]
            wiki_url = temp_config.get_from_prefix(prefix)[1]

            wiki = Wiki(wiki_api, wiki_url)
            if not is_raw:
                url = await wiki.get_from_api(title, is_template)
            else:
                url = await wiki.url_parse(title)
            await bot.send(event, url)
        except NoDefaultPrefixException as e:
            await bot.send(event, message="没有找到默认前缀，请群管或bot管理员先设置默认前缀")
        except NoSuchPrefixException as e:
            await bot.send(event, message="指定的默认前缀对应的wiki不存在，请管理员检查设置")
