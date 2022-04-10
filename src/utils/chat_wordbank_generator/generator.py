"""
简易的词库批量生成工具，只能生成，代码很暴力（梦回初学python.jpg）
"""
import json
import random
import re
from sys import exit
from uuid import uuid1
from pathlib import Path


def get_input(prompt: str, typ: str = "", *args, **kwargs):
    inp = ''
    while inp == '':
        inp = input(prompt + "\n")
        if inp in ("!#exit", "!#quit"):
            ex()
        if not check_valid_input(inp, typ, args, kwargs):
            inp = ''
        if typ == "bool":
            inp = str_to_bool(inp) if inp else args[0]
        if kwargs.get("allow_empty", False):
            break

    return inp


def check_valid_input(inp: str, typ: str = "", args: tuple = (), kwargs=None):
    if kwargs is None:
        kwargs = {}
    if inp == '' and kwargs.get("allow_empty", False):
        return True
    match typ:
        case "num":
            result = inp.isdigit() and args[0] <= int(inp) <= args[1] if len(args) >= 2 else int(inp)  # 不提供最大值时，只检查最小值
        case "url":
            result = re.match(r'^https?:/{2}\w.+$', inp)
        case "bool":
            result = inp.strip() in ("Y", "y", "n", "N", "T", "t", "f", "F", "")
        case _:
            result = True
    if not result:
        print("非法的输入值！")
        return False
    return True


def str_to_bool(string: str | None | bool) -> bool:
    """
    将字符串形式的true/false转换成布尔值
    :param string: 要判断的字符串
    :return: 转换出的布尔值
    """
    return True if string in ("T", "t", "Y", "y") else False


def gen_replyer() -> dict:
    replyer = []
    while True:
        replyer_type = int(get_input("请选择回复类型， 可选类型有：0.限制 1.文本 2.图片 3.语音 4.TTS 5.正则替换 6.自定义函数 7.留空", "num", 0, 7).strip())
        match replyer_type:
            case 0:
                new_rep = {
                    "type": "restricted",
                    "restriction": {}
                }
                # restriction_type = int(get_input("请选择限制类型，可选类型有：1.好感度", "num", 1, 1).strip())
                restriction_type = 1
                match restriction_type:
                    case 1:
                        new_rep["restriction"]["type"] = "fav"
                        new_rep["restriction"]["min_fav"] = get_input("请输入要限制的最低好感度，范围-100~100", "num", -100, 100)
                print("请提供允许条件下的回复：")
                new_rep["allow"] = gen_replyer()
                print("请提供拒绝条件的回复：")
                new_rep["deny"] = gen_replyer()
            case 1:
                new_rep = {
                    "type": "text",
                    "text": get_input("请输入要回复的文本").strip(),
                }
            case 2:
                new_rep = {
                    "type": "image",
                }
                filename = input("请输入图片的文件名（含后缀），该文件应该被置于词库所在目录的 static/images 子目录下；若要使用url,请直接回车：")
                if filename:
                    new_rep["filename"] = filename
                else:
                    new_rep["url"] = get_input("请提供指向图片的**直链**，推荐使用开放图床提供的直链：", "url")
            case 3:
                new_rep = {
                    "type": "voice",
                    "filename": get_input("请输入语音文件的文件名（含后缀），该文件应该被置于词库所在目录的 static/audio 子目录下"),
                }
            case 4:
                new_rep = {
                    "type": "tts",
                    "filename": get_input("请输入要转换成语音的文字"),
                    "lang": get_input("请提供上述文字对应的语言标签，需要符合IETF标准，详见 https://datahub.io/core/language-codes"),
                }
            case 5:
                new_rep = {
                    "type": "regex_sub",
                    "pattern": get_input("请提供用于正则替换的模式字符串"),
                    "repl": get_input("请提供用于替换的字符串（仅支持纯文本）"),
                    "count": int(get_input("请提供替换次数，默认为0（无限）", "num", 0, allow_empty=True).strip() or 0)
                }
            case 6:
                new_rep = {
                    "type": "code",
                    "local": get_input("是否要本地运行该代码？如非必要，建议使用默认（否）y/N", "bool", False)
                }
                code = ''
                while True:
                    newline = get_input("请输入下一行代码，直接回车来结束输入：", allow_empty=True).strip()
                    if newline:
                        code += newline + "\n"
                    else:
                        break
                new_rep["code"] = code
            case _:
                new_rep = {}

        if new_rep:
            new_rep["weight"] = int(get_input("要为该回复赋予权重吗？权重更大的回复被抽取的概率更高。默认为1：", "num", 1, allow_empty=True).strip() or 1)

        replyer.append(new_rep)
        if replyer_type == 0 or not get_input("要为该响应器添加另一个回复吗？Y/n", "bool", True):
            break

    options = gen_options()

    resp = {}
    if len(replyer) == 1:
        resp["replyer"] = replyer[0]
    elif len(replyer) > 1:
        resp["replyer"] = replyer
    if options:
        resp["options"] = options

    return resp


def gen_options() -> dict:
    options = {}
    while True:
        option_type = int(get_input("要为该回复组/响应器继续添加附加选项吗？0. 不添加（默认） 1.好感度", "num", 0, 1, allow_empty=True).strip() or 0)
        match option_type:
            case 1:
                typ = get_input("请选择要对好感度进行的操作，1.加 2.减 3.乘 4.除", "num", 1, 4)
                options["fav"] = {
                    "type": "+" if typ == 1 else "-" if typ == 2 else "*" if typ == 3 else "/",
                    "num": int(get_input("请输入要操作的数量", "num", 0).strip()),
                }
                max_daily = int(get_input("请输入每天最大次数限制，默认为0（无限)：", "num", 0, allow_empty=True).strip() or 0)
                if max_daily:
                    options["fav"]["max_daily"] = max_daily
                    options["fav"]["uuid"] = str(uuid1())
            case _:
                break

    return options


print("欢迎使用词库生成工具！你可以随时输入 !#exit 或 !#quit 来退出")

output = []
file = Path(f"output{random.randint(0, 114514)}.json")

while file.exists():
    file = Path(f"output{random.randint(0, 114514)}.json")

with open(file, 'w', encoding='utf-8') as f:
    def ex():
        f.write(json.dumps(output, indent=2))
        exit(0)
    while True:
        new_matcher = {
            "matcher": {},
        }
        matcher_type = int(get_input("请选择响应器类型，可选类型有：1.前缀 2.关键词 3.全字 4.正则", "num", 1, 4).strip())
        match matcher_type:
            case 1:
                new_matcher["matcher"]["type"] = "prefix"
                new_matcher["matcher"]["keyword"] = get_input("输入你要匹配的前缀").strip()
            case 2:
                new_matcher["matcher"]["type"] = "keyword"
                new_matcher["matcher"]["keyword"] = get_input("输入你要匹配的关键词").strip()
                new_matcher["matcher"]["simple_mode"] = get_input("是否启用简易匹配？y/N", "bool", False)
            case 3:
                new_matcher["matcher"]["type"] = "full"
                new_matcher["matcher"]["keyword"] = get_input("输入要匹配的文字").strip()
            case 4:
                new_matcher["matcher"]["type"] = "regex"
                new_matcher["matcher"]["regex"] = get_input("输入要使用的正则表达式")
                new_matcher["matcher"]["ignore_case"] = get_input("是否忽略大小写？Y/n", "bool", True)

        for key, value in gen_replyer().items():
            new_matcher[key] = value

        output.append(new_matcher)

        f.truncate(0)
        f.write(json.dumps(output, indent=2))

        if not get_input("要继续添加吗：Y/n", "bool", True):
            break
