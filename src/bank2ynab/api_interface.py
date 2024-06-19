"""
bank2ynab API acess
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from bank2ynab.ynab_api_response import YNABError


class APIInterface:
    """
    A class representing the API interface for interacting with the YNAB API.

    Attributes:
        budget_info (dict[str, dict]): A dictionary mapping budget IDs to budget parameters.
        logger (logging.Logger): The logger object for logging messages.

    Methods:
        __init__(api_token: str): Initializes the APIInterface object.
        access_api(budget_id: str, keyword: str, method: str, data: dict) -> dict: Accesses the YNAB API.
        api_read(budget_id: str, keyword: str) -> Any: Reads data from the YNAB API.
        post_transactions(budget_id: str, data: dict) -> None: Sends transaction data to the YNAB API.
        get_budget_accounts(budget_id: str) -> dict[str, dict]: Retrieves account data for a budget.
        get_budgets() -> dict[str, dict]: Retrieves budget data.

    """

    def __init__(self, api_token: str) -> None:
        """
        Initializes the APIInterface object.

        Args:
            api_token (str): The API token to access the YNAB API.

        Raises:
            ValueError: If an empty API token is provided.
        """
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
        """
        Accesses the YNAB API.

        Args:
            budget_id (str): The ID of the budget.
            keyword (str): The keyword for the API endpoint.
            method (str): The HTTP method to use (either "post" or "get").
            data (dict): The data to send in the API request.

        Returns:
            dict: The response data from the API.

        Raises:
            YNABError: If the API response status code is >= 300.
        """
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
        """
        Reads data from the YNAB API.

        Args:
            budget_id (str): The ID of the budget.
            keyword (str): The keyword for the API endpoint.

        Returns:
            Any: The response data from the API.

        Raises:
            YNABError: If there is an error accessing the API.
        """
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
        Sends transaction data to YNAB via API call.

        Args:
            budget_id (str): The ID of the budget to post transactions to.
            data (dict): The transaction data in JSON format.

        Raises:
            YNABError: If there is an error accessing the API.
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
        Retrieves account data for a budget.

        Args:
            budget_id (str): The ID of the budget.

        Returns:
            dict[str, dict]: A dictionary mapping account IDs to account parameters.

        Raises:
            YNABError: If there is an error accessing the API.
        """
        accounts = self.api_read(budget_id=budget_id, keyword="accounts")
        return APIInterface.fix_id_based_dicts(accounts)

    def get_budgets(self) -> dict[str, dict]:
        """
        Retrieves budget data.

        Returns:
            dict[str, dict]: A dictionary mapping budget IDs to budget parameters.

        Raises:
            YNABError: If there is an error accessing the API.
        """
        budgets = self.api_read(budget_id="", keyword="budgets")

        return APIInterface.fix_id_based_dicts(budgets)

    @staticmethod
    def fix_id_based_dicts(input_data: dict) -> dict[str, dict]:
        """
        Combines response data JSON into a dictionary mapping ID to response data.

        Args:
            input_data (dict): The JSON-style dictionary.

        Returns:
            dict[str, dict]: A dictionary mapping "id" to response data.
        """
        output_dict: dict[str, dict] = {}
        for sub_dict in input_data:
            output_dict.setdefault(sub_dict["id"], sub_dict)

        return output_dict
