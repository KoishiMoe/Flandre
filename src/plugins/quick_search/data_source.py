import re
from typing import Optional
from urllib import parse

from nonebot import require
from nonebot.adapters.onebot.v11 import Bot, utils, GroupMessageEvent
from nonebot.matcher import Matcher

from .config import Config

# 接入频率限制
require("ratelimit")
from ..ratelimit.config_manager import register as register_ratelimit
from ..ratelimit.rule import check_limit

register_ratelimit("search", "快速搜索")


async def search_handle(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    msg = str(event.message).strip().lstrip(" ？?")
    msg = utils.unescape(msg)
    cfg: Config = Config(event.group_id)
    try:
        prefix, keyword = re.split(" ", msg, maxsplit=1)
    except ValueError:
        return

    url = cfg.get_url(prefix)
    if url:
        matcher.stop_propagation()

        if not await check_limit(bot, event, "search"):
            await matcher.finish("度娘累了，一会再来吧～")

        await bot.send(event, url_parse(url, keyword))


def url_parse(url: str, keyword: str) -> Optional[str]:
    if url:
        return re.sub(r"%s(?!\w)", parse.quote(keyword), url, count=1)  # 排除后面跟的有其他字母/数字的
