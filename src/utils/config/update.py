import sys
import shutil
from pathlib import Path

from nonebot.log import logger
from ruamel.yaml import round_trip_load, round_trip_dump

CONFIG_PATH = Path(".") / "config.yaml"
DEFAULT_CONFIG_PATH = Path(".") / "config_default.yaml"
BACKUP_CONFIG_PATH = Path(".") / "config.yaml.bak"

class Update:
    @staticmethod
    def check_config():
        if not CONFIG_PATH.is_file():
            Update.init_config()


        if not DEFAULT_CONFIG_PATH.is_file():
            logger.error("配置文件更新检查失败：无法读取默认配置文件(config_default.yaml)，该文件可能已被删除或改名。"
                         "bot将跳过配置文件更新检测，如果后续出现配置相关报错，请手动更新配置文件")
            return

        try:
            with (
                open(CONFIG_PATH, 'r', encoding='utf-8') as f1,
                open(DEFAULT_CONFIG_PATH, 'r', encoding='utf-8') as f2,
            ):
                current_config = round_trip_load(f1)
                default_config = round_trip_load(f2)
        except PermissionError as e:
            logger.error("读取配置文件失败：权限不足")
            sys.exit(1)
        except Exception as e:
            logger.error(f"读取配置文件失败：未知错误：\n{e}"
                         "\n这可能是配置文件格式错误导致的，请参考yaml规范进行修改，或者删除配置文件以让bot重新创建")
            sys.exit(1)

        if not current_config or current_config.get("__version__", 0) < default_config["__version__"]:
            # 第一个检测空文件，第二个是以防current_config中不存在版本号（即旧版本配置文件）
            Update.update_config()

    @staticmethod
    def update_config() :
        try:
            shutil.copyfile(CONFIG_PATH, BACKUP_CONFIG_PATH)
            logger.info("已将原始配置文件备份到config.yaml.bak")
        except IOError as e:
            logger.error(f"备份配置文件失败:IO错误，请检查是否有足够权限\n{e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"备份配置文件失败:未知错误\n{e}")
            sys.exit(1)

        try:
            with (
                open(CONFIG_PATH, 'r', encoding='utf-8') as f1,
                open(DEFAULT_CONFIG_PATH, 'r', encoding='utf-8') as f2,
            ):
                old_config = round_trip_load(f1)
                new_config = round_trip_load(f2)
        except PermissionError as e:
            logger.error("读取配置文件失败：权限不足")
            sys.exit(1)
        except Exception as e:
            logger.error(f"读取配置文件失败：未知错误：\n{e}")  # 如果只是格式出错，check_config应该就过不去
            sys.exit(1)

        for i in new_config.keys():
            if isinstance(new_config[i], dict):  # 考虑到版本号不是字典
                if i in old_config.keys():
                    for j in new_config[i].keys():
                        if j in old_config[i].keys():
                            new_config[i][j] = old_config[i][j]

        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                f.write(round_trip_dump(new_config).replace('null', '').
                        replace("      ", ''))  # ruamel.yaml会莫名其妙添加空格……原因未知
            logger.warning("已更新config.yaml，请编辑配置文件后重新启动bot")
            sys.exit(0)
        except PermissionError as e:
            return "更新配置文件错误：没有写权限"
        except Exception as e:
            return f"更新配置文件错误：未知错误\n{e}"

    @staticmethod
    def init_config():
        if not DEFAULT_CONFIG_PATH.is_file():
            logger.error("初始化配置文件失败：未找到默认配置文件")
            sys.exit(1)
        try:
            shutil.copyfile(DEFAULT_CONFIG_PATH, CONFIG_PATH)
            logger.warning("未找到配置文件，已在bot所在目录生成config.yaml,请参考文档进行修改后再次启动bot")
            sys.exit(0)
        except IOError as e:
            logger.error(f"备份配置文件失败:IO错误，请检查是否有足够权限\n{e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"备份配置文件失败:未知错误\n{e}")
            sys.exit(1)
