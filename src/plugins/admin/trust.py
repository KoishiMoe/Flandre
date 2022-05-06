"""
仅仅是自动同意邀请罢了（
"""
import os
from json import dumps, loads
from pathlib import Path

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.params import RawCommand
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot.typing import T_State

from src.utils.check_at import check_at
from src.utils.config import BotConfig

DATA_DIR = Path(".") / "data" / "database" / "admin"
TRUST_CFG = DATA_DIR / "trust_users.json"
# 接入帮助
default_start = list(BotConfig.command_start)[0] if BotConfig.command_start else "/"


trust = on_command("trustuser", aliases={"whitelistuser", "trustusr", "whitelistusr", "信任用户", "白名单用户"},
                   permission=SUPERUSER, state={"is_trust": True}, rule=to_me())
distrust = on_command("distrustuser",
                      aliases={"distrustusr", "nowhitelistuser", "nowhitelistusr", "不信任用户", "移除白名单用户"},
                      permission=SUPERUSER, state={"is_trust": False}, rule=to_me())

# 接入帮助
trust.__help_name__ = "superuser_trust"
trust.__help_info__ = "使用 trustuser/whitelistuser/信任用户/白名单用户\n" \
                    "格式为： 信任用户 qq号1 qq号2\n" \
                    "或： trustuser @user1 @user2 （仅群聊）\n" \
                    "bot将自动同意目标发起的加好友/加群申请（信任优先于拉黑）"
distrust.__help_name__ = "superuser_distrust"
distrust.__help_info__ = "使用 distrustuser/nowhitelistuser/不信任用户/移除白名单用户\n" \
                    "具体语法同信任"


@trust.handle()
@distrust.handle()
async def _trust(bot: Bot, event: MessageEvent, state: T_State, raw_command: str = RawCommand()):
    is_trust: bool = state["is_trust"]

    target = check_at(event.json())
    target += str(event.message).strip().removeprefix(raw_command).strip().split()

    target_list = [int(usr) for usr in target if (isinstance(usr, str) and usr.isdigit()) or isinstance(usr, int)]
    # check_at返回的列表里有字符串("all")和数字（用户帐号）；从消息中解出来的目标则应该是字符串形式的数字

    if target_list:
        __modify_whitelist(target_list, is_whitelist=is_trust)

        await trust.finish("操作成功！")
    else:
        await trust.finish(f"啊啦，你似乎没有提供要{'信任' if is_trust else '解除信任'}的用户的说……")


def get_trusted_users() -> list:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not TRUST_CFG.is_file():
        with open(TRUST_CFG, "w", encoding='utf-8') as w:
            w.write(dumps([], indent=4))

    return loads(TRUST_CFG.read_bytes())


def __modify_whitelist(users: list, is_whitelist: bool = True):
    trusted = set(get_trusted_users())
    if is_whitelist:
        for user in users:
            trusted.add(str(user))  # 不都整成字符串的话后面查询可能会出问题（有些是整数有些是字符串）
    else:
        for user in users:
            trusted.discard(str(user))

    with open(TRUST_CFG, "w", encoding='utf-8') as w:
        w.write(dumps(list(trusted), indent=4))
