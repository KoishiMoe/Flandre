from datetime import timedelta
from pathlib import Path

from nonebot.log import logger
from ruamel.yaml import safe_load
import sys

from .update import Update

CONFIG_PATH = Path(".") / "config.yaml"
DEFAULT_CONFIG_PATH = Path(".") / "config_default.yaml"


Update.check_config()

try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = safe_load(f)

except PermissionError as e:
    logger.error("读取配置文件（config.yaml）失败：权限不足")
    sys.exit(1)
except Exception as e:
    logger.error(f"读取配置文件失败：未知错误：\n{e}"
                 "\n这可能是配置文件格式错误导致的，请参考yaml规范进行修改，或者删除配置文件以让bot重新创建")
    sys.exit(1)

try:
    if not config:  # 空配置文件
        logger.error("如果你看到这条提示，意味着bot无法读取默认配置文件，并且你当前的配置文件内容为空。\n"
                     "如果上述属实，请删除空白的配置文件后再次启动\n"
                     "如果你认为这是一个错误，请收集相关信息后提交issue")
        sys.exit(1)


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

    class B23Config:
        config: dict = config["b23Extract"]

        sessdata: str = str(config.get("sessdata", ""))
        bili_jct: str = str(config.get("bili_jct", ""))
        buvid3: str = str(config.get("buvid3", ""))
        proxy: str = str(config.get("http_proxy", ""))
        use_image: str = str(config.get("use_image", 'auto'))

    class AntiMiniapp:
        config: dict = config["anti_miniapp"]

        ignored_keywords: list = list(config['ignored_keywords'])

except (KeyError, AttributeError) as e:
    Update.check_config()
except (ValueError, TypeError) as e:
    logger.error("配置文件（config.yaml）参数非法！请参考文档进行正确的配置，或者删除配置文件以让bot重新创建")
    sys.exit(1)
except Exception as e:
    logger.error(f"读取配置文件（config.yaml）时发生了未知错误:\n{e}")
    sys.exit(1)

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
