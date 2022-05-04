from nonebot import Bot
from nonebot.adapters.onebot.v11 import Event
from nonebot.adapters.onebot.v11.permission import GROUP, PRIVATE
from nonebot.plugin import export
from nonebot.rule import Rule

from .query import get_status


@export()
def online(service: str) -> Rule:
    async def _is_online(bot: Bot, event: Event) -> bool:
        if not (
            await get_status("*", "global")
            and await get_status(service, "global")
        ):
            return False
        try:
            if await GROUP(bot, event):
                # 群消息类事件比较多，考虑后续兼容性问题，这里用权限检测
                if not (
                    await get_status(service, "g*")
                    and await get_status("*", "g" + str(event.group_id))
                    and await get_status(service, "g" + str(event.group_id))
                    and await get_status("*", f"g{str(event.group_id)}u{str(event.get_user_id())}")
                    and await get_status(service, f"g{str(event.group_id)}u{str(event.get_user_id())}")
                ):
                    return False
            elif await PRIVATE(bot, event) and not await get_status(service, "u*"):
                return False

            return (
                    await get_status(service, "u" + str(event.get_user_id()))
                    and await get_status("*", "u" + str(event.get_user_id()))
            )
        except ValueError:
            return False  # 事件没有上下文时，获取user_id可能会抛出ValueError

    return Rule(_is_online)
