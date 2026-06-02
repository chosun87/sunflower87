from typing import Any, Optional


def success_response(data: Optional[Any] = None, message: Optional[str] = None) -> dict:
    res = {"status": "success"}
    if data is not None:
        res["data"] = data
    if message is not None:
        res["message"] = message
    return res


def error_response(message: str) -> dict:
    return {"status": "error", "message": message}
