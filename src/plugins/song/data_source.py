from random import randint

from aiohttp import ClientSession, ClientTimeout, ClientResponse
from nonebot import logger

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " \
             "Chrome/91.0.4501.0 Safari/537.36 Edg/91.0.866.0"
HEADERS = {'X-Real-IP': f"58.206.254.{randint(1, 254)}", "User-Agent": USER_AGENT, "Accept": "application/json"}


async def get_music_list(keyword: str, source: str = "163") -> list[dict[str, str | int]] | None:
    match source:
        case "163":
            url = "https://music.163.com/api/cloudsearch/pc"
            params = {"s": keyword, "type": 1, "offset": 0, "limit": 10}
        case "qq":
            url = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp"
            params = {"p": 1, "n": 10, "w": keyword, "format": "json"}
        case _:
            logger.warning(f"未知的音乐平台：{source}，通常情况下这不应该发生")
            return

    try:
        async with ClientSession(headers=HEADERS, timeout=ClientTimeout(total=3)) as session:
            resp: ClientResponse = await session.get(url=url, params=params)
            resp: dict = await resp.json(content_type=None)  # Q音返回的mimetype是javascript……
    except Exception as e:
        logger.warning(f"从平台{source}搜索音乐{keyword}时发生了错误：{e}")
        return

    if not resp:
        return

    match source:
        case "163":
            songs = resp.get("result", {}).get("songs")
            if not songs:
                return
            songs_list = [
                {
                    "id": song.get("id", 22636634),  # 私货2333
                    "name": song.get("name", "获取歌名出错"),
                    "artist": '、'.join([artist.get("name", "获取歌手名出错") for artist in song.get("ar", [])])
                    if song.get("ar") else "",
                } for song in songs
            ]
        case "qq":
            songs = resp.get("data", {}).get("song", {}).get("list", [])
            if not songs:
                return
            songs_list = [
                {
                    "id": song.get("songid", 4809988),
                    "name": song.get("songname", "获取歌名出错"),
                    "artist": "、".join([artist.get("name") for artist in song.get("singer", [])])
                    if song.get("singer") else "",
                } for song in songs
            ]
        case _:
            logger.warning(f"未知的音乐平台：{source}，通常情况下这不应该发生")
            return

    if len(songs_list) >= 2 and songs_list[0]["name"] == keyword:
        # 如果第一个就完全匹配了，并且之后的不是完全匹配，那么直接返回第一个
        flag = False
        for i in songs_list[1:]:
            if i["name"] == keyword:
                flag = True
                break
        if not flag:
            songs_list = [songs_list[0]]

    return songs_list


    
