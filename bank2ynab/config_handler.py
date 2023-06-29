from __future__ import annotations

import configparser
import logging
from pathlib import Path
from typing import Any, Dict, List


class ConfigHandler:
    logger = logging.getLogger("bank2ynab")

    def __init__(self) -> None:
        """
        This class instantiates a config handler
        tha reads bank2ynab.conf and if specified the
        user_configuration.conf file.

        It handles reading, updating and cleaning the configuration
        """

        project_dir = Path(__file__).resolve().parent.parent
        self.bank_conf_path = project_dir / "bank2ynab.conf"
        self.user_conf_path = project_dir / "user_configuration.conf"

        self.config = configparser.ConfigParser(interpolation=None)
        if self.bank_conf_path.exists():
            with open(self.bank_conf_path, encoding="utf-8") as f:
                self.config.read_file(f)

        self.user_config = configparser.ConfigParser(interpolation=None)
        if self.user_conf_path.exists():
            self.user_config.read(self.user_conf_path)
            self.config.read(self.user_conf_path)

    def save_account_selection(self, bank, budget_id, account_id):
        """
        saves YNAB account to use for each bank
        """
        try:
            self.user_config.add_section(bank)
            logging.info("Saving default account for %s...", bank)
        except configparser.DuplicateSectionError:
            self.logger.warning("%s bank is already mapped to another account", bank)

        self.user_config.set(bank, "YNAB Account ID", f"{budget_id}||{account_id}")
        with open(self.user_conf_path, "w", encoding="utf-8") as config_file:
            self.user_config.write(config_file)

        self.config.update(self.user_config)

    def fix_conf_params(self, section: str) -> Dict[str, Any]:
        """
        from a ConfigParser object, return a dictionary of all parameters
        for a given section in the expected format.
        Because ConfigParser defaults to values under [DEFAULT] if present,
        these values should always appear unless the file is really bad.

        :param section: name of section in config file to access
            (i.e. bank name, e.g. "MyBank" matches "[MyBank]" in file)
        :return: dictionary matching shorthand strings to specified
            values in config
        """

        bank_config = {
            "bank_name": section,
            "input_columns": self.get_config_line_lst(section, "Input Columns", ","),
            "output_columns": self.get_config_line_lst(section, "Output Columns", ","),
            "api_columns": self.get_config_line_lst(
                section, "API Transaction Fields", ","
            ),
            "input_filename": self.get_config_line_str(
                section, "Source Filename Pattern"
            ),
            "path": self.get_config_line_str(section, "Source Path"),
            "ext": self.get_config_line_str(section, "Source Filename Extension"),
            "encoding": self.get_config_line_str(section, "Encoding"),
            "regex": self.get_config_line_boo(section, "Use Regex For Filename"),
            "fixed_prefix": self.get_config_line_str(section, "Output Filename Prefix"),
            "output_ext": self.get_config_line_str(
                section, "Output Filename Extension"
            ),
            "input_delimiter": self.get_config_line_str(
                section, "Source CSV Delimiter"
            ),
            "header_rows": self.get_config_line_int(section, "Header Rows"),
            "footer_rows": self.get_config_line_int(section, "Footer Rows"),
            "date_format": self.get_config_line_str(section, "Date Format"),
            "date_dedupe": self.get_config_line_boo(section, "Date De-Duplication"),
            "delete_original": self.get_config_line_boo(section, "Delete Source File"),
            "cd_flags": self.get_config_line_lst(
                section, "Inflow or Outflow Indicator", ","
            ),
            "payee_to_memo": self.get_config_line_boo(section, "Use Payee for Memo"),
            "plugin": self.get_config_line_str(section, "Plugin"),
            "plugin_args": self.get_config_line_lst(section, "Plugin Arguments", "\n"),
            "api_token": self.get_config_line_str(section, "YNAB API Access Token"),
            "api_account": self.get_config_line_lst(section, "YNAB Account ID", "|"),
            "currency_mult": self.get_config_line_flt(
                section, "Currency Conversion Factor"
            ),
        }

        # quick n' dirty fix for tabs as delimiters
        if bank_config["input_delimiter"] == "\\t":
            bank_config["input_delimiter"] = "\t"

        return bank_config

    def get_config_line_str(self, section_name: str, param: str) -> str:
        """
        Returns a string value from a given section in the config object.

        :param section_name: section to search for parameter
        :param param: parameter to obtain from section
        :return: value matching parameter
        """
        return self.config.get(section_name, param)

    def get_config_line_int(self, section_name: str, param: str) -> int:
        """
        Returns an integer value from a given section in the config object.

        :param section_name: section to search for parameter
        :param param: parameter to obtain from section
        :return: value matching parameter
        """
        return self.config.getint(section_name, param)

    def get_config_line_flt(self, section_name: str, param: str) -> float:
        """
        Returns a float value from a given section in the config object.

        :param section_name: section to search for parameter
        :param param: parameter to obtain from section
        :return: value matching parameter
        """

        return self.config.getfloat(section_name, param)

    def get_config_line_boo(self, section_name: str, param: str) -> bool:
        """
        Returns a bool value from a given section in the config object.

        :param section_name: section to search for parameter
        :param param: parameter to obtain from section
        :return: value matching parameter
        """

        return self.config.getboolean(section_name, param)

    def get_config_line_lst(
        self, section_name: str, param: str, splitter: str
    ) -> List[Any]:
        """
        Returns a list value from a given section in the config object.

        :param section_name: section to search for parameter
        :param param: parameter to obtain from section
        :return: value matching parameter
        """
        if self.config.has_option(section_name, param):
            return self.config.get(section_name, param).split(splitter)

        return self.config.get("DEFAULT", param).split(splitter)
