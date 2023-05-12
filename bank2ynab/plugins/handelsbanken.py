# Plugin for handling format of Handelsbanken [SE] bank export files
"""
    Strip HTML from input file, allowing it to be used by main script
    With thanks to @joacand's script from here:
    github.com/joacand/HandelsbankenYNABConverter/blob/master/Converter.py
"""
from __future__ import annotations

import csv
import logging
import re
from typing import Any, Dict, List

from bank2ynab.bank_handler import BankHandler


class Handelsbanken(BankHandler):
    def __init__(self, config_dict: Dict[str, Any]):
        """
        :param config_dict: a dictionary of conf parameters
        """
        super().__init__(config_dict)
        self.name = "Handelsbanken"

    def _preprocess_file(self, file_path: str, **kwargs) -> str:
        """
        Strips HTML from input file, modifying the input file directly
        :param file_path: path to file
        """
        if kwargs:
            logging.warning("Extra arguments passed %s", kwargs)

        with open(file_path, encoding="utf-8", mode="r") as input_file:
            output_rows: List[List[str]] = []
            for row in input_file:
                cells = row.split(";")
                new_row: List[str] = []
                for cell in cells:
                    es = re.findall(r"\\>.*?\\<", cell)
                    while "><" in es:
                        es.remove("><")
                        for n, i in enumerate(es):
                            es[n] = i[1:-1]
                    # if our cell isn't empty, add it to the row
                    if len(es) > 0:
                        new_row.append(es[0])
                # if our row isn't empty, add it to the list of rows
                if new_row:
                    output_rows.append(new_row)

        # overwrite our source file
        with open(file_path, encoding="utf-8", mode="wb") as output_file:
            writer = csv.DictWriter(
                output_file,
                fieldnames=output_rows[0],
                quoting=csv.QUOTE_ALL,
                delimiter=";",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(output_rows[1:])

        return file_path


def build_bank(config: Dict[str, Any]) -> BankHandler:
    """This factory function is called from the main program,
    and expected to return a BankHandler subclass.
    Without this, the module will fail to load properly.

    :param config: dict containing all available configuration parameters
    :return: a BankHandler subclass instance
    """
    return Handelsbanken(config)
