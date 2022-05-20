from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment
from nonebot.plugin import require
from nonebot.rule import to_me

from src.utils.favorability import FavData

# 接入服务管理器
require("service")
from ..service.admin import register
from ..service.rule import online

register("fav", "好感度管理")

# 接入禁言检查
require("utils")
from ..utils.gag import not_gagged as gag

# 接入频率限制
require("ratelimit")
from ..ratelimit.config_manager import register as register_ratelimit
from ..ratelimit.rule import check_limit

register_ratelimit("fav", "好感度管理")

# 接入帮助系统
__usage__ = '查询好感度：@bot 好感度\n' \
            '更多功能，敬请期待～（咕咕咕）'

__help_version__ = '0.0.1 (Flandre)'

__help_plugin_name__ = '好感度管理'

check_favorability = on_command("好感度", rule=to_me() & online("fav") & gag())


@check_favorability.handle()
async def _check_favorability(bot: Bot, event: MessageEvent):
    if not await check_limit(bot, event, "fav"):
        await check_favorability.finish("啊啦，这么想知道我对你怎么想吗，就不告诉你ᕕ( ᐛ )ᕗ")
    user = int(event.user_id)
    fav_data = FavData(user)

    await bot.send(event=event, message=MessageSegment.reply(user) + f"你的好感度是{fav_data.favorability}")
