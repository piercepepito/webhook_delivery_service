class WebDeliveryError(Exception):
    """
    A customzed exception when a webhook delivery fails

    Attributes:
        original_error: the original string error that occured during the HTTP Request
        duration_ms: the length of time when executing a func in milliseconds
    """
    def __init__(self, original_error, duration_ms):
        self.original_error = original_error
        self.duration_ms = duration_ms
        super().__init__(str(original_error))


class InvalidDeliveryIdError(Exception):
    pass