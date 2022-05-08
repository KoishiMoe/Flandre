import json
import os
from pathlib import Path

MC_DIR = Path(".") / "data" / "database" / "mcstatus"


class Config:
    def __init__(self, group_id: int):
        self.__gid = group_id
        self.__config: dict = self.__get_config()
        self.__servers: dict = self.__config["servers"]
        self.__default: str = self.__config["default"]

    def add_server(self, name: str, address: str, port: int = 25565, is_be: bool = False) -> bool:
        if name in self.__servers.keys():
            return False
        self.__servers[name] = {
            "address": address,
            "port": port,
            'is_be': is_be,
        }
        if not self.__default:
            self.__config["default"] = name
            self.__default = name
        return self._save_data()

    def del_server(self, name: str) -> bool:
        if self.__default == name:
            self.__config["default"] = ""
            self.__default = ""
        return self.__servers.pop(name, False) and self._save_data()

    def __get_config(self) -> dict:
        file_name = f'{self.__gid}.json'
        path = MC_DIR / file_name

        os.makedirs(MC_DIR, exist_ok=True)
        if not path.is_file():
            with open(path, "w", encoding="utf-8") as w:
                w.write(json.dumps({
                    "default": "",
                    "servers": {}},
                    indent=4
                ))
        data = json.loads(path.read_bytes())

        return data

    def _save_data(self) -> bool:
        file_name = f'{self.__gid}.json'
        data: dict = self.__config

        path = MC_DIR / file_name
        with open(path, "w", encoding="utf-8") as w:
            w.write(json.dumps(data, indent=4))
        return True

    def get_server(self, prefix: str = None) -> dict | None:
        if not prefix:
            return self.__servers.get(self.__default)
        return self.__servers.get(prefix)

    def list_data(self) -> str:
        count: int = 0
        temp_list = f"默认：{self.__default}\n"

        for k, v in self.__servers.items():
            count += 1
            temp_list += f"{count}.名称：{k}\n" \
                         f"地址：{v['address']}:{v['port']}  {'基岩版' if v['is_be'] else 'Java版'}\n"

        return temp_list

    def set_default(self, name: str) -> bool:
        if name in self.__servers:
            self.__config["default"] = name
            self.__default = name
            return self._save_data()
        return False

    @property
    def servers(self) -> set:
        servers = set(self.__servers.keys())
        return servers
