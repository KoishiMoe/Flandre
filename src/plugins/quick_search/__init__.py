import re
from urllib import parse

from nonebot import on_startswith
from nonebot.adapters.onebot.v11 import Bot, utils, GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP

from . import config_manager
from .config import Config

# 接入帮助系统
__usage__ = '使用：\n' \
            '?前缀 关键词\n' \
            '前缀由群管和bot超管配置\n' \
            '配置（带global的是全局命令，仅超管可用）：\n' \
            '快速添加：search.add [搜索引擎名称] [自定义前缀（可选）]' \
            '添加：search.add，search.add.global\n' \
            '删除：search.delete，search.delete.global\n' \
            '列表：search.list，search.list.global'

__help_version__ = '0.1.0 (Flandre)'

__help_plugin_name__ = '快速搜索'

search = on_startswith(("?", "？"), permission=GROUP)


@search.handle()
async def _search(bot: Bot, event: GroupMessageEvent):
    msg = str(event.message).strip().lstrip(" ？?")
    msg = utils.unescape(msg)
    cfg: Config = Config(event.group_id)
    try:
        prefix, keyword = re.split(" ", msg, maxsplit=1)
    except ValueError:
        return

    url = cfg.get_url(prefix)
    if url:
        await bot.send(event, url_parse(url, keyword))


def url_parse(url: str, keyword: str) -> str | None:
    if url:
        return re.sub(r"%s(?!\w)", parse.quote(keyword), url, count=1)  # 排除后面跟的有其他字母/数字的
