class CoolQClientException(Exception):
    pass


class CoolQAPIFailureException(CoolQClientException):
    pass


class CoolQCookieExpiredException(CoolQAPIFailureException):
    pass


class CoolQOfflineException(CoolQClientException):
    pass


class CoolQDisconnectedException(CoolQClientException):
    pass


class CoolQUnknownException(CoolQClientException):
    pass
