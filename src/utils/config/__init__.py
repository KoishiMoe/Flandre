from datetime import timedelta
from pathlib import Path

from nonebot.log import logger
from yaml import safe_load

from .init_config import Initcfg

CONFIG_PATH = Path(".") / "config.yaml"


def update_config():
    result = Initcfg.update_config(CONFIG_PATH)
    if result == True:
        logger.warning("上次bot更新增加了一些配置项，已将其添加到config.yaml中，请编辑配置文件后重新启动bot")
        exit(0)
    else:
        logger.error(result)
        exit(1)


if not CONFIG_PATH.is_file():
    result = Initcfg.new_config(CONFIG_PATH)
    if result == True:  # 因为result总是非空，故加==True
        logger.warning("未找到配置文件，已在bot所在目录生成config.yaml,请参考文档进行修改后再次启动bot")
        exit(0)
    else:
        logger.error(result)
        exit(1)

try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = safe_load(f)
        if not Initcfg.check_config(config):
            update_config()

except PermissionError as e:
    logger.error("读取配置文件（config.yaml）失败：权限不足")
    exit(1)
except Exception as e:
    logger.error(f"读取配置文件失败：未知错误：\n{e}"
                 "\n这可能是配置文件格式错误导致的，请参考yaml规范进行修改，或者删除配置文件以让bot重新创建")
    exit(1)

try:
    if not config:  # 空配置文件
        result = Initcfg.new_config(CONFIG_PATH)
        if result == True:  # 因为result总是非空，故加==True
            logger.warning("配置文件为空，已重新初始化config.yaml,请参考文档进行修改后再次启动bot")
            exit(0)
        else:
            logger.error(result)
            exit(1)


    class BotConfig:
        config: dict = config["BotConfig"]

        port: int = int((config.get("port", 8080)))
        debug: bool = bool(config.get("debug", False))
        superusers: set = set(config.get("superusers", []))
        nickname: set = set(config.get("nickname", ["芙兰", "芙兰朵露", "芙兰朵露·斯卡蕾特"]))
        command_start: set = set(config.get("command_prefix", ["", "/"]))
        command_sep: set = set(config.get("command_sep", ["."]))
        session_expire_timeout: timedelta = timedelta(seconds=config.get("session_expire_timeout", 60))
        log_level: int = int(config.get("log_level", 0))
        use_local_help: bool = bool(config.get("use_local_help", False))


    class WithdrawConfig:
        config: dict = config["WithdrawConfig"]

        max_withdraw_num: int = int(config.get("max_withdraw_num", 50))


    class PixivConfig:
        config: dict = config["Pixiv"]

        max_pic_num: int = int(config.get("max_pic_num", 20))
        use_forward_msg: bool = bool(config.get("use_forward_msg", True))
        token: str = str(config.get("token", ''))
        enable_tag_filter: bool = bool(config.get("enable_tag_filter", True))
        disable_fallback: bool = bool(config.get("disable_fallback", False))
        blocked_tags: set = set(config.get("blocked_tags", {"R18", }))
        proxy: str = str(config.get("proxy", ''))

    class b23Config:
        config: dict = config["b23Extract"]

        sessdata: str = str(config.get("sessdata", ""))
        bili_jct: str = str(config.get("bili_jct", ""))
        buvid3: str = str(config.get("buvid3", ""))
        proxy: str = str(config.get("http_proxy", ""))

except (KeyError, AttributeError) as e:
    update_config()
except (ValueError, TypeError) as e:
    logger.error("配置文件（config.yaml）参数非法！请参考文档进行正确的配置，或者删除配置文件以让bot重新创建")
    exit(1)
except Exception as e:
    logger.error(f"读取配置文件（config.yaml）时发生了未知错误:\n{e}")
    exit(1)

RUNTIME_CONFIG = {
    "port": BotConfig.port,
    "debug": BotConfig.debug,
    "superusers": BotConfig.superusers,
    "nickname": BotConfig.nickname,
    "command_start": BotConfig.command_start,
    "command_sep": BotConfig.command_sep,
    "session_expire_timeout": BotConfig.session_expire_timeout,
    "log_level": BotConfig.log_level,
    "use_local_help": BotConfig.use_local_help,
}
