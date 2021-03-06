from nonebot import on_startswith
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP
from nonebot.matcher import Matcher
from nonebot.plugin import require

from . import config_manager
from .config import Config
from .data_source import search_handle

# 接入服务管理器
require("service")
from ..service.admin import register
from ..service.rule import online

register("search", "快速搜索")

# 接入禁言检查
require("utils")
from ..utils.gag import not_gagged as gag

# 接入帮助系统
__usage__ = '使用：\n' \
            '?前缀 关键词\n' \
            '前缀由群管和bot超管配置\n' \
            '配置（带global的是全局命令，仅超管可用）：\n' \
            '添加：search.add，search.add.global\n' \
            '删除：search.delete，search.delete.global\n' \
            '列表：search.list，search.list.global'

__help_version__ = '0.2.0 (Flandre)'

__help_plugin_name__ = '快速搜索'

search = on_startswith(("?", "？"), permission=GROUP, rule=online("search") & gag(), block=False)


@search.handle()
async def _search(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    await search_handle(bot, event, matcher)
