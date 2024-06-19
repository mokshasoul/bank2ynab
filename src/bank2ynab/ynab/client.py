from typing import Any
import requests


class YNABClient:
    """
    Abstracts YNAB API
    """

    API_ENDPOINT = "api.youneedabudget.com"
    API_VERSION = "v1"

    def __init__(self, *, api_token: str) -> None:
        if not api_token:
            raise ValueError("Invalid API token")

        self.auth_token = api_token
        self.client = requests.session()
        self.base_uri = f"https://{self.API_ENDPOINT}/{self.API_VERSION}"
        self.client.headers.update({"Authorization": f"Bearer {api_token}"})

    def list_budgets(self) -> Any:
        request_uri = f"{self.base_uri}/budget"
        res = self.client.get(url=request_uri)
        res.raise_for_status()

        return res.json().get("data", {})

    def get_budget(self, budget_id: str) -> Any:
        request_uri = f"{self.base_uri}/budget/{budget_id}"
        res = self.client.get(url=request_uri)
        res.raise_for_status()

        return res.json().get("data", {})

    def list_accounts(self, budget_id: str) -> Any:
        request_uri = f"{self.base_uri}/budget/{budget_id}/accounts"
        res = self.client.get(url=request_uri)
        res.raise_for_status()

        return res.json().get("data", {})

    def get_account(self, budget_id: str, account_id: str) -> Any:
        request_uri = f"{self.base_uri}/budget/{budget_id}/accounts/{account_id}"
        res = self.client.get(url=request_uri)
        res.raise_for_status()

        return res.json().get("data", {})