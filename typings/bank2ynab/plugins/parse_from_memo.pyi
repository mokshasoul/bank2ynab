from _typeshed import Incomplete
from bank2ynab.bank_handler import BankHandler as BankHandler, get_output_path as get_output_path
from bank2ynab.dataframe_handler import read_csv as read_csv
from bank2ynab.transactionfile_reader import detect_encoding as detect_encoding

class ParseFromMemo(BankHandler):
    parsers_to_try: Incomplete
    def __init__(self, config_object) -> None: ...

def build_bank(config): ...
