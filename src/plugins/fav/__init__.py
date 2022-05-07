from typing import Callable

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment
from nonebot.plugin import require
from nonebot.rule import to_me

from src.utils.favorability import FavData

# 接入服务管理器
register: Callable = require("service").register
online: Callable = require("service").online

register("fav", "好感度管理")

# 接入禁言检查
gag: Callable = require("utils").not_gagged

# 接入帮助系统
__usage__ = '查询好感度：@bot 好感度\n' \
            '更多功能，敬请期待～（咕咕咕）'

__help_version__ = '0.0.1 (Flandre)'

__help_plugin_name__ = '好感度管理'

check_favorability = on_command("好感度", rule=to_me() & online("fav") & gag())


@check_favorability.handle()
async def _check_favorability(bot: Bot, event: MessageEvent):
    user = int(event.user_id)
    fav_data = FavData(user)

    await bot.send(event=event, message=MessageSegment.reply(user) + f"你的好感度是{fav_data.favorability}")