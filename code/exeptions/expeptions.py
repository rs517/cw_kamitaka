class Http301MovedPermanentlyException(Exception):
    def __init__(self, url, message="HTTP Exception 301: Moved Permanently"):
        self.url = url
        self.message = message
        super().__init__(self.message)


class Http302FoundException(Exception):
    def __init__(self, url, message="HTTP Exception 302: Found"):
        self.url = url
        self.message = message
        super().__init__(self.message)


class Http403AccessDeniedError(Exception):
    def __init__(self, url, message="HTTP Error 403: Access Denied"):
        self.url = url
        self.message = message
        super().__init__(self.message)


class Http404NotFoundError(Exception):
    def __init__(self, url, message="HTTP Error 404: Not Found"):
        self.url = url
        self.message = message
        super().__init__(self.message)


class Http410GoneError(Exception):
    def __init__(self, url, message="HTTP Error 410: Resource is permanently removed."):
        self.url = url
        self.message = message
        super().__init__(self.message)


class Http429TooManyRequestsException(Exception):
    def __init__(self, url, message="HTTP Error 429: Too Many Requests"):
        self.url = url
        self.message = message
        super().__init__(self.message)
