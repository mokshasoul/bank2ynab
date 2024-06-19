from __future__ import annotations

import logging
from configparser import NoSectionError
from typing import Dict, List

from bank2ynab import user_input
from bank2ynab.api_interface import APIInterface
from bank2ynab.config_handler import ConfigHandler

# configure our logger
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


class YNAB_API:
    """
    uses Personal Access Token stored in user_configuration.conf
    (note for devs: be careful not to accidentally share API access token!)
    """

    def __init__(self, config_object: ConfigHandler, transactions=None) -> None:
        self.transactions = transactions if transactions else []
        self.budget_id = None
        self.config_handler = config_object
        self.api_token = self.config_handler.config.get(
            "DEFAULT", "YNAB API Access Token"
        )

        self.api_connect = None

        if self.api_token:
            self.api_connect = APIInterface(api_token=self.api_token)

    def run(self, transaction_data: Dict[str, List]):
        if not self.api_connect:
            raise NotImplementedError

        logging.debug("Transaction data: %s", transaction_data)
        # get previously-saved budget/account mapping
        bank_account_mapping = self.get_saved_accounts(transaction_data)
        # load budget & account data from API
        budget_info = self.api_connect.budget_info
        # remove any account IDs that don't exist in API info
        bank_account_mapping = remove_invalid_accounts(
            prev_saved_map=bank_account_mapping, api_data=budget_info
        )
        # ask user to set budget & account for each unsaved bank
        select_accounts(mappings=bank_account_mapping, budget_info=budget_info)
        # save account mappings
        self.save_account_mappings(bank_account_mapping)
        # map transactions to budget and account IDs
        budget_transactions = apply_mapping(transaction_data, bank_account_mapping)
        for budget_id, budget in budget_info.items():
            if budget_id in budget_transactions:
                self.api_connect.post_transactions(
                    budget_id=budget_id,
                    data=budget_transactions[budget_id],
                )
            else:
                logging.info(
                    "No transactions to upload for %s.",
                    budget["name"],
                )

    def get_saved_accounts(self, t_data: Dict) -> Dict[str, Dict[str, str]]:
        bank_account_mapping: Dict[str, Dict[str, str]] = {}
        for bank_name in t_data.keys():
            account_id = ""
            budget_id = ""
            # check if bank has account associated with it already
            try:
                config_line = self.config_handler.get_config_line_lst(
                    bank_name, "YNAB Account ID", "||"
                )
                budget_id = config_line[0]
                account_id = config_line[1]
                logging.info("Previously-saved account for %s found.", bank_name)
            except IndexError:
                pass
            except NoSectionError:
                # TODO - can we handle this within the config class?
                logging.info("No user configuration for %s found.", bank_name)
            bank_account_mapping.setdefault(
                bank_name, {"account_id": account_id, "budget_id": budget_id}
            )
        return bank_account_mapping

    def save_account_mappings(self, mapping: Dict[str, dict]):
        for bank_name in mapping:
            # save account selection for bank
            save_ac_toggle = self.config_handler.get_config_line_boo(
                bank_name, "Save YNAB Account"
            )
            if save_ac_toggle:
                self.config_handler.save_account_selection(
                    bank_name,
                    mapping[bank_name]["budget_id"],
                    mapping[bank_name]["account_id"],
                )
            else:
                logging.info(
                    "Saving default YNAB account is disabled for %s "
                    "- account match not saved.",
                    bank_name,
                )


def remove_invalid_accounts(
    prev_saved_map: Dict[str, Dict[str, str]], api_data: Dict[str, dict]
) -> Dict[str, Dict[str, str]]:
    temp_mapping = prev_saved_map
    for bank in prev_saved_map:
        budget_id = prev_saved_map[bank]["budget_id"]
        account_id = prev_saved_map[bank]["account_id"]

        try:
            if budget_id not in api_data.keys():
                raise KeyError
            if account_id not in api_data[budget_id]["accounts"].keys():
                raise KeyError
        except KeyError:
            temp_mapping.setdefault(bank, {"account_id": "", "budget_id": ""})

    return temp_mapping


def select_accounts(mappings: Dict[str, Dict[str, str]], budget_info: Dict[str, dict]):
    for bank in mappings.keys():
        if mappings[bank]["account_id"] == "":
            # get the budget ID and Account ID to write to
            budget_id, account_id = select_account(bank, budget_info)
            mappings[bank]["budget_id"] = budget_id
            mappings[bank]["account_id"] = account_id


def select_account(bank_name: str, budget_info: Dict[str, dict]):
    budget_id = ""
    account_id = ""
    instruction = "No YNAB {} for transactions from {} set!\nPick {}"

    # "No YNAB budget for {} set! \nPick a budget".format(bank)
    msg = instruction.format("budget", bank_name, "a budget")

    # generate budget name/id list
    budget_list = generate_name_id_list(budget_info)
    # ask user to select budget
    budget_id = user_input.get_user_input(budget_list, msg)

    # msg = "Pick a YNAB account for transactions from {}".format(bank)
    msg = instruction.format("account", bank_name, "an account")
    # generate account name/id list
    account_dict = budget_info[budget_id]["accounts"]
    account_list = generate_name_id_list(account_dict)
    # ask user to select account
    account_id = user_input.get_user_input(account_list, msg)

    return budget_id, account_id


def generate_name_id_list(input_dict: Dict) -> List[List]:
    output_list = []
    for input_id, input_conf in input_dict.items():
        output_list.append([input_conf["name"], input_id])

    return output_list


def apply_mapping(
    transaction_data: Dict[str, list], mapping: Dict[str, Dict[str, str]]
) -> Dict[str, Dict[str, list]]:
    """
    Create a dictionary of budget_ids mapped to a dictionary of transactions.
    Add an account_id to each transaction.

    :param transaction_data: dictionary of bank names to transaction data
    :param mapping: dictionary mapping bank names to budget ID and account ID
    :return: dictionary of budget_id mapped to a dictionary of transactions
    """
    logging.info("Adding budget and account IDs to transactions...")
    budget_transaction_dict: Dict[str, Dict[str, list]] = {}

    # get transactions for each bank
    for bank, account_transactions in transaction_data.items():
        budget_id = mapping[bank]["budget_id"]
        account_id = mapping[bank]["account_id"]

        # insert account_id into each transaction
        for transaction in account_transactions:
            transaction["account_id"] = account_id
        # add transaction list into entry for relevant budget
        if budget_id in budget_transaction_dict:
            budget_transaction_dict[budget_id]["transactions"].extend(
                account_transactions
            )
        else:
            budget_transaction_dict.setdefault(
                budget_id, {"transactions": account_transactions}
            )

    return budget_transaction_dict
