from pathlib import Path
from datetime import timedelta
from yaml import safe_load

CONFIG_PATH = Path(".") / "config.yaml"
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = safe_load(f)


class BotConfig:
    config: dict = config["BotConfig"]

    port: int = int((config.get("port", 8080)))
    debug: bool = bool(config.get("debug", False))
    superusers: set = set(config.get("superusers", []))
    nickname: set = set(config.get("nickname", ["芙兰", "芙兰朵露", "芙兰朵露·斯卡蕾特"]))
    command_start: set = set(config.get("command_prefix", ["", "/"]))
    command_sep: set = set(config.get("command_sep", ["."]))
    session_expire_timeout: timedelta = timedelta(seconds=config.get("session_expire_timeout", 60))


RUNTIME_CONFIG = {
    "port": BotConfig.port,
    "debug": BotConfig.debug,
    "superusers": BotConfig.superusers,
    "nickname": BotConfig.nickname,
    "command_start": BotConfig.command_start,
    "command_sep": BotConfig.command_sep,
    "session_expire_timeout": BotConfig.session_expire_timeout,
}
