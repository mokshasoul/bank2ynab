from _typeshed import Incomplete
from bank2ynab import dataframe_handler as dataframe_handler, transactionfile_reader as transactionfile_reader
from bank2ynab.dataframe_handler import DataframeHandler as DataframeHandler
from pathlib import Path
from typing import Any

class BankHandler:
    name: Incomplete
    config_dict: Incomplete
    files_processed: int
    transaction_list: Incomplete
    logger: Incomplete
    def __init__(self, config_dict: dict[str, Any]) -> None: ...
    def run(self) -> None: ...

def get_output_path(input_path: str, prefix: str, ext: str) -> Path: ...
