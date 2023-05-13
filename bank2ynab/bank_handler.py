"""
    Bank handling module
"""
from __future__ import annotations

import logging
import os
import traceback
from pathlib import Path
from typing import Any, List, Dict

from bank2ynab import dataframe_handler, transactionfile_reader
from bank2ynab.dataframe_handler import DataframeHandler


class BankHandler:
    """
    Handle the flow for data input, parsing, and data output
    for a given bank configuration.
    """

    def __init__(self, config_dict: Dict[str, Any]) -> None:
        """
        Initialise object and load bank-specific configuration parameters.

        :param config_dict: dictionary of all banks' configurations with
        the bank names as keys.
        :type config_dict: dict
        """
        self.name = config_dict.get("bank_name", "DEFAULT")
        self.config_dict = config_dict
        self.files_processed = 0
        self.transaction_list: List[Dict] = []
        self.logger = logging.getLogger("bank2ynab")

    def run(self) -> None:
        matching_files = transactionfile_reader.get_files(
            name=self.config_dict["bank_name"],
            file_pattern=self.config_dict["input_filename"],
            try_path=self.config_dict["path"],
            regex_active=self.config_dict["regex"],
            ext=self.config_dict["ext"],
            prefix=self.config_dict["fixed_prefix"],
        )

        file_dfs: List = []

        for src_file in matching_files:
            self.logger.info("Parsing input file: %s (%s)", src_file, self.name)
            try:
                # perform preprocessing operations on file if required
                src_file = self._preprocess_file(
                    file_path=src_file,
                    plugin_args=self.config_dict["plugin_args"],
                )
                # get file's encoding
                src_encod = transactionfile_reader.detect_encoding(src_file)
                # create our base dataframe

                df_handler = DataframeHandler()
                df_handler.run(
                    file_path=src_file,
                    delim=self.config_dict["input_delimiter"],
                    header_rows=int(self.config_dict["header_rows"]),
                    footer_rows=int(self.config_dict["footer_rows"]),
                    encod=src_encod,
                    input_columns=self.config_dict["input_columns"],
                    output_columns=self.config_dict["output_columns"],
                    api_columns=self.config_dict["api_columns"],
                    cd_flags=self.config_dict["cd_flags"],
                    date_format=self.config_dict["date_format"],
                    date_dedupe=self.config_dict["date_dedupe"],
                    fill_memo=self.config_dict["payee_to_memo"],
                    currency_fix=self.config_dict["currency_mult"],
                )

                self.files_processed += 1
            except ValueError as err:
                self.logger.info(
                    "No output data from this file for this bank. (%s)", err
                )
                self.logger.debug(traceback.format_exc())
            else:
                # make sure our data is not blank before writing
                if not df_handler.df.empty:
                    # write export file
                    output_path = get_output_path(
                        input_path=src_file,
                        prefix=self.config_dict["fixed_prefix"],
                        ext=self.config_dict["output_ext"],
                    )
                    self.logger.info(
                        "Writing output file: %s (debug - commented out)",
                        output_path,
                    )
                    df_handler.output_csv(str(output_path.absolute()))
                    # save api transaction data for each bank to list
                    file_dfs.append(df_handler.api_transaction_df)
                    # delete original csv file
                    if self.config_dict.get("delete_original", False):
                        self.logger.info(
                            "Removing input file: %s (debug - commented out)",
                            src_file,
                        )
                        os.remove(src_file)
                else:
                    self.logger.info("No output data from this file for this bank.")
        # don't add empty transaction dataframes
        if file_dfs:
            combined_df = dataframe_handler.combine_dfs(file_dfs)
            self.transaction_list = combined_df.to_dict(orient="records")

    def _preprocess_file(self, file_path: str, **kwargs) -> str:
        """
        exists solely to be used by plugins for pre-processing a file
        that otherwise can be read normally (e.g. weird format)

        :param file_path: path to file
        """
        # intentionally empty - plugins can use this function
        if kwargs:
            self.logger.warning("Extra arguments passed to function: %s", kwargs)

        return file_path


def get_output_path(input_path: str, prefix: str, ext: str) -> Path:
    """
    Generate the name of the output file.

    :param path: path to output file
    :return: target filename
    """
    target_dir = Path(input_path).parent
    target_fname = Path(input_path).stem

    new_filename = f"{prefix}{target_fname}{ext}"
    new_path = target_dir / new_filename
    counter = 1
    while new_path.exists():
        new_filename = f"{prefix}{target_fname}_{counter}{ext}"
        new_path = target_dir / new_filename
        counter += 1

    return new_path
