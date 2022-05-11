import asyncio

from nonebot import on_notice
from nonebot.adapters.onebot.v11 import Bot, NoticeEvent
from nonebot.log import logger
from nonebot.matcher import Matcher

from src.utils.config import BotConfig, UtilsConfig

login = on_notice()


@login.handle()
async def _login(bot: Bot, event: NoticeEvent, matcher: Matcher):
    if not event.notice_type == "client_status":
        return
    else:
        matcher.stop_propagation()
    is_login = event.online
    device = event.client
    device_kind = device.get("device_kind")
    device_name = device.get("device_name")

    logger.info(f"Bot在 {device_kind} 设备 {device_name} {'登入' if is_login else '登出'}")

    if UtilsConfig.login:
        msg = f"报告主人，检测到我的帐号在 {device_kind} 设备 {device_name} 上{'登入' if is_login else '登出'}了。" \
              f"如果这不是主人的操作的话，也许是时候给我的帐号换个密码了……"
        for su in BotConfig.superusers:
            await bot.send_private_msg(user_id=int(su), message=msg)
            await asyncio.sleep(1)
