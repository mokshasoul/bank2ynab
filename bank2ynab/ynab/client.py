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
        self.base_ur = f"https://{self.API_ENDPOINT}/{self.API_VERSION}"
        self.client.headers.update({"Authorization": f"Bearer {api_token}"})

    def list_budgets(self) -> dict:
        request_uri = f"{self.base_ur}/budget"
        res = self.client.get(url=request_uri)

        if res.status_code >= 300:
            # TODO: raise error
            pass

        return res.json()["data"]

    def get_budget(self, budget_id: str) -> dict:
        request_uri = f"{self.base_ur}/budget/{budget_id}"
        res = self.client.get(url=request_uri)
        if res.status_code >= 300:
            # TODO: raise error
            pass

        return res.json()["data"]

    def list_accounts(self, budget_id: str) -> dict:
        request_uri = f"{self.base_ur}/budget/{budget_id}/accounts"
        res = self.client.get(url=request_uri)
        if res.status_code >= 300:
            # TODO: raise error
            pass

        return res.json()["data"]

    def get_account(self, budget_id: str, account_id: str) -> dict:
        request_uri = f"{self.base_ur}/budget/{budget_id}/accounts/{account_id}"
        res = self.client.get(url=request_uri)
        if res.status_code >= 300:
            # TODO: raise error
            pass

        return res.json()["data"]
