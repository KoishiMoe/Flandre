from pathlib import Path
from datetime import timedelta
from yaml import safe_load, YAMLError

from .init_config import Initcfg

CONFIG_PATH = Path(".") / "config.yaml"

if not CONFIG_PATH.is_file():
    result = Initcfg.new_config(CONFIG_PATH)
    if result == True:  # 因为result总是非空，故加==True
        print("未找到配置文件，已在bot所在目录生成config.yaml,请参考文档进行修改后再次启动bot")
        exit(0)
    else:
        print(result)
        exit(1)

try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = safe_load(f)
except PermissionError as e:
    print("读取配置文件（config.yaml）失败：权限不足")
    exit(1)
except Exception as e:
    print(f"读取配置文件失败：未知错误：\n{e}"
          "\n这可能是配置文件格式错误导致的，请参考yaml规范进行修改，或者删除配置文件以让bot重新创建")
    exit(1)

try:
    if not config:  # 空配置文件
        result = Initcfg.new_config(CONFIG_PATH)
        if result == True:  # 因为result总是非空，故加==True
            print("配置文件为空，已重新初始化config.yaml,请参考文档进行修改后再次启动bot")
            exit(0)
        else:
            print(result)
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


    class WithdrawConfig:
        config: dict = config["WithdrawConfig"]

        max_withdraw_num: int = int((config.get("max_withdraw_num", 50)))

except (KeyError, AttributeError) as e:
    result = Initcfg.update_config(CONFIG_PATH)
    if result == True:
        print("上次bot更新增加了一些配置项，已将其添加到config.yaml中，请编辑配置文件后重新启动bot")
        exit(0)
    else:
        print(result)
        exit(1)
except (ValueError, TypeError) as e:
    print("配置文件（config.yaml）参数非法！请参考文档进行正确的配置，或者删除配置文件以让bot重新创建")
    exit(1)
except Exception as e:
    print(f"读取配置文件（config.yaml）时发生了未知错误:\n{e}")
    exit(1)

RUNTIME_CONFIG = {
    "port": BotConfig.port,
    "debug": BotConfig.debug,
    "superusers": BotConfig.superusers,
    "nickname": BotConfig.nickname,
    "command_start": BotConfig.command_start,
    "command_sep": BotConfig.command_sep,
    "session_expire_timeout": BotConfig.session_expire_timeout,
}
