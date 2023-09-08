"""
    bank2ynab API acess
"""
from __future__ import annotations

import logging
from typing import Any

import requests

from bank2ynab.ynab_api_response import YNABError


class APIInterface:
    def __init__(self, api_token: str) -> None:
        # dict mapping {budget_id: {budget_params}}
        self.budget_info: dict[str, dict] = {}
        self.logger = logging.getLogger("bank2ynab")

        self.logger.info("Attempting to connect to YNAB API...")
        if api_token:
            self.api_token = api_token
            self.logger.info("Obtaining budget and account data...")
            # create budget parameter dictionary
            budget_dict = self.get_budgets()
            # add accounts dictionary to each budget in dict
            for budget_id, budget in budget_dict.items():
                budget_accounts = self.get_budget_accounts(budget_id=budget_id)
                budget["accounts"] = budget_accounts

            self.budget_info = budget_dict
            self.logger.info("All budget and account data obtained.")
        else:
            self.logger.error("No API-token provided.")
            raise ValueError("Empty API token")

    def access_api(
        self,
        *,
        budget_id: str,
        keyword: str,
        method: str,
        data: dict,
    ) -> dict:
        base_url = "https://api.youneedabudget.com/v1/budgets/"
        params = {"access_token": self.api_token}

        if budget_id:
            url = f"{base_url}{budget_id}/{keyword}"
        else:
            # only happens when we're looking for the list of budgets
            url = base_url

        if method == "post":
            self.logger.info("Sending '%s' data to YNAB API...", keyword)
            response = requests.post(url, params=params, json=data, timeout=30)
        else:
            self.logger.info("Reading '%s' data from YNAB API...", keyword)
            response = requests.get(url, params=params, timeout=30)

        response_data = {}

        if response.status_code >= 300:
            raise YNABError(str(response.status_code), response.text)

        response_data = response.json()["data"]
        return response_data

    def api_read(self, *, budget_id: str, keyword: str) -> Any:
        return_data = {}
        try:
            return_data = self.access_api(
                budget_id=budget_id,
                keyword=keyword,
                method="get",
                data={},
            )
        except YNABError as err:
            self.logger.error("YNAB API Error: %s", err)

        return return_data.get(keyword, {})

    def post_transactions(self, *, budget_id: str, data: dict) -> None:
        """
        Send transaction data to YNAB via API call

        :param api_token: API token to access YNAB API
        :param budget_id: id of budget to post transactions to
        :param data: transaction data in json format
        """

        self.logger.info("Uploading transactions to YNAB...")
        try:
            response = self.access_api(
                budget_id=budget_id,
                keyword="transactions",
                method="post",
                data=data,
            )
            self.logger.info(
                "Success:\n %s entries uploaded,\n %s entries skipped.",
                len(response["transaction_ids"]),
                len(response["duplicate_import_ids"]),
            )
        except YNABError as err:
            self.logger.error("YNAB API Error: %s", err)

    def get_budget_accounts(self, *, budget_id: str) -> dict[str, dict]:
        """
        Returns dictionary matching account id to list of account parameters.

        :param api_token: API token to access YNAB API
        :param budget_id: budget ID to read account data from
        :return: dictionary mapping account id to parameters
        """
        accounts = self.api_read(budget_id=budget_id, keyword="accounts")
        return APIInterface.fix_id_based_dicts(accounts)

    def get_budgets(self) -> dict[str, dict]:
        """
        Returns dictionary matching budget id to list of budget parameters.

        :param api_token: API token to access YNAB API
        :return: dictionary mapping budget id to parameters
        """
        budgets = self.api_read(budget_id="", keyword="budgets")

        return APIInterface.fix_id_based_dicts(budgets)

    @staticmethod
    def fix_id_based_dicts(input_data: dict) -> dict[str, dict]:
        """
        Combines response data JSON into a dictionary mapping ID to response data.

        :param input_data: JSON-style dictionary
        :return: dictionary mapping "id" to response data
        """
        output_dict: dict[str, dict] = {}
        for sub_dict in input_data:
            output_dict.setdefault(sub_dict["id"], sub_dict)

        return output_dict
