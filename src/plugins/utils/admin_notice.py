import asyncio

from nonebot import on_notice
from nonebot.adapters.onebot.v11 import Bot, GroupAdminNoticeEvent
from nonebot.log import logger

from src.utils.config import BotConfig, UtilsConfig

set_admin = on_notice()


@set_admin.handle()
async def _set_admin(bot: Bot, event: GroupAdminNoticeEvent):
    if not event.self_id == event.user_id:
        return
    is_set = event.sub_type == "set"
    logger.info(f"Bot在群 {event.group_id} 被{'设为' if is_set else '取消'}了管理员")

    if UtilsConfig.admin:
        msg = f"报告主人，{'我成为了群' if is_set else '我在群'} {event.group_id} " \
              f"{'的管理员<(￣ˇ￣)/' if is_set else '被取消了管理员权限(。﹏。)'}"
        for su in BotConfig.superusers:
            await bot.send_private_msg(user_id=int(su), message=msg)
            await asyncio.sleep(1)
