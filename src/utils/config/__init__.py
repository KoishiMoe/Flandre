from pathlib import Path
from datetime import timedelta
from yaml import safe_load, safe_dump

CONFIG_PATH = Path(".") / "config.yaml"
DEFAULT_CONFIG = {
    'BotConfig':
        {
            'port': 8080,
            'debug': False,
            'superusers': [""],
            'nickname': ["芙兰", "芙兰朵露", "芙兰朵露·斯卡蕾特", "Flandre"],
            'command_start': ["", "/"],
            'command_sep': ["."],
            'session_expire_timeout': 60,
        },

    'WithdrawConfig':
        {
            'max_withdraw_num': 50,
        },

}
if not CONFIG_PATH.is_file():
    with open(CONFIG_PATH, 'w', encoding='utf-8') as w:
        w.write(safe_dump(DEFAULT_CONFIG).encode('utf-8').decode('unicode-escape'))  # 防止中文被输出为转义字符
    print("未找到配置文件，已在bot所在目录生成config.yaml,请参考文档进行修改后再次启动bot")
    exit(0)
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


class WithdrawConfig:
    config: dict = config["WithdrawConfig"]

    max_withdraw_num: int = int((config.get("max_withdraw_num", 50)))


RUNTIME_CONFIG = {
    "port": BotConfig.port,
    "debug": BotConfig.debug,
    "superusers": BotConfig.superusers,
    "nickname": BotConfig.nickname,
    "command_start": BotConfig.command_start,
    "command_sep": BotConfig.command_sep,
    "session_expire_timeout": BotConfig.session_expire_timeout,
}
