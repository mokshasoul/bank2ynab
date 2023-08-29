from _typeshed import Incomplete

class ErrorDetail:
    def __init__(self, *, err_id: str, name: str, detail: str) -> None: ...

class ErrorResponse:
    error: Incomplete
    def __init__(self, *, error) -> None: ...
