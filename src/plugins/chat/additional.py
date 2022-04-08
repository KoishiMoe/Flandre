"""
附加选项处理
"""
from datetime import date

from src.utils.favorability import FavData
from .exceptions import UnknownOperationError

record = {
    "date": date.today(),
    "users": {}
}


class FavPostProcessOperator:
    def __init__(self, uid: int):
        self.uid = uid
        self.data = FavData(uid=uid)

    def execute(self, operation: dict):
        if self.__check_time_restriction(operation):
            match operation["type"]:
                case "+" | "add":
                    self.data.add(operation["num"])
                case "-" | "reduce":
                    self.data.reduce(operation["num"])
                case "*" | "multiple":
                    self.data.multiple(operation["num"])
                case "/" | "divide":
                    self.data.divide(operation["num"])
                case _:
                    raise UnknownOperationError(f"Unknown operation: {operation['type']}")

    def __check_time_restriction(self, operation: dict) -> bool:
        if record["date"] != date.today():
            self.record = {
                "date": date.today(),
                "users": {}
            }
            return True

        user_record = record["users"]
        current_user = user_record.get(self.uid, {})
        user_record[self.uid] = current_user  # 防止后面因为user_record[self.uid]不存在造成keyerror
        current_time = current_user.get(operation["uuid"], 0)

        if current_time < operation["max_daily"]:
            user_record[self.uid][operation["uuid"]] = current_time + 1
            return True
        return False
