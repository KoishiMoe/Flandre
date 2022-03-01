import math

from aiohttp import ClientSession
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.log import logger
from pixivpy_async import AppPixivAPI
from pixivpy_async.error import AuthTokenError

from src.utils.config import PixivConfig

URL = 'https://pixiv.cat/'
HEADERS = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 '
                  'Safari/537.36'}


class Pixiv:
    @staticmethod
    async def get_pic(picid: str) -> list:
        if PixivConfig.token:
            num, tags = await Pixiv._get_pic_api(int(picid))
            if num:
                # 如图片有tag,检查tag是否在黑名单中
                if PixivConfig.enable_tag_filter and list(PixivConfig.blocked_tags)[0]:  # 防止未配置block tag时误伤
                    for tag in tags:
                        for value in tag.values():
                            if value in PixivConfig.blocked_tags:
                                return []

                images = [MessageSegment.image(f"{URL}{picid}.jpg") if num == 1 else
                          MessageSegment.image(f"{URL}{picid}-{i}.jpg") for i in range(1, num + 1)]  # num=1时，不加次序id

                return images

        # 禁止回落时，直接返回空值
        if PixivConfig.disable_fallback:
            return []

        imgurl = URL + picid + '.jpg'
        session = ClientSession()
        resp = await session.get(imgurl)
        await session.close()
        if resp.status == 404:  # pixiv.cat 404，判定为不止一张（不存在的情况在_get_multi_pic中处理）
            images = await Pixiv._get_multi_pic(picid)
            return images
        if resp.status == 200:
            images = [MessageSegment.image(imgurl)]
            return images
        return []

    @staticmethod
    async def _get_multi_pic(picid: str) -> list:
        session = ClientSession()

        async def try_pic(picid: str, current: int, max_num: int, min_num: int) -> int:
            """
            二分法求最大数量
            在图片量较少的时候也许一个个试更有效率？
            """
            imgurl = f'{URL}{picid}-{current}.jpg'
            resp = await session.get(imgurl)
            if max_num == min_num:
                return max_num
            if resp.status == 200:
                min_num = current
                if max_num == min_num:
                    return max_num
                return await try_pic(picid, math.ceil((max_num + min_num) / 2), max_num, min_num)
            if resp.status == 404:
                max_num = current - 1
                return await try_pic(picid, math.ceil((max_num + min_num) / 2), max_num, min_num)
            return 0

        max_num: int = await try_pic(picid, math.ceil(PixivConfig.max_pic_num / 2), PixivConfig.max_pic_num, 0)
        await session.close()

        images = []
        for i in range(1, max_num + 1):
            images.append(MessageSegment.image(f"{URL}{picid}-{i}.jpg", timeout=1000))

        return images

    @staticmethod
    async def _get_pic_api(picid: int):
        try:
            if PixivConfig.proxy:
                aapi = AppPixivAPI(proxy=PixivConfig.proxy)
            else:
                aapi = AppPixivAPI()
            await aapi.login(refresh_token=PixivConfig.token)
        except AuthTokenError:
            logger.error("登陆pixiv失败，请检查token是否有误")
            return 0, []
        except Exception as e:
            logger.error(f"登陆pixiv出错：未知错误：\n{e}")
            return 0, []

        try:
            """
            已知问题：帐号未开通r18访问时，会导致返回信息异常（num=1,tags=[])
            关闭r18访问并不能用来屏蔽r18，反而会导致tag无法被识别，所以还是尽量开着吧……
            """
            result = await aapi.illust_detail(picid)
            num = result.get("illust", {}).get("page_count", 0)
            tags = result.get("illust", {}).get("tags", [])
        except Exception as e:
            logger.error(f"获取插画信息错误：未知错误\n{e}")
            return 0, []
        return num, tags
