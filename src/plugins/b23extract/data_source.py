import re
from io import BytesIO

import qrcode
from PIL import Image
from aiohttp import ClientSession, ClientTimeout
from bilibili_api import video, live, bvid2aid, bangumi, article, Credential, settings
from nonebot.adapters.onebot.v11 import MessageSegment

from src.utils.str2img import Str2Img


class Extract:
    def __init__(self, message: str, credential: Credential = None, proxy: str = '', use_image: bool = True):
        self.text = message
        self.credential = credential if credential else None
        self.use_image = use_image
        self.avid: int = 0
        self.room_id: int = 0
        self.epid: int = 0
        self.ssid: int = 0
        self.mdid: int = 0
        self.cvid: int = 0
        settings.proxy = proxy

    async def process(self):
        resp_tuple = await self._pre_process()
        resp = await self._post_process(resp_tuple)
        return resp

    async def _pre_process(self):
        aid = re.compile(r'av(\d+)', re.I).search(self.text)
        bvid = re.compile(r'(BV([a-zA-Z0-9]{10})+)', re.I).search(self.text)
        epid = re.compile(r'ep(\d+)', re.I).search(self.text)
        ssid = re.compile(r'ss(\d+)', re.I).search(self.text)
        mdid = re.compile(r'md(\d+)', re.I).search(self.text)
        room_id = re.compile(r"(live\.bilibili\.com(\\?)/((blanc|h5)(\\?)/)?(\d+))", re.I).search(self.text)
        # 消息里面有时候有双斜杠 ，直播id又没有标识头……
        cvid = re.compile(r'(cv|/read/(mobile|native)(/|\?id=))(\d+)', re.I).search(self.text)
        if bvid:
            self.avid = bvid2aid(bvid[0])
            resp = await self._av_parse()
        elif aid:
            self.avid = int(re.sub(r"([^0-9])", "", aid[0]))
            resp = await self._av_parse()
        elif epid:
            self.epid = int(re.sub(r"([^0-9])", "", epid[0]))
            resp = await self._bangumi_parse()
        elif ssid:
            self.ssid = int(re.sub(r"([^0-9])", "", ssid[0]))
            resp = await self._bangumi_parse()
        elif mdid:
            self.mdid = int(re.sub(r"([^0-9])", "", mdid[0]))
            resp = await self._bangumi_parse()
        elif room_id:
            self.room_id = int(re.sub(r"([^0-9])", "", room_id[0].replace("h5", "")))  # 不然h5中的5会被保留
            resp = await self._live_parse()
        elif cvid:
            self.cvid = int(re.sub(r"([^0-9])", "", cvid[0]))
            resp = await self._article_parse()
        else:
            return
        return resp

    async def _post_process(self, resp_tuple: tuple):
        async def gen_text(resp_tuple: tuple):
            resp = MessageSegment.image(resp_tuple[2]) if resp_tuple[2] else ''
            resp += f"{resp_tuple[0]}\n链接：{resp_tuple[1]}"
            return resp
        async def gen_image(resp_tuple: tuple):
            try:
                img = await self._gen_image(resp_tuple)
                resp_img = MessageSegment.image(img)
                resp_text = f"标题：{resp_tuple[3]}\n链接：{resp_tuple[1]}"
                return resp_img, resp_text
            except:
                resp = gen_text(resp_tuple)
                resp += "\nWarning: 图片生成失败，请管理员检查bot日志"
                return resp

        if self.use_image == 'no':
            resp = await gen_text(resp_tuple)
            return resp
        elif self.use_image == 'yes':
            return await gen_image(resp_tuple)
        else:
            # auto或无效值
            if len(resp_tuple[0]) + len(resp_tuple[3]) > 120:
                # 检查标题和简介的长度是否过长
                return await gen_image(resp_tuple)
            else:
                return await gen_text(resp_tuple)


    async def _av_parse(self):
        vid = video.Video(aid=self.avid, credential=self.credential)
        info = await vid.get_info()

        tname = info.get("tname", "未知分类")
        pic = info.get("pic", "")
        title = info.get("title", "未知标题")
        up = info.get("owner", {}).get("name", "")
        desc = info.get("desc", "")
        desc = await self._check_desc(desc)

        cover = await self._check_cover(pic)

        message = f"标题：{title}\n" \
                  f"UP：{up}\n" \
                  f"分类：{tname}\n" \
                  f"简介：{desc}"
        url = f"https://www.bilibili.com/video/av{self.avid}"

        return message, url, cover, title

    async def _live_parse(self):
        room = live.LiveRoom(self.room_id, credential=self.credential)
        info = await room.get_room_info()

        room_info: dict = info.get("room_info", {})
        cover = room_info.get("cover", "")
        title = room_info.get("title", "")
        tags = room_info.get("tags", "")
        desp = room_info.get("description", "")
        area = f'{room_info.get("parent_area_name", "")}-{room_info.get("area_name", "")}'

        desp = await self._check_desc(desp)

        cover = await self._check_cover(cover)

        resp = f"\n标题：{title}\n" \
               f"分区：{area}\n" \
               f"标签：{tags}\n" \
               f"简介：{desp}"
        url = f"https://live.bilibili.com/{self.room_id}"
        return resp, url, cover, title

    async def _bangumi_parse(self):
        async def parse_ssid(ssid):
            info: dict = await bangumi.get_overview(ssid, credential=self.credential)
            cover = info.get("cover", "")
            title = info.get("session_title", "")
            desp = info.get("evaluate", "")
            mmid = info.get("media_id")
            url = f"https://www.bilibili.com/bangumi/media/md{mmid}"

            cover = await self._check_cover(cover)

            resp = f"\n标题：{title}\n" \
                   f"简介：{await self._check_desc(desp)}"

            return resp, url, cover, title

        if self.mdid:
            info: dict = await bangumi.get_meta(self.mdid, credential=self.credential)
            self.ssid = info.get("season_id", "")
            if not self.ssid:
                cover = info.get("cover", "")
                title = info.get("title", "")
                url = info.get("share_url", f"https://www.bilibili.com/bangumi/media/md{self.mdid}")

                cover = await self._check_cover(cover)

                resp = f"\n标题：{title}"
            else:
                resp, url, cover, title = await parse_ssid(self.ssid)

        elif self.ssid:
            resp, url, cover, title = await parse_ssid(self.ssid)

        elif self.epid:
            info: dict = await bangumi.get_episode_info(self.epid, credential=self.credential)
            title = info.get("h1Title", "")
            media_info = info.get("mediaInfo", {})
            cover = media_info.get("cover", "") if media_info else ""
            desp = media_info.get("evaluate", "") if media_info else ""
            url = f"https://www.bilibili.com/bangumi/play/ep{self.epid}"
            desp = await self._check_desc(desp)

            cover = await self._check_cover(cover)
            resp = f"\n标题：{title}\n" \
                   f"简介：{desp}"

        else:
            resp = "解析番剧信息失败"
            url = ''
            cover = ''
            title = ''

        return resp, url, cover, title

    async def _article_parse(self):
        art = article.Article(self.cvid, credential=self.credential)
        info: dict = await art.get_info()
        title = info.get("title", "")
        cover = info.get("banner_url", "")
        author = info.get("author_name", "")
        url = f"https://www.bilibili.com/read/cv{self.cvid}"

        cover = await self._check_cover(cover)
        resp = f"\n标题：{title}\n" \
               f"作者：{author}\n"

        return resp, url, cover, title

    @staticmethod
    async def _check_cover(cover: str):
        if cover:
            if not cover.startswith("http"):
                cover = f"https://{cover.strip('/')}"  # api似乎会返回不带http的链接
            # resp = MessageSegment.image(cover, cache=True, timeout=1000)
        else:
            cover = ""
        return cover

    async def _check_desc(self, desc: str):
        # FIXME: 图片生成失败时简介过长
        if self.use_image != 'no':
            return desc
        else:
            return desc if len(desc) <= 100 else desc[:100] + "……"

    @staticmethod
    async def _gen_image(resp_tuple: tuple):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"}

        if resp_tuple[1]:
            qr = qrcode.QRCode()
            qr.add_data(resp_tuple[1])
            qr.make(fit=True)
            qrc = qr.make_image(fill_color=(74, 69, 99))
        else:
            qrc = None

        try:
            async with ClientSession() as session:
                resp = await session.get(resp_tuple[2], headers=headers, timeout=ClientTimeout(total=30))
                cover = BytesIO(await resp.content.read())
        except Exception:
            cover = None

        convertor = Str2Img()
        base_img = convertor.gen_image(text=resp_tuple[0])

        if cover:
            cover = Image.open(cover)
            cover = cover.resize((1080, 608), Image.ANTIALIAS)

            out_img = Image.new(mode="RGB", size=(1080, 608 + base_img.size[1]),
                                color=(255, 255, 255))
            out_img.paste(cover, (0, 0))
            out_img.paste(base_img, (0, 609))
        else:
            out_img = Image.new(mode="RGB", size=(1080, base_img.size[1]),
                                color=(255, 255, 255))
            out_img.paste(base_img, (0, 0))

        if qrc:
            qrc = qrc.resize((130, 130), Image.ANTIALIAS)
            out_img.paste(qrc, (0, out_img.size[1] - 130))

        buf = BytesIO()
        out_img.save(buf, format="JPEG", quality=95)

        return buf
