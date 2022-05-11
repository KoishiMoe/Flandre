import re
from asyncio.exceptions import TimeoutError
from socket import gaierror

from mcstatus import JavaServer, BedrockServer

from src.utils.str2img import Str2Img


async def je_or_be(address: str, port: int) -> bool | None:
    """判定给定的服务器是je还是be，若je返回True，be返回False，无法连接返回None"""
    no_port_flag = False
    try:
        if not port:
            no_port_flag = True
            port = 25565
        server = JavaServer(address, port)
        result = await server.async_status()
        if result:
            return True
    except Exception:
        pass
    try:
        if not port or no_port_flag:
            port = 19132
        server = BedrockServer(address, port)
        result = await server.async_status()
        if result:
            return False
    except Exception:
        pass
    return None


async def get_server_status(address: str, port: int, is_be: bool | None = False):
    if is_be is None:
        # 在这里直接获取信息，减少一次请求
        try:
            tmp_port = port or 25565
            server = JavaServer(address, tmp_port)
            status = await server.async_status(tries=1)
        except TimeoutError:
            try:
                tmp_port = port or 19132
                server = BedrockServer(address, tmp_port)
                status = await server.async_status(tries=1)
            except Exception:
                return "连接失败：也许服务器宕机了╮（╯＿╰）╭"
        except gaierror:
            return "无法解析域名……是不是打错了？((*・∀・）ゞ→→"
        except Exception:
            try:
                tmp_port = port or 19132
                server = BedrockServer(address, tmp_port)
                status = await server.async_status()
            except Exception:
                return "连接失败：我也不知道发生了什么╮（╯＿╰）╭"

    else:
        if is_be:
            if not port:
                port = 19132
            server = BedrockServer(address, port)
        else:
            if not port:
                port = 25565
            server = JavaServer(address, port)

        try:
            status = await server.async_status()
        except gaierror:
            return "域名解析失败：是不是打错了？((*・∀・）ゞ→→"
        except Exception:
            return "连接失败：也许服务器宕机了╮（╯＿╰）╭"

    if isinstance(server, BedrockServer):
        motd = status.motd + '\n' + status.map
        motd = re.sub(r'§\w', '', motd)
        output = f"描述：{motd.strip()}\n" \
                 f"服务端：{status.version.version}\n" \
                 f"在线人数：{status.players_online}/{status.players_max}\n" \
                 f"延迟：{status.latency}"
    else:
        raw = status.raw
        desc: dict | str = raw.get("description", "")
        motd = __parse_java_motd(desc) if isinstance(desc, dict) else re.sub(r'§\w', '', desc)
        output = f"描述：{motd.strip()}\n" \
                 f"服务端：{status.version.name}\n" \
                 f"在线人数：{status.players.online}/{status.players.max}\n" \
                 f"延迟：{status.latency:.2f}ms"
        if status.players.online:
            output += "\n在线列表：\n"
            players = [player.name for player in status.players.sample]
            output += "、".join(players)

    if len(output) > 200:
        output = Str2Img().gen_message(output)

    return output


def __parse_java_motd(description: dict) -> str:
    """提供description字典，返回拆出来的无格式motd；
    之所以用这个是因为status.description会缺失一部分带格式文本（如加粗的文本，本体也直接无了）
    只在少量服务器测试过，不确保100%可用。"""
    motd = description.get("text")
    for k, v in description.items():
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    motd += __parse_java_motd(item)
        elif isinstance(v, dict):
            motd += __parse_java_motd(v)

    return motd
