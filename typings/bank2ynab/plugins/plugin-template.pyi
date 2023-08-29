from bank2ynab.bank_handler import BankHandler as BankHandler

class YourActualBankPlugin(BankHandler):
    name: str
    def __init__(self, config_dict: dict) -> None: ...

def build_bank(config): ...
