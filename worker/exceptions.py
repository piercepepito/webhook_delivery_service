class WebDeliveryError(Exception):
    def __init__(self, original_error, duration_ms):
        self.original_error = original_error
        self.duration_ms = duration_ms
        super().__init__(str(original_error))