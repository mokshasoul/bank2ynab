from bank_handler import BankHandler

class OCBC_Bank_SG(BankHandler):
    name: str
    def __init__(self, config_dict: dict) -> None: ...

def build_bank(config): ...
