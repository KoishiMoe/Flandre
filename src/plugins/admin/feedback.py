import asyncio

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
from nonebot.params import RawCommand
from nonebot.plugin import require
from nonebot.rule import to_me
from nonebot.typing import T_State

from src.utils.config import BotConfig

# 接入服务管理器
require("service")
from ..service.admin import register
from ..service.rule import online

register("feedback", "反馈")

# 接入禁言检查
require("utils")
from ..utils.gag import not_gagged as gag

# 接入帮助
default_start = list(BotConfig.command_start)[0] if BotConfig.command_start else "/"

# 接入频率限制
require("ratelimit")
from ..ratelimit.config_manager import register as register_ratelimit
from ..ratelimit.rule import check_limit

register_ratelimit("feedback", "反馈")

QUIT_LIST = ["取消", "算了", "退出", "0", "exit"]

feedback = on_command("feedback", aliases={"反馈", "来杯红茶"}, rule=online("feedback") & gag() & to_me())
# 红茶是ATRI那边的叫法，至于为啥是红茶……建议问@Kyomotoi✧(≖ ◡ ≖✿)

feedback.__help_name__ = "feedback"
feedback.__help_info__ = "使用 feedback/反馈/来杯红茶 就可以开始反馈了，可以把内容直接接在命令后面，也可以等bot询问后再说"


@feedback.handle()
async def _feedback(bot: Bot, event: MessageEvent, state: T_State, raw_command: str = RawCommand()):
    if not await check_limit(bot, event, "feedback", False):
        await feedback.finish("反馈太快了，请一次把话说完！（＃￣～￣＃）")
    msg = str(event.message).strip().removeprefix(raw_command).strip()
    if msg:
        state["content"] = msg


@feedback.got("content", "啊啦，你想反馈什么呢，我可以替你转告给主人的哒✧(≖ ◡ ≖✿)\n不小心触发了？回复“退出”即可( *⊙~⊙)")
async def _feedback_send(bot: Bot, event: MessageEvent, state: T_State):
    content = str(state["content"]).strip()
    if content in QUIT_LIST:
        await feedback.finish("好吧……以后有问题再找我哦～")

    await check_limit(bot, event, "feedback", True)
    await bot.send(event, message=r"收到，感谢反馈\(@^０^@)/★")

    report = f"哒！咱收到了来自群{event.group_id}的用户{event.user_id}的一条反馈！\n" if isinstance(event, GroupMessageEvent) \
        else f"哒！咱收到了用户{event.user_id}的反馈～\n"

    report += content
    for su in BotConfig.superusers:
        await bot.send_private_msg(user_id=su, message=report)
        await asyncio.sleep(1)
