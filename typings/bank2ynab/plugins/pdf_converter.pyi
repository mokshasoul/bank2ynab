import pandas as pd
from _typeshed import Incomplete
from bank2ynab import bank_handler as bank_handler
from bank2ynab.bank_handler import BankHandler as BankHandler
from typing import List

class PDF_Converter(BankHandler):
    config: Incomplete
    def __init__(self, config_object: dict) -> None: ...

def read_pdf_to_dataframe(pdf_path: str, table_cols: List[str]) -> pd.DataFrame: ...
def build_bank(config): ...
