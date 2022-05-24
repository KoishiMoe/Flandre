import asyncio
from random import randint

from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER, GROUP_ADMIN
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State
from nonebot.plugin import require

from src.utils.check_at import check_at
from src.utils.command_processor import process_command
from src.utils.config import BotConfig
from .utils import get_global_group, get_groups_in_global_group

# 接入帮助
default_start = list(BotConfig.command_start)[0] if BotConfig.command_start else "/"

mute = on_command("禁言", aliases={"口球", "mute", "gag"}, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                  state={"status": True})
unmute = on_command("解禁", aliases={"解除禁言", "取出口球", "unmute"}, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                    state={"status": False})

# 接入帮助
mute.__help_name__ = "mute"
mute.__help_info__ = "使用 mute/“禁言”\n" \
                    "格式为： 禁言 qq号1 qq号2 [-t 时长（单位：秒，可选，默认为 60~3600 随机）]\n" \
                    "或： mute @user1 @user2 [-t 时长] \n" \
                    "当群加入群组后，这将会在整个群组内禁言该用户"
unmute.__help_name__ = "unmute"
unmute.__help_info__ = "使用 unmute/解禁/解除禁言 \n" \
                       "格式为： 解除禁言 qq号1 qq号2\n" \
                       "同样，如果加入群组后，会在整个群组解禁该用户"


@mute.handle()
@unmute.handle()
async def _ban(bot: Bot, event: GroupMessageEvent, state: T_State, raw_command: str = RawCommand()):
    new_status = state["status"]

    targets = check_at(event.json())
    param_list, param_dict = process_command(raw_command, str(event.message))
    targets += param_list

    target_list: list = \
        [int(usr) for usr in targets if (isinstance(usr, str) and usr.isdigit()) or isinstance(usr, int)]
    # check_at返回的列表里有字符串("all")和数字（用户帐号）；从消息中解出来的目标则应该是字符串形式的数字
    if "all" in targets:
        target_list.append("all")

    mute_time = randint(60, 3600)
    if param_dict.get("t"):
        if not new_status:
            await unmute.finish("解禁操作不应含有参数“t“，请检查输入")
        if isinstance(param_dict["t"], str) and param_dict["t"].isdigit():
            mute_time = int(param_dict["t"])
        else:
            await mute.finish("错误：提供的禁言时间无效")

    if target_list:
        global_group = await get_global_group(event.group_id)

        if global_group:
            groups = await get_groups_in_global_group(global_group)
        else:
            groups = {event.group_id}
        if "all" in target_list:
            failed = []
            for group in groups:
                try:
                    await bot.set_group_whole_ban(group_id=group, enable=new_status)
                    await asyncio.sleep(1)
                except ActionFailed as e:
                    logger.info(f"对群{group}设置全员禁言时发生了错误：{e}")
                    failed += group
            output = f"对{len(groups)}个群设置全员禁言完成"
            if failed:
                output += f"其中有{len(failed)}个群失败，分别是：{'、'.join(failed)}"
            await bot.send(event, output)
        for target in target_list:
            if isinstance(target, int):
                for group in groups:
                    try:
                        await bot.set_group_ban(group_id=group, user_id=target, duration=mute_time if new_status else 0)
                        await asyncio.sleep(1)
                    except ActionFailed as e:
                        logger.info(f"从群{group}中禁言用户{targets}时发生了错误：{e}")
            if new_status:
                await bot.send(event, f"用户禁言操作完成，禁言时长为{mute_time}秒")
            else:
                await bot.send(event, f"用户禁言操作完成")
    else:
        await mute.finish(f"啊啦，你似乎没有提供要{'禁言' if new_status else '解禁'}的对象的说……")


# 接入服务管理器
require("service")
from ..service.admin import register
from ..service.rule import online

register("muteme", "给我口球")

# 接入频率限制
require("ratelimit")
from ..ratelimit.config_manager import register as register_ratelimit
from ..ratelimit.rule import check_limit

register_ratelimit("muteme", "给我口球")

# 接入禁言检查
require("utils")
from ..utils.gag import not_gagged as gag


muteme = on_command("muteme", aliases={"给我口球", "口球自己", "口球我自己", "gagme"}, rule=online("muteme") & gag())

# 接入帮助
muteme.__help_name__ = "muteme"
muteme.__help_info__ = "使用 “给我口球”\n" \
                    "格式为： 给我口球 [时长（单位：秒，可选，默认为 60~3600 随机）]"


@muteme.handle()
async def _muteme(bot: Bot, event: GroupMessageEvent, state: T_State, raw_command: str = RawCommand()):
    param_list, param_dict = process_command(raw_command, str(event.message))

    if not await check_limit(bot, event, "muteme"):
        await muteme.finish("就这么抖M吗……休息一会吧（｀へ´）")

    bot_role = await bot.get_group_member_info(group_id=event.group_id, user_id=event.self_id)
    if not bot_role.get("role") in ("owner", "admin"):
        await muteme.finish("emmmmm，我的权限似乎不够的说……")

    if param_list and param_list[0].isdigit():
        mute_time = int(param_list[0])
    else:
        mute_time = randint(60, 3600)
    state["time"] = mute_time


@muteme.got("sure", "确定要让我口球你吗（y/N），不能反悔呦( ﹁ ﹁ ) ~→")
async def _muteme_sure(bot: Bot, event: GroupMessageEvent, state: T_State):
    sure = str(state["sure"]).strip() in ("Y", "y", "T", "t", "Yes", "yes", "YES", "True", "true", "是", "确定")
    if sure:
        try:
            await bot.set_group_ban(group_id=event.group_id, user_id=event.user_id, duration=state["time"])
        except ActionFailed:
            await muteme.finish(f"emmmm……操作失败了，也许是权限不足？")
        await muteme.finish(f"你已被口球{state['time']}秒")
    else:
        await muteme.finish("OK")
