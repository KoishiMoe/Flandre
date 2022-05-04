"""
与群聊使用的ban不同，此处的ban不会导致用户在群聊中被封禁，但是会让bot对目标实行冷暴力(bushi)
"""
import os
from json import dumps, loads
from pathlib import Path
from typing import Callable

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER
from nonebot.plugin import require
from nonebot.rule import to_me
from nonebot.typing import T_State

from src.utils.config import BotConfig
from .utils import check_at

srv_update_status: Callable = require("service").update_status
DATA_DIR = Path(".") / "data" / "database" / "admin"
# 接入帮助
default_start = list(BotConfig.command_start)[0] if BotConfig.command_start else "/"


ban = on_command("banuser", aliases={"bangroup", "banusr", "bangrp", "封禁用户", "封禁群"}, permission=SUPERUSER,
                 state={"is_ban": True}, rule=to_me())
pardon = on_command("pardonuser",
                    aliases={"pardonusr", "pardongroup", "pardongrp", "赦免用户", "解封用户", "赦免群", "解封群"},
                    permission=SUPERUSER, state={"is_ban": False}, rule=to_me())

# 接入帮助
ban.__help_name__ = "superuser_ban"
ban.__help_info__ = "使用 banuser/banusr/“封禁用户”，bangroup/bangrp/“封禁群”\n" \
                    "格式为： 封禁用户 qq号1 qq号2\n" \
                    "或： banuser @user1 @user2 （仅群聊）\n" \
                    "bot将不再响应被封禁者的消息，也会自动拒绝目标发起的加好友/加群申请"
pardon.__help_name__ = "superuser_pardon"
pardon.__help_info__ = "使用 pardonuser/pardonusr/赦免用户/解封用户，pardongroup/pardongrp/赦免群/解封群\n" \
                    "具体语法同封禁"


@ban.handle()
@pardon.handle()
async def _ban(bot: Bot, event: MessageEvent, state: T_State, raw_command: str = RawCommand()):
    is_ban: bool = state["is_ban"]
    if is_ban:
        is_usr = raw_command.endswith(("banuser", "banusr", "封禁用户"))
    else:
        is_usr = raw_command.endswith(("pardonuser", "pardonusr", "赦免用户", "解封用户"))

    target = check_at(event.json())
    target += str(event.message).strip().removeprefix(raw_command).strip().split()

    target_list = [int(usr) for usr in target if (isinstance(usr, str) and usr.isdigit()) or isinstance(usr, int)]
    # check_at返回的列表里有字符串("all")和数字（用户帐号）；从消息中解出来的目标则应该是字符串形式的数字

    if target_list:
        for user in target_list:
            await srv_update_status(service="*", user=f"{'u' if is_usr else 'g'}{user}", state=not is_ban)
        __ban_or_pardon(target_list, is_ban=is_ban, is_group=not is_usr)

        await ban.finish("操作成功！")
    else:
        await ban.finish(f"啊啦，你似乎没有提供要{'封禁' if is_ban else '解封'}的{'用户' if is_usr else '群'}的说……")


def get_banned_users(is_group: bool = False) -> list:
    if not is_group:
        ban_cfg = DATA_DIR / "ban_users.json"
    else:
        ban_cfg = DATA_DIR / "ban_groups.json"

    os.makedirs(DATA_DIR, exist_ok=True)
    if not ban_cfg.is_file():
        with open(ban_cfg, "w", encoding='utf-8') as w:
            w.write(dumps([], indent=4))

    return loads(ban_cfg.read_bytes())


def __ban_or_pardon(users: list, is_ban: bool = True, is_group: bool = False):
    if not is_group:
        ban_cfg = DATA_DIR / "ban_users.json"
    else:
        ban_cfg = DATA_DIR / "ban_groups.json"

    banned = set(get_banned_users(is_group))
    if is_ban:
        for user in users:
            banned.add(str(user))  # 不都整成字符串的话后面查询可能会出问题（有些是整数有些是字符串）
    else:
        for user in users:
            banned.discard(str(user))

    with open(ban_cfg, "w", encoding='utf-8') as w:
        w.write(dumps(list(banned), indent=4))
