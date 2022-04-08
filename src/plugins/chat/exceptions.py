"""
插件定义的异常
"""


class UnknownOperationError(Exception):
    """未知操作 """
    pass


class UnknownMatcherTypeError(Exception):
    """未知响应器类型"""
    pass


class UnknownReplyTypeError(Exception):
    """未知回复类型"""
    pass


class UnknownRestrictionTypeError(Exception):
    """未知限制类型"""
    pass


class FileDownloadError(Exception):
    """文件下载失败"""
    pass
