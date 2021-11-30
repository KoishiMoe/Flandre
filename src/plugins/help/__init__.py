from pathlib import Path

import nonebot

from src.utils.config import BotConfig

'''
使用本地帮助时，停止该插件的加载
目前采取的是子插件的方式，如有其它更好方式还请不吝赐教
'''
if not BotConfig.use_local_help:
    nonebot.load_plugin(
        str((Path(__file__).parent / "help_wiki").resolve()))
