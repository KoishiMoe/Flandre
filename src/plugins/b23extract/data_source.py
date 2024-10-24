import re
from io import BytesIO

from aiohttp import ClientSession, ClientTimeout
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.log import logger

from src.utils.str2img import Str2Img
from .bilibili_api import video, live, bangumi, article, Credential, settings
from .bilibili_api.exceptions import ResponseCodeException
from ...utils.config import B23Config


class Extract:
    def __init__(self, message: str, credential: Credential = None, proxy: str = '', use_image: str = 'auto'):
        self.text = message
        self.credential = credential if credential else None
        self.use_image = use_image
        self.avid: int = 0
        self.bvid: str = ''
        self.room_id: int = 0
        self.epid: int = 0
        self.ssid: int = 0
        self.mdid: int = 0
        self.cvid: int = 0
        settings.proxy = proxy

    async def process(self):
        resp_tuple = await self._pre_process()
        if resp_tuple:
            resp = await self._post_process(resp_tuple)
            return resp

    async def _pre_process(self):
        aid = re.compile(r'av(\d+)', re.I).search(self.text)
        bvid = re.compile(r'(BV([a-zA-Z\d]{10})+)', re.I).search(self.text)
        epid = re.compile(r'ep(\d+)', re.I).search(self.text)
        ssid = re.compile(r'ss(\d+)', re.I).search(self.text)
        mdid = re.compile(r'md(\d+)', re.I).search(self.text)
        room_id = re.compile(r"(live\.bilibili\.com(\\?)/((blanc|h5)(\\?)/)?(\d+))", re.I).search(self.text)
        # 消息里面有时候有双斜杠 ，直播id又没有标识头……
        cvid = re.compile(r'(cv|/read/(mobile|native)(/|\?id=))(\d+)', re.I).search(self.text)
        if bvid:
            self.bvid = bvid[0]
            # self.avid = bvid2aid(bvid[0])
            resp = await self._video_parse()
        elif aid:
            self.avid = int(re.sub(r"(\D)", "", aid[0]))
            resp = await self._video_parse()
        elif epid:
            self.epid = int(re.sub(r"(\D)", "", epid[0]))
            resp = await self._bangumi_parse()
        elif ssid:
            self.ssid = int(re.sub(r"(\D)", "", ssid[0]))
            resp = await self._bangumi_parse()
        elif mdid:
            self.mdid = int(re.sub(r"(\D)", "", mdid[0]))
            resp = await self._bangumi_parse()
        elif room_id:
            self.room_id = int(re.sub(r"(\D)", "", room_id[0].replace("h5", "")))  # 不然h5中的5会被保留
            resp = await self._live_parse()
        elif cvid:
            self.cvid = int(re.sub(r"(\D)", "", cvid[0]))
            resp = await self._article_parse()
        else:
            return
        return resp

    async def _post_process(self, resp_tuple: tuple):
        async def gen_text(resp_tuple: tuple):
            resp = MessageSegment.image(await self._get_cover(resp_tuple[2])) if resp_tuple[2] else ''  # nonebot获取图片可能会抽风
            resp += f"{resp_tuple[0]}\n链接：{resp_tuple[1]}"
            return resp

        async def gen_image(resp_tuple: tuple):
            try:
                img = await self._gen_image(resp_tuple)
                resp_img = MessageSegment.image(img)
                resp_text = f"标题：{resp_tuple[3]}\n链接：{resp_tuple[1]}"
                return resp_img, resp_text
            except Exception as e:
                resp = await gen_text(resp_tuple)
                resp += "\nWarning: 图片生成失败，请管理员检查bot日志"
                logger.warning(f"图片生成失败：{e}")
                return resp

        if self.use_image == 'no':
            resp = await gen_text(resp_tuple)
            return resp
        elif self.use_image == 'yes':
            return await gen_image(resp_tuple)
        else:
            # auto或无效值
            if len(resp_tuple[0]) > 200:
                # 检查视频文字介绍的长度是否过长
                return await gen_image(resp_tuple)
            else:
                return await gen_text(resp_tuple)

    async def _video_parse(self):
        if self.avid > 0:
            vid = video.Video(aid=self.avid, credential=self.credential)
        else:
            vid = video.Video(bvid=self.bvid, credential=self.credential)
        info = await vid.get_info()

        aid = info.get("aid", 0)
        bvid = info.get("bvid", "")
        tname = info.get("tname", "未知分类")
        pic = info.get("pic", "")
        title = info.get("title", "未知标题")
        up = info.get("owner", {}).get("name", "")
        desc = info.get("desc", "")

        if info.get("staff", None):
            up_uid = [i.get("mid") for i in info.get("staff", [])]
            up_name = [i.get("name") for i in info.get("staff", [])]
        else:
            up_uid = [info.get("owner", {}).get("mid", 0)]
            up_name = [info.get("owner", {}).get("name", "")]

        try:
            tags = await vid.get_tags()
            tags = [i.get("tag_name", "") for i in tags]
        except Exception as e:
            logger.info(f"获取视频{self.avid}标签失败：{e}")
            tags = []

        if self._filter(title, up_name, up_uid, tags, tname, desc):
            raise ResponseCodeException(-403, "")

        desc = self._check_desc(desc)
        cover = await self._check_cover(pic)

        message = f"\n标题：{title}\n" \
                  f"UP：{up}\n" \
                  f"分类：{tname}\n" \
                  f"简介：{desc}"
        # url = f"https://www.bilibili.com/video/av{self.avid}"
        if aid > 0:
            url = f"https://b23.tv/av{aid}"
        elif bvid:
            url = f"https://b23.tv/{bvid}"
        elif self.avid > 0:
            url = f"https://b23.tv/av{self.avid}"
        else:
            url = f"https://b23.tv/{self.bvid}"

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
        up = info.get("anchor_info", {}).get("base_info", {}).get("uname", "")
        up_uid = room_info.get("uid", -1)

        if self._filter(title, [up], [up_uid], tags.split(','), room_info.get("area_name", ""), desp):
            raise ResponseCodeException(-403, "")

        desp = self._check_desc(desp)

        cover = await self._check_cover(cover)

        resp = f"\n标题：{title}\n" \
               f"主播：{up}\n" \
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

            if self._filter(title, [], [], [], "", desp):
                raise ResponseCodeException(-403, "")

            cover = await self._check_cover(cover)

            resp = f"\n标题：{title}\n" \
                   f"简介：{self._check_desc(desp)}"

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
            desp = self._check_desc(desp)

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

        # 似乎专栏的分类和标签在html里面？为了这个去解析html有点太重了
        if self._filter(title, [author], [info.get("mid", 0)], [], "", ""):
            raise ResponseCodeException(-403, "")

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

    @staticmethod
    async def _get_cover(cover: str):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Referer": "https://www.bilibili.com/"
        }
        try:
            session = ClientSession()
            resp = await session.get(cover, headers=headers, timeout=ClientTimeout(total=30))
            cover = BytesIO(await resp.content.read())
            await session.close()
        except Exception as e:
            if "session" in locals():
                await session.close()
            logger.warning(f"下载封面{cover}失败：{e}")
            cover = None

        return cover

    def _check_desc(self, desc: str):
        # FIXME: 图片生成失败时简介过长
        if self.use_image != 'no':
            return desc
        else:
            return desc if len(desc) <= 180 else desc[:180] + "……"

    async def _gen_image(self, resp_tuple: tuple):
        cover = await self._get_cover(resp_tuple[2])

        convertor = Str2Img()
        img = convertor.gen_image(text=resp_tuple[0], qrc=resp_tuple[1], head_pic=cover)

        buf = BytesIO()
        img.save(buf, format="JPEG", quality=95)

        return buf

    def _filter(self, title: str, up: list[str], up_uid: list[int], tag: list[str], category: str, desc: str):
        if B23Config.filter_title:
            for i in B23Config.filter_title:
                if title and re.search(i, title, re.I):
                    logger.info(f"标题：{title} 被过滤")
                    return True
        if B23Config.filter_up_regex:
            for i in B23Config.filter_up_regex:
                for j in up:
                    if j and re.search(i, j, re.I):
                        logger.info(f"UP：{j} 被过滤")
                        return True
        if B23Config.filter_up_uid:
            for i in B23Config.filter_up_uid:
                for j in up_uid:
                    if j and int(i) == int(j):
                        logger.info(f"UP UID：{j} 被过滤")
                        return True
        if B23Config.filter_tag:
            for i in B23Config.filter_tag:
                for j in tag:
                    if j and re.search(i, j, re.I):
                        logger.info(f"标签：{j} 被过滤")
                        return True
        if B23Config.filter_category:
            if category and category in B23Config.filter_category:
                logger.info(f"分类：{category} 被过滤")
                return True
        if B23Config.filter_desc:
            for i in B23Config.filter_desc:
                if desc and re.search(i, desc, re.I):
                    logger.info(f"简介：{desc} 被过滤")
                    return True

