from fastapi import status


class PulseError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message, self.status_code)


class DuplicateMonitorError(PulseError):
    def __init__(self) -> None:
        super().__init__("Monitor already exists", status_code=status.HTTP_409_CONFLICT)


class MonitorNotFoundError(PulseError):
    def __init__(self) -> None:
        super().__init__("Monitor not found", status_code=status.HTTP_404_NOT_FOUND)


class RateLimitExceeded(PulseError):
    def __init__(self) -> None:
        super().__init__(
            "Too many requests. Please wait a minute or create an account",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class InvalidURL(PulseError):
    def __init__(self) -> None:
        super().__init__("Enter a valid URL", status_code=status.HTTP_400_BAD_REQUEST)
