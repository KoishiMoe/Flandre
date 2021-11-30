from src.utils.config import BotConfig

'''
使用本地帮助时，停止该插件的加载
如有其它更好方式还请不吝赐教
'''
if not BotConfig.use_local_help:
    from . import help_main
