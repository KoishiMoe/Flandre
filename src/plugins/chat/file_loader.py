"""
下载和加载词库文件
"""
import json
import os
from pathlib import Path

from aiofile import Writer, AIOFile
from aiohttp import ClientSession, ClientTimeout
from nonebot.log import logger
from py7zr import SevenZipFile

from .exceptions import FileDownloadError


DATA = Path('.') / 'data' / 'resources'
DATA_ONLINE_PATH = DATA / 'online' / 'chat'
DATA_CUSTOM_PATH = DATA / 'custom' / 'chat'
STORAGE_PATH = Path('.') / 'data' / 'database' / 'chat'

DATA_URL = "https://github.com/KoishiMoe/Flandre-resources/raw/main/chat/"
USER_AGENT: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'

BASE_FILE = {
  "format_version": 1,
  "comment": "请勿手动修改上方格式版本号",
  "bank": []
}


async def get_base_wordbank() -> list:
    custom_bank = DATA_CUSTOM_PATH / 'wordbank.json'
    online_bank = DATA_ONLINE_PATH / 'wordbank.json'

    os.makedirs(DATA_ONLINE_PATH, exist_ok=True)
    os.makedirs(DATA_CUSTOM_PATH, exist_ok=True)

    if not custom_bank.exists():
        if not online_bank.exists():
            logger.info("未找到词库，正在下载在线词库……")
            try:
                await get_file('wordbank.7z')
            except Exception as e:
                logger.error(f"下载在线词库失败：{e}\n"
                             f"如果无法自动下载，请前往{DATA_URL}手动下载，并将其置于./data/resources/online/chat/中")
                raise FileDownloadError

        wordbank = json.loads(online_bank.read_bytes()).get("bank", [])
    else:
        wordbank = json.loads(custom_bank.read_bytes()).get("bank", [])

    return wordbank


async def get_wordbank(gid: int) -> list:
    """
    返回指定群/全局的词库
    :param gid: 群号，若为0,则表示全局
    :return: 包含所有匹配单元的列表
    """
    os.makedirs(STORAGE_PATH, exist_ok=True)
    path = STORAGE_PATH / f'{gid}.json'
    if not path.is_file():
        with open(path, 'w', encoding='utf-8') as w:
            w.write(json.dumps(BASE_FILE, indent=2))
    data = json.loads(path.read_bytes()).get("bank", [])

    return data


async def get_full_wordbank(gid: int) -> list:
    """
    返回完整的词库，包含本群（如果群号不为0）、全局、基础词库
    :param gid: 群号，如果是私聊，应当传入0
    :return: 包含完整词库的列表
    """
    if gid:
        return await get_wordbank(gid) + await get_wordbank(0) + await get_base_wordbank()
    else:
        return await get_wordbank(0) + await get_base_wordbank()


async def save_wordbank(gid: int, wordbank: list):
    path = STORAGE_PATH / f'{gid}.json'
    data = BASE_FILE
    data["bank"] = wordbank
    with open(path, 'w', encoding='utf-8') as w:
        w.write(json.dumps(data, indent=2))


async def get_file(filename: str):
    async with ClientSession(headers={'User-Agent': USER_AGENT}) as session:
        async with session.get(f"{DATA_URL}{filename}", timeout=ClientTimeout(total=120)) as resp:
            async with AIOFile(DATA_ONLINE_PATH / filename, 'wb') as f:
                writer = Writer(f)
                result = await resp.read()
                await writer(result)
                await f.fsync()

    with SevenZipFile(DATA_ONLINE_PATH / filename, 'r') as z:
        z.extractall(path=DATA_ONLINE_PATH)
