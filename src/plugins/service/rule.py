from nonebot import Bot
from nonebot.adapters.onebot.v11 import Event
from nonebot.adapters.onebot.v11.permission import GROUP
from nonebot.plugin import export
from nonebot.rule import Rule

from .query import get_status


@export()
def online(service: str) -> Rule:
    async def _is_online(bot: Bot, event: Event) -> bool:
        enabled = await get_status(service, "global")
        if not enabled:
            return False
        if await GROUP(bot, event):
            # 群消息类事件比较多，考虑后续兼容性问题，这里用权限检测
            enabled = await get_status(service, "g" + str(event.group_id))
            if not enabled:
                return False
            enabled = await get_status(service, f"g{str(event.group_id)}u{str(event.get_user_id())}")
            if not enabled:
                return False
        enabled = await get_status(service, "u" + str(event.get_user_id()))
        return enabled

    return Rule(_is_online)
