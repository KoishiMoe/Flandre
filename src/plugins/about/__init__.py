"""
最水插件，没有之一
"""

from typing import Callable

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.rule import to_me
from nonebot.plugin import require

# 接入帮助系统
__usage__ = '@我 发送“关于”即可'

__help_version__ = '0.0.1 (Flandre)'

__help_plugin_name__ = 'about'

# 接入服务管理器
register: Callable = require("service").register
online: Callable = require("service").online

register("about", "关于")

# 接入频率限制
register_ratelimit: Callable = require("ratelimit").register
limit: Callable = require("ratelimit").limit

register_ratelimit("about", "关于")

# 接入禁言检查
gag: Callable = require("utils").not_gagged


about = on_command("关于", aliases={"about", "协议", "开源", "source", "license", "版权"},
                   rule=to_me() & online("about") & gag() & limit("about"))


@about.handle()
async def _about(bot: Bot, event: MessageEvent):
    msg = "本机器人由 Flandre 强力(bushi)驱动\n" \
          "Flandre 是自由软件，按 GNU AFFERO GENERAL PUBLIC LICENSE Version 3 (AGPLv3) 协议开源，您可以在协议允许的范围内分发和/或修改本软件。\n" \
          "协议全文可以在 https://github.com/KoishiMoe/Flandre/blob/main/LICENSE 查看.\n" \
          "如需获取源代码，请前往 https://github.com/KoishiMoe/Flandre ，喜欢的话也可以去给我点个小星星( *￣▽￣)((≧︶≦*)"
    await about.finish(msg)
