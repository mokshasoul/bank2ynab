from _typeshed import Incomplete

RESPONSE_CODES: Incomplete

class YNABError(Exception):
    response_code: Incomplete
    def __init__(self, response_code: str, detail: str) -> None: ...
