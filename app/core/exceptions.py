class VendorRateLimitError(Exception):
    def __init__(
        self,
        retry_after: int
    ):
        self.retry_after = retry_after
        super().__init__(
            "Vendor rate limited request"
        )


class VendorServerError(Exception):
    pass


class VendorTimeoutError(Exception):
    pass