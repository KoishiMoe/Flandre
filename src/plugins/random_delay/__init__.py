import asyncio
from typing import Dict, Any
from random import randint

from nonebot.adapters.onebot.v11 import Bot

from src.utils.config import RandomDelay

# 接入帮助系统
__usage__ = '本插件无任何用户交互，仅根据配置文件中定义的时间为对话增加随机延迟'

__help_version__ = '0.0.1 (Flandre)'

__help_plugin_name__ = '随机延迟'


@Bot.on_calling_api
async def random_delay(bot: Bot, api: str, data: Dict[str, Any]):
    if api in ("send_msg", "send_private_msg", "send_group_msg"):
        await asyncio.sleep(randint(RandomDelay.min_time, RandomDelay.max_time))
