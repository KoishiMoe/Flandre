"""
储存所有响应器
"""
import re
from random import shuffle

import jieba

__all__ = ["Matcher", "PrefixMatcher", "KeywordMatcher", "FullTextMatcher", "RegexMatcher"]


class Matcher:
    def __init__(self, matcher_type: str, probability: int = 100, priority: int = 10, atme: bool = True):
        self.type = matcher_type
        self.probability = probability
        self.priority = priority
        self.atme = atme

    def match(self, message) -> bool:
        """
        判定传入消息是否符合规则
        :param message 要匹配的消息
        :return 若匹配返回真，不匹配返回假
        """
        pass


class PrefixMatcher(Matcher):
    def __init__(self, keyword: str, probability: int = 100, priority: int = 10, atme: bool = True):
        self.prefix = keyword

        super(PrefixMatcher, self).__init__(matcher_type="prefix", probability=probability, priority=priority,
                                            atme=atme)

    def match(self, message: str) -> bool:
        if message.strip().startswith(self.prefix):
            return True
        return False


class KeywordMatcher(Matcher):
    def __init__(self, keyword: str, simple: bool = False, probability: int = 100, priority: int = 10,
                 atme: bool = True):
        self.keyword = keyword
        self.simple = simple

        super(KeywordMatcher, self).__init__(matcher_type="keyword", probability=probability, priority=priority,
                                             atme=atme)

    def match(self, message: str) -> bool:
        message = message.strip()
        if self.simple:
            if self.keyword in message:
                return True
            return False

        words = jieba.lcut(message, cut_all=False)
        shuffle(words)

        for word in words:
            if word == self.keyword:
                return True
        return False


class FullTextMatcher(Matcher):
    def __init__(self, text: str, probability: int = 100, priority: int = 10, atme: bool = True):
        self.text = text

        super(FullTextMatcher, self).__init__(matcher_type="full", probability=probability, priority=priority,
                                              atme=atme)

    def match(self, message: str) -> bool:
        message = message.strip()

        return message == self.text


class RegexMatcher(Matcher):
    def __init__(self, regex: str, ignore_case: bool = True, probability: int = 100, priority: int = 10,
                 atme: bool = True):
        self.regex = regex
        self.ignore_case = ignore_case

        super(RegexMatcher, self).__init__(matcher_type="regex", probability=probability, priority=priority, atme=atme)

    def match(self, message: str) -> bool:
        message = message.strip()
        flags = re.I if self.ignore_case else 0
        result = re.search(pattern=self.regex, string=message, flags=flags)

        if result is None:
            return False
        return True
