from typing import Callable

from aiohttp import ClientSession, ClientTimeout
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.params import RawCommand
from nonebot.plugin import require
from nonebot.rule import to_me

# 接入帮助系统
__usage__ = '用法：一言 [句子类型（可选）]\n' \
            '句子类型有 a （动画）、b（漫画）、c（游戏）、d（文学）、e（原创）、f（来自网络）、g（其他）、h（影视）、i（诗词）j（网易云）、k（哲学）、l（抖机灵）\n' \
            '感谢 https://developer.hitokoto.cn/ 提供的接口'

__help_version__ = '0.0.1 (Flandre)'

__help_plugin_name__ = 'hitokoto'

# 接入服务管理器
register: Callable = require("service").register
online: Callable = require("service").online

register("hitokoto", "一言")

# 接入频率限制
register_ratelimit: Callable = require("ratelimit").register
check_limit: Callable = require("ratelimit").check_limit

register_ratelimit("hitokoto", "一言")

# 接入禁言检查
gag: Callable = require("utils").not_gagged

API_URL = "https://v1.hitokoto.cn/"

hitokoto = on_command("一言", aliases={"一句", "hitokoto"}, rule=online("hitokoto") & gag() & to_me())


@hitokoto.handle()
async def _hitokito(bot: Bot, event: MessageEvent, raw_command: str = RawCommand()):
    if not await check_limit(bot, event, "hitokoto"):
        await hitokoto.finish("少女祈祷中…")

    params = str(event.message).strip().removeprefix(raw_command).strip()
    if params:
        c_type = "&c=".join(params.split())

    async with ClientSession(timeout=ClientTimeout(1)) as session:
        if params:
            resp = await session.get(f"{API_URL.removesuffix('/')}/?charset=utf-8&c={c_type}")
        else:
            resp = await session.get(f"{API_URL.removesuffix('/')}/?charset=utf-8")

    result: dict = await resp.json()
    output = result.get("hitokoto", "")
    result_from = result.get("from")
    from_who = result.get("from_who")
    if from_who:
        output += " —— " + from_who
    if result_from:
        output += f" （{result_from}）"
    await hitokoto.finish(output)
