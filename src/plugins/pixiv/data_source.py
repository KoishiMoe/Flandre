import requests

from nonebot.adapters.cqhttp import MessageSegment

URL = 'https://pixiv.cat/'
HEADERS = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'}


class Pixiv:
    @staticmethod
    async def get_pic(picid: str) -> list:
        imgurl = URL + picid + '.jpg'
        resp = requests.get(imgurl)
        if resp.status_code == 404:
            images = await Pixiv._get_multi_pic(picid)
            return images
        elif resp.status_code == 200:
            images = [MessageSegment.image(imgurl)]
            return images
        else:
            return []

    @staticmethod
    async def _get_multi_pic(picid: str) -> list:
        images = []
        for i in range(1, 11):
            imgurl = f"{URL}{picid}-{i}.jpg"
            resp = requests.get(imgurl)
            if resp.status_code == 200:
                images.append(MessageSegment.image(imgurl, timeout=1000))
        return images
