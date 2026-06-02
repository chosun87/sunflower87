from typing import Any, Optional


class AppException(Exception):
    def __init__(self, status_code: int, detail: str, data: Optional[Any] = None):
        self.status_code = status_code
        self.detail = detail
        self.data = data
        super().__init__(detail)


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)


class BadRequestException(AppException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=400, detail=detail)


class InternalServerException(AppException):
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(status_code=500, detail=detail)
