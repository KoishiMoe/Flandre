from time import time

from nonebot import on_notice, get_driver
from nonebot.adapters.onebot.v11 import Bot, Event, GroupBanNoticeEvent
from nonebot.adapters.onebot.v11.permission import GROUP
from nonebot.log import logger
from nonebot.rule import Rule

from src.utils.config import BotConfig

record = {}

driver = get_driver()


@driver.on_bot_connect
async def _check_existing_gag(bot: Bot):
    global record

    groups: list[dict] = []
    for i in range(3):
        try:
            groups = await bot.get_group_list()
            break
        except Exception as e:
            logger.warning(f"获取群列表出错，正在重试（{i + 1}/3）……\n错误信息：{e}")

    if not groups:
        return

    record = {}
    for group in groups:
        gid = group.get("group_id")
        if gid:
            try:
                bot_info = await bot.get_group_member_info(group_id=gid, user_id=int(bot.self_id))
                t = time()
                if bot_info.get("shut_up_timestamp"):
                    record[gid] = {
                        "time": t,
                        "duration": bot_info["shut_up_timestamp"] - t,
                    }
            except Exception as e:
                logger.warning(f"获取群{group}的禁言状态时发生了错误：{e}")


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
