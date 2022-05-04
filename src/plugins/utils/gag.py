from time import time

from nonebot import on_notice
from nonebot.adapters.onebot.v11 import Bot, Event, GroupBanNoticeEvent
from nonebot.adapters.onebot.v11.permission import GROUP
from nonebot.log import logger
from nonebot.plugin import export
from nonebot.rule import Rule

from src.utils.config import BotConfig

record = {}

gag = on_notice(block=False)


@gag.handle()
async def _gag(bot: Bot, event: GroupBanNoticeEvent):
    if not event.is_tome():
        return

    if event.duration:
        record[event.group_id] = {
            "time": time(),
            "duration": event.duration
        }
        logger.info(f"在群{event.group_id}被{event.operator_id}禁言了{event.duration}秒")

        msg = f"呜……我在{event.group_id}被{event.operator_id}口球了{event.duration}秒……;╥﹏╥;"

    else:
        record.pop(event.group_id, None)
        logger.info(f"在群{event.group_id}被{event.operator_id}解除禁言")

        msg = f"好耶，我在{event.group_id}的口球被{event.operator_id}摘下来了ヾ(^▽^*))) "

    for su in BotConfig.superusers:
        await bot.send_private_msg(user_id=int(su), message=msg)


@export()
def not_gagged() -> Rule:
    async def _not_gagged(bot: Bot, event: Event) -> bool:
        if await GROUP(bot, event) and event.group_id in record.keys():
            gid = event.group_id
            rec = record.get(gid, {})
            if int(time() - rec.get("time", 0)) > rec.get("duration", 0):
                record.pop(gid, None)
                return True
            else:
                return False
        else:
            return True

    return Rule(_not_gagged)
