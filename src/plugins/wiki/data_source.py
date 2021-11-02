from json import JSONDecodeError
from urllib import parse

from mediawiki import MediaWiki


# WIKI_DIR = Path(".") / "data" / "database" / "wiki"
# os.makedirs(WIKI_DIR, exist_ok=True)

class NoApiUrlException(Exception):
    pass

class Wiki:

    def __init__(self, api_url: str, fallback_url: str):
        # self.__api = MediaWiki(url=api_url)
        self.__url = fallback_url
        self.__api_url = api_url

    async def get_from_api(self, title: str, is_template: bool) -> str:
        if is_template:
            title = "T:" + title
        try:
            if self.__api_url == '':
                raise NoApiUrlException
            self.__api = MediaWiki(url=self.__api_url)
            result = self.__api.opensearch(title, results=1)
        except:  # 针对无法正常调用API的情况的回落，例如WAF
            result = await self.url_parse(title)
            # result = f"API调用失败，已使用备用方式\n{result}"
            return result
        if result:
            title = result[0][0]
            url = result[0][2]
            result = f"标题：{title}\n链接：{url}"
        else:
            result = await self.url_parse(title)
            result = f"没有找到该条目，以下是由条目名直接生成的链接\n{result}"
        return result

    async def url_parse(self, title: str) -> str:
        result = f"标题：{title}\n链接：{self.__url + parse.quote(title)}"
        return result

    # @staticmethod
    # async def load_group_info(group: int) -> dict:
    #     file_name = f"{group}.json"
    #     path = WIKI_DIR / file_name
    #     if not path.is_file():
    #         with open(path, "w", encoding="utf-8") as w:
    #             w.write(json.dumps({}))
    #
    #     data = json.loads(path.read_bytes())
    #     return data
    #
    # @staticmethod
    # async def save_group_info(group: int, data: dict) -> None:
    #     file_name = f"{group.json}"
    #     path = WIKI_DIR / file_name
    #     if not path.is_file():
    #         with open(path, "w", encoding="utf-8") as w:
    #             w.write(json.dumps({}))
    #
    #     with open(path, "w", encoding="utf-8") as w:
    #         w.write(json.dumps(data, indent=4))
