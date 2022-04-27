from . import sqlite
from . import admin
from . import rule

# 接入帮助系统
__usage__ = """
            私聊（仅超管）：
            查询：service [-u 用户帐号] [-g 群号]
            其中帐号和群号是可选的，都不提供时输出全部服务的全局开启情况，提供帐号时输出对该用户的开启情况，提供群时输出该群的开启情况，都提供时显示该用户在该群的服务访问权限
            修改：enable/disable 服务名 [-u 用户帐号] [-g 群号]
            enable：启用，disable：禁用，服务名：service命令查询到的服务名（英文），其他参数同上
            群聊（群管/超管）：
            查询：service [-u 用户帐号]
            不提供用户时输出该群和全局的插件开启情况，提供用户时显示该用户在本群的访问权限。不要提供-g参数，会被忽略
            修改：enable/disable 服务名 [-u 用户帐号]
            同上，只能修改本群全体/某用户（当提供-u参数时）在本群的服务访问权限，-g参数无效
            """

__help_version__ = '0.0.1 (Flandre)'

__help_plugin_name__ = '服务管理器'
