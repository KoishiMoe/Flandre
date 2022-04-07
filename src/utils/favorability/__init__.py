import json
import os
from pathlib import Path

from .exceptions import ValueOutOfRangeError

PATH = Path("") / "data" / "database" / "love"
JSON_PATH = PATH / "data.json"


class FavData:
    def __init__(self, uid: int):
        self.__uid = str(uid)
        self.__data = self.__get_data()

    def __get_data(self) -> dict:
        os.makedirs(PATH, exist_ok=True)

        if not JSON_PATH.is_file():
            with open(JSON_PATH, "w", encoding="utf-8") as w:
                w.write(json.dumps({}))

        data: dict = json.loads(JSON_PATH.read_bytes())

        return data

    def __save_data(self):
        with open(JSON_PATH, "w", encoding="utf-8") as w:
            w.write(json.dumps(self.__data, indent=4))

    def update_data(self, new_vaule: int):
        if -100 <= new_vaule <= 100:
            self.__data[self.__uid] = new_vaule
            self.__save_data()
        else:
            raise ValueOutOfRangeError

    @property
    def favorability(self) -> int:
        return self.__data.get(self.__uid, 0)

    def add(self, value: int):
        try:
            self.update_data(self.favorability + value)
        except ValueOutOfRangeError:
            self.update_data(100)

    def reduce(self, value: int):
        try:
            self.update_data(self.favorability - value)
        except ValueOutOfRangeError:
            self.update_data(-100)

    def multiple(self, value: int | float):
        try:
            self.update_data(int(self.favorability * value))
        except ValueOutOfRangeError:
            # 好感度==0 的话应该不会超范围吧……
            if self.favorability * value > 0:
                self.update_data(100)
            else:
                self.update_data(-100)

    def divide(self, value: int | float):
        if value == 0:
            raise ValueError
        else:
            try:
                self.update_data(int(self.favorability / value))
            except ValueOutOfRangeError:
                if self.favorability / value > 0:
                    self.update_data(100)
                else:
                    self.update_data(-100)
