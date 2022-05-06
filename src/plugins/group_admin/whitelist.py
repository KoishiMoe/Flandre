"""
自动同意申请，以及忽略群名片检查
因为白名单后期经过了一次功能调整，和黑名单不一致的部分基本没有了……所以……现在的白名单模块看起来和黑名单基本一致……
以后（有生之年）重构的时候会合并的（咕咕咕）
"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_OWNER, GROUP_ADMIN
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from src.utils.check_at import check_at
from src.utils.config import BotConfig
from .sqlite import sqlite_pool
from .utils import get_global_group, whitelist_operation, is_group_admin

# 接入帮助

default_start = list(BotConfig.command_start)[0] if BotConfig.command_start else "/"

whitelist = on_command("trust", aliases={"whitelist", "信任", "白名单"}, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                       state={"is_trust": True})
nowhitelist = on_command("distrust", aliases={"nowhitelist", "removewhitelist", "不信任", "移出白名单", "移除白名单"},
                         permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, state={"is_trust": False})

# 接入帮助
whitelist.__help_name__ = "whitelist"
whitelist.__help_info__ = "使用 trust/whitelist/信任/白名单\n" \
                          "格式为： 信任 qq号1 qq号2\n" \
                          "或： trust @user1 @user2 \n" \
                          "bot将自动同意目标在本组内其他群发起的加群申请"
nowhitelist.__help_name__ = "removewhitelist"
nowhitelist.__help_info__ = "使用 distrust/nowhitelist/removewhitelist/不信任/移出白名单\n" \
                            "具体语法同信任"


@whitelist.handle()
@nowhitelist.handle()
async def _whitelist(bot: Bot, event: GroupMessageEvent, state: T_State, raw_command: str = RawCommand()):
    is_trust: bool = state["is_trust"]

    target = check_at(event.json())
    target += str(event.message).strip().removeprefix(raw_command).strip().split()

    target_list = [int(usr) for usr in target if (isinstance(usr, str) and usr.isdigit()) or isinstance(usr, int)]
    # check_at返回的列表里有字符串("all")和数字（用户帐号）；从消息中解出来的目标则应该是字符串形式的数字

    if target_list:
        await whitelist_operation(bot, int(event.group_id), target_list, is_trust)
        await whitelist.finish("操作成功！")
    else:
        await whitelist.finish(f"啊啦，你似乎没有提供要{'加入白名单' if is_trust else '移出白名单'}的用户的说……")


whitelist_list = on_command("whitelistlist", aliases={"trustlist", "白名单列表", "信任列表"},
                            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)


@whitelist_list.handle()
async def _wh_list(bot: Bot, event: GroupMessageEvent):
    global_group = await get_global_group(gid=event.group_id)
    if not global_group:
        gid = event.group_id
    else:
        gid = global_group
    ls = "白名单有：\n"
    for i in await sqlite_pool.fetch_all(
            "select userID from whitelist where whitelist.groupName=:gname",
            {"gname": gid}):
        if i:
            ls += i[0] + "\n"
    await whitelist_list.finish(ls)


async def check_trust(gid: int, uid: int) -> bool:
    # 信任超管
    if str(uid) in BotConfig.superusers or uid in BotConfig.superusers:
        return True
    # 信任管理员
    if await is_group_admin(gid, uid):
        return True
    global_group = await get_global_group(gid)
    if global_group:
        gid = global_group
    # 白名单用户
    return bool(await sqlite_pool.fetch_one("select userID from whitelist where groupName=:gname and userID=:uid",
                                            {"gname": gid, "uid": uid}))
