from bank2ynab.bank_handler import BankHandler as BankHandler
from typing import Any, Dict

class Handelsbanken(BankHandler):
    name: str
    def __init__(self, config_dict: Dict[str, Any]) -> None: ...

def build_bank(config: Dict[str, Any]) -> BankHandler: ...
