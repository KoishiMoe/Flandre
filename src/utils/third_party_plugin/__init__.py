"""
初始化为第三方插件准备的配置文件和目录
"""
import os
from json import dumps, loads
from pathlib import Path

__all__ = ["init_3rd_plugin"]

EMPTY_FILE = {
  "plugins": [],
  "plugin_dirs": ["src/third_party_plugins"],
}

FILE_PATH = Path("plugins.json")
PLUGIN_DIR = Path(".") / "src" / "third_party_plugins"


def init_3rd_plugin() -> bool:
    if not FILE_PATH.is_file():
        with open(FILE_PATH, "w", encoding='utf-8') as w:
            w.write(dumps(EMPTY_FILE, indent=4))
    os.makedirs(PLUGIN_DIR, exist_ok=True)

    plugins: dict = loads(FILE_PATH.read_bytes())
    plugin_list = plugins.get("plugins")
    plugin_dir = plugins.get("plugin_dirs")

    for i in plugin_list:
        if i:
            return True
    for i in plugin_dir:
        path = Path(i)
        if path.exists() and os.listdir(path):
            return True

    return False
