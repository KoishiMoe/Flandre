import re
from urllib import parse

from nonebot import on_regex
from nonebot.plugin import export
from nonebot.adapters.onebot.v11 import Bot, utils, GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP

from . import config_manager
from .config import Config
from .config import NoDefaultPrefixException, NoSuchPrefixException
from .data_source import Wiki
from .mediawiki import MediaWiki

# 接入帮助系统
__usage__ = '使用：\n' \
            '[[前缀:条目名]] {{前缀:模板名}} ((前缀:条目名))\n' \
            '其中中括号、大括号匹配后会调用api搜索条目/模板名，如果有误，可以使用小括号方式绕过api直接生成链接\n' \
            '前缀由群管和bot超管配置，没有指定前缀或前缀无效时，会回落到默认前缀\n' \
            '查看本群wiki列表： @bot wiki列表\n' \
            '配置：\n' \
            '@bot 添加/删除(全局)wiki\n' \
            '@bot 设置(全局)默认wiki\n' \
            '按提示提供相应参数即可\n' \
            '注意：私聊状态下bot仅会响应超管的命令，且仅能管理全局wiki'

__help_version__ = '0.2.5 (Flandre)'

__help_plugin_name__ = 'Wiki推送'

# 导出获取wiki内容的方法，供帮助插件使用
export().get_wiki = MediaWiki.get_page_content
export().opensearch = MediaWiki.opensearch

# 用于正则匹配的模板字符串
ARTICLE_RAW = r"&#91;&#91;(.*?)&#93;&#93;"  # 似乎是adapter出于安全原因会把中括号转义，此处用于让事件响应器能正确响应事件
ARTICLE = r"\[\[(.*?)\]\]"
TEMPLATE = r"\{\{(.*?)\}\}"
RAW = r"\(\((.*?)\)\)"

# 响应器
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


# 公用方法
async def wiki_parse(pattern: str, is_template: bool, is_raw: bool, bot: Bot, event: GroupMessageEvent):
    msg = str(event.message).strip()
    msg = utils.unescape(msg)  # 将消息处理为正常格式，以防搜索出错
    temp_config: Config = Config(event.group_id)
    titles = re.findall(pattern, msg)
    for title in titles:
        title = str(title)
        prefix = re.match(r'\w+:|\w+：', title)
        if not prefix:
            prefix = ''
        else:
            prefix = prefix.group(0).lower().rstrip(":：")  # 删掉右侧冒号以进行匹配
            if prefix in temp_config.prefixes:
                title = re.sub(f"{prefix}:|{prefix}：", '', title, count=1, flags=re.I)  # 去除标题左侧的前缀
            else:
                prefix = ''  # 如果不在前缀列表里，视为名字空间标识，回落到默认前缀

        # 锚点支持
        anchor_list = re.split('#', title, maxsplit=1)
        title = anchor_list[0]
        anchor = f"#{parse.quote(anchor_list[1])}" if len(anchor_list) > 1 else ''

        try:
            if title is None or title.strip() == "":
                continue
            wiki_api = temp_config.get_from_prefix(prefix)[0]
            wiki_url = temp_config.get_from_prefix(prefix)[1]

            wiki_object = Wiki(wiki_api, wiki_url)
            if not is_raw:
                url = await wiki_object.get_from_api(title, is_template, anchor)
            else:
                url = await wiki_object.url_parse(title)
                url = f"标题：{title}\n链接：{url}{anchor}"

            await bot.send(event, url)
        except NoDefaultPrefixException:
            await bot.send(event, message="没有找到默认前缀，请群管或bot管理员先设置默认前缀")
        except NoSuchPrefixException:
            await bot.send(event, message="指定的默认前缀对应的wiki不存在，请管理员检查设置")
