"""
限制器
"""
from src.utils.favorability import FavData


class Restrictor:
    def __init__(self, restrictor_type: str):
        self.type = restrictor_type

    def check(self, user_id) -> bool:
        """
        检查指定用户是否符合限制条件
        :param user_id: 用户id
        :return: 若符合条件，返回True,否则False
        """
        pass


class FavRestrictor(Restrictor):
    def __init__(self, min_fav: int):
        self.min_fav = min_fav

        super(FavRestrictor, self).__init__(restrictor_type="fav")

    def check(self, user_id: int) -> bool:
        data = FavData(uid=user_id)

        return data.favorability >= self.min_fav
