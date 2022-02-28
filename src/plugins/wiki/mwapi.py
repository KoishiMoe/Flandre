import aiohttp
from aiohttp import ClientTimeout as ctimeout
from re import compile

from .exceptions import HTTPTimeoutError, MediaWikiException, MediaWikiGeoCoordError, PageError

'''
代码主要来自 pymediawiki 库（以MIT许可证开源），并根据bot的实际需要做了一些修改
该库的Github地址：https://github.com/barrust/mediawiki
许可证：https://github.com/barrust/mediawiki/blob/master/LICENSE
'''

USER_AGENT: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
ODD_ERROR_MESSAGE = (
    "出现了未知问题……如果您所查询的目标wiki以及目标条目均正常，那么可能是bot出现了bug,"
    "请在项目的github页面上提交issue,并附上您查询的目标wiki、条目名及bot日志（若有）"
)


class Mwapi:
    def __init__(self, url: str, api_url: str = '', ua: str = USER_AGENT, timeout: ctimeout = ctimeout(total=30)):
        self._api_url = api_url
        self._url = url
        self._timeout = timeout
        self._ua = ua
        self._title = None
        self._page_url = None
        self._redirected = False
        self._disambiguation = False
        self._from_title = None

    async def _wiki_request(self, params: dict) -> dict:
        # update params
        params["format"] = "json"
        if "action" not in params:
            params["action"] = "query"

        session = aiohttp.ClientSession()
        headers = {"User-Agent": self._ua}

        # get response
        resp = await session.get(self._api_url, params=params, headers=headers, timeout=self._timeout)
        resp_dict = await resp.json()

        await session.close()

        return resp_dict

    async def _wikitext(self) -> str:
        query_params = {
            "action": "parse",
            "page": self._title,
            "prop": "wikitext",
            "formatversion": 2,
        }
        request = await self._wiki_request(query_params)

        # 都到这里了，页面应该存在吧……
        return request["parse"]["wikitext"]

    async def _handle_disambiguation(self) -> list:
        # 截取正文中位于**行首**的内链，以排除非消歧义链接
        # （因为一般的消歧义页面，条目名都在行首）
        # 思路来自于 https://github.com/wikimedia/pywikibot/blob/master/scripts/solve_disambiguation.py
        wikitext = await self._wikitext()
        found_list = list()

        reg = compile(r'\*.*?\[\[(.*?)(?:\||\]\])')
        for line in wikitext.splitlines():
            found = reg.match(line)
            if found:
                found_list.append(found.group(1))

        return found_list


    @staticmethod
    def _check_error_response(response, query):
        """ check for default error messages and throw correct exception """
        if "error" in response:
            http_error = ["HTTP request timed out.", "Pool queue is full"]
            geo_error = [
                "Page coordinates unknown.",
                "One of the parameters gscoord, gspage, gsbbox is required",
                "Invalid coordinate provided",
            ]
            err = response["error"]["info"]
            if err in http_error:
                raise HTTPTimeoutError(query)
            if err in geo_error:
                raise MediaWikiGeoCoordError(err)
            raise MediaWikiException(err)

    async def test_api(self) -> bool:
        try:
            params = {"meta": "siteinfo", "siprop": "extensions|general"}
            resp = await self._wiki_request(params)
        except:
            return False

        query = resp.get("query", None)
        if query is None or query.get("general", None) is None:
            return False

        return True

    async def search(self, query: str, results: int = 10, suggestion: bool = False) -> tuple | list:

        max_pull = 500  # api有500的上限

        search_params = {
            "list": "search",
            "srprop": "",
            "srlimit": min(results, max_pull) if results is not None else max_pull,
            "srsearch": query,
            "sroffset": 0,  # this is what will be used to pull more than the max
        }
        if suggestion:
            search_params["srinfo"] = "suggestion"

        raw_results = await self._wiki_request(search_params)

        self._check_error_response(raw_results, query)

        search_results = [d["title"] for d in raw_results["query"]["search"]]

        if suggestion:
            sug = None
            if raw_results["query"].get("searchinfo"):
                sug = raw_results["query"]["searchinfo"]["suggestion"]
            return search_results, sug
        return search_results

    async def suggest(self, query) -> str | None:
        res, suggest = await self.search(query, results=1, suggestion=True)
        try:
            title = res[0] or suggest
        except IndexError:  # page doesn't exist
            title = None
        return title

    async def opensearch(self, query, results=10, redirect=True):
        max_pull = 500

        query_params = {
            "action": "opensearch",
            "search": query,
            "limit": (min(results, max_pull) if results is not None else max_pull),
            "redirects": ("resolve" if redirect else "return"),
            "warningsaserror": True,
            "namespace": "",
        }

        results = await self._wiki_request(query_params)

        self._check_error_response(results, query)

        res = list()
        for i, item in enumerate(results[1]):
            res.append((item, results[2][i], results[3][i]))
        return res

    async def get_page_info(self, title: str, redirect: bool = True) -> dict:
        self._title = title

        query_params = {
            "titles": self._title,
            "prop": "info|pageprops",
            "inprop": "url",
            "ppprop": "disambiguation",
            "converttitles": 1,
        }
        if redirect:
            query_params["redirects"] = 1

        request = await self._wiki_request(query_params)

        query = request["query"]
        if query.get("pages", None):
            pageid = list(query["pages"].keys())[0]
            page = query["pages"][pageid]

        # determine result of the request
        # redirects is present in query if page is a redirect
        # 有重定向的情况下，query中没有'pages'，所以把重定向检测放在前面
        if "redirects" in query:
            await self._handle_redirect(query=query)
        # missing is present if the page is missing
        elif "missing" in page:
            raise PageError(title=title)
        # if pageprops is returned, it must be a disambiguation error
        elif "pageprops" in page:
            self._disambiguation = True  # 目前没想好消歧义怎么处理……先mark一下吧
            self._page_url = page["fullurl"]
            self._title = page["title"]
            found_list = await self._handle_disambiguation()
        else:
            self._page_url = page["fullurl"]

        result = {
            "exception": False,
            "redirected": self._redirected,
            "disambiguation": self._disambiguation,
            "title": self._title,
            "url": self._page_url,
            "from_title": self._from_title,
            "notes": found_list if self._disambiguation else ''
        }

        return result

    async def _handle_redirect(self, query):
        """ handle redirect """

        final_redirect = query["redirects"][-1]

        if "normalized" in query:
            normalized = query["normalized"][0]
            if normalized["from"] != self._title:
                raise MediaWikiException(ODD_ERROR_MESSAGE)
            from_title = normalized["to"]
        else:
            from_title = self._title

        if not from_title == final_redirect["to"]:  # 循环重定向
            await self.get_page_info(final_redirect["to"], redirect=False)  # 虽然前面已经检测过循环重定向了，不过以防万一
        else:
            await self.get_page_info(final_redirect["from"], redirect=False)  # 防止绕回来
        self._from_title = from_title
        self._redirected = True
