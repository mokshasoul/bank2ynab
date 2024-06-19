class ErrorDetail:
    def __init__(self, *, err_id: str, name: str, detail: str):
        self._id = err_id
        self._name = name
        self._detail = detail


class ErrorResponse:
    def __init__(self, *, error):
        self.error = error
