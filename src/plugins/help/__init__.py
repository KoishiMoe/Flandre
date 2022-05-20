"""
Nonebot 2 Help Plugin
Author: XZhouQD
Since: 16 May 2021
"""
from pathlib import Path

import nonebot

from .handler import helper

# 接入服务管理器
nonebot.plugin.require("service")
from ..service.admin import register

register("help", "帮助")


default_start = list(nonebot.get_driver().config.command_start)[0]

# store all subplugins
_sub_plugins = set()
# load sub plugins
_sub_plugins |= nonebot.load_plugins(
    str((Path(__file__).parent / "plugins").resolve()))

__usage__ = f'''欢迎使用Nonebot 2 Help Plugin
本插件提供公共帮助菜单能力
此Bot配置的命令前缀：{" ".join(list(nonebot.get_driver().config.command_start))}
'''

__help_version__ = '0.2.2 (Flandre)'

__help_plugin_name__ = "帮助"
