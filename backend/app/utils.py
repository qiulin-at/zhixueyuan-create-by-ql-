def ok(data=None, message: str = "ok") -> dict:
    return {"code": 0, "message": message, "data": data}


def paginated(items: list, total: int, page: int, page_size: int) -> dict:
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def error(code: int, message: str) -> dict:
    return {"code": code, "message": message, "data": None}