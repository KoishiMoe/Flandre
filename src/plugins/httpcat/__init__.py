from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment, Message
from nonebot.params import RawCommand
from nonebot.plugin import require

# 接入帮助系统
__usage__ = 'http.cat： httpcat [http状态码]\n' \
            '注意状态码仅支持标准RFC'

__help_version__ = '0.0.1 (Flandre)'

__help_plugin_name__ = 'httpcat'

# 接入服务管理器
require("service")
from ..service.admin import register
from ..service.rule import online

# 接入频率限制
require("ratelimit")
from ..ratelimit.config_manager import register as register_ratelimit
from ..ratelimit.rule import check_limit

register_ratelimit("httpcat", "http状态码猫猫图")

register("httpcat", "获取Http状态码猫猫图")

# 接入禁言检查
require("utils")
from ..utils.gag import not_gagged as gag

http_cat = on_command("httpcat", rule=online("httpcat") & gag())


@http_cat.handle()
async def _http_cat(bot: Bot, event: MessageEvent, raw_command: str = RawCommand()):
    if not await check_limit(bot, event, "httpcat"):
        await http_cat.finish("哒咩，请节制吸猫哦(☆-ｖ-)")
    msg = str(event.message).strip().removeprefix(raw_command).strip()
    if msg.isnumeric() and len(msg) == 3:
        image = MessageSegment.image(f'https://http.cat/{msg}')
        await bot.send(event, message=Message(image))
