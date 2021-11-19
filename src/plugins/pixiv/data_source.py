import math

from aiohttp import ClientSession
from nonebot.adapters.cqhttp import MessageSegment

from src.utils.config import PixivConfig

URL = 'https://pixiv.cat/'
HEADERS = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 '
                  'Safari/537.36'}


class Pixiv:
    @staticmethod
    async def get_pic(picid: str) -> list:
        imgurl = URL + picid + '.jpg'
        session = ClientSession()
        resp = await session.get(imgurl)
        await session.close()
        if resp.status == 404:
            images = await Pixiv._get_multi_pic(picid)
            return images
        elif resp.status == 200:
            # TODO: 在前面的步骤将图片下载到本地，以节约时间；配套设施：缓存清理
            images = [MessageSegment.image(imgurl)]
            return images
        else:
            return []

    @staticmethod
    async def _get_multi_pic(picid: str) -> list:
        session = ClientSession()

        async def try_pic(picid: int, current: int, max_num: int, min_num: int) -> int:
            """二分法求最大数量"""
            imgurl = f'{URL}{picid}-{current}.jpg'
            resp = await session.get(imgurl)
            if max_num == min_num:
                return max_num
            if resp.status == 200:
                min_num = current
                if max_num == min_num:
                    return max_num
                return await try_pic(picid, math.ceil((max_num + min_num) / 2), max_num, min_num)
            elif resp.status == 404:
                max_num = current - 1
                return await try_pic(picid, math.ceil((max_num + min_num) / 2), max_num, min_num)
            else:
                return 0

        max_num: int = await try_pic(picid, math.ceil(PixivConfig.max_pic_num / 2), PixivConfig.max_pic_num, 1)
        await session.close()

        images = []
        for i in range(1, max_num + 1):
            images.append(MessageSegment.image(f"{URL}{picid}-{i}.jpg", timeout=1000))

        return images
