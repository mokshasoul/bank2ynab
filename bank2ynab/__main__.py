"""
main bank2ynab module
"""

import importlib
import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List

from bank2ynab.bank_handler import BankHandler
from bank2ynab.config_handler import ConfigHandler
from bank2ynab.ynab_api import YNAB_API

# configure our logger
logging.basicConfig(format="%(levelname): %(message)", level=logging.INFO)


def build_bank(bank_config: Dict[str, Any]) -> BankHandler:
    """Factory method loading the correct class
    for a given configuration."""
    plugin_module_name = bank_config.get("plugin", None)
    if plugin_module_name:
        module = importlib.import_module(f"plugins.{plugin_module_name}")
        if not hasattr(module, "build_bank"):
            err_msg = (
                f"The specified plugin {plugin_module_name}.py "
                "does not contain the required build_bank(config) method."
            )
            raise ImportError(err_msg)
        bank: BankHandler = module.build_bank(bank_config)
        return bank

    return BankHandler(config_dict=bank_config)


# Let's run this thing!
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="bank2ynab",
        description="Imports bank csv exports into YNAB",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    logger = logging.getLogger("bank2ynab")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("%s\nDEBUG LOGGING ACTIVE\n%s", "-" * 8, "-" * 8)

    try:
        config_handler = ConfigHandler(
            project_dir=Path(__file__).resolve().parent.parent
        )
    except FileNotFoundError:
        logger.error("No configuration file found, process aborted.")
    else:
        # generate list of bank objects to process
        bank_obj_list: List[BankHandler] = []
        for bank_params in config_handler.config.sections():
            config_dict = config_handler.fix_conf_params(bank_params)
            # create bank object using config (allows for plugin use)
            bank_object = build_bank(bank_config=config_dict)
            bank_obj_list.append(bank_object)

        # initialize variables for summary:
        files_processed = 0
        bank_transaction_dict: Dict[str, list] = {}

        # process account for each config entry
        for bank_object in bank_obj_list:
            bank_object.run()
            if bank_object.transaction_list:
                bank_transaction_dict[bank_object.name] = bank_object.transaction_list
            files_processed += bank_object.files_processed
        logger.info("File processing complete! %s files processed.", files_processed)

        if bank_transaction_dict:
            api = YNAB_API(config_handler)
            try:
                api.run(bank_transaction_dict)
            except NotImplementedError:
                logger.error("No API key given, not uploading transaction data")
