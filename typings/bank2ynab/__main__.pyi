from bank2ynab.bank_handler import BankHandler as BankHandler
from bank2ynab.config_handler import ConfigHandler as ConfigHandler
from bank2ynab.ynab_api import YNAB_API as YNAB_API
from typing import Any, Dict

def build_bank(bank_config: Dict[str, Any]) -> BankHandler: ...
