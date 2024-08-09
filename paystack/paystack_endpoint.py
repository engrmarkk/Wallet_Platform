from .base import PaystackBase
import requests


class PaystackEndpoints(PaystackBase):
    def list_banks(self):
        try:
            url = f"{self.url}/bank?country={self.country}"
            response = requests.get(url, headers=self.header)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(e, "error from list_banks")
            return {}

    def resolve_account(self, account_number, bank_code):
        try:
            print(self.header, "header from resolve_account")
            url = f"{self.url}/bank/resolve?account_number={account_number}&bank_code={bank_code}"
            response = requests.get(url, headers=self.header)
            response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx and 5xx)

            # Debugging statements
            print(response.content.decode(), "response content from resolve_account")
            print(response.json(), "response JSON from resolve_account")

            return response.json(), response.status_code

        except requests.exceptions.HTTPError as http_err:
            # Handles HTTP errors (4xx, 5xx)
            print(f"HTTP error occurred: {http_err}")
            return {}, 500

        except requests.exceptions.RequestException as req_err:
            # Handles other requests exceptions (e.g., connection errors)
            print(f"Request exception occurred: {req_err}")
            return {}, 500

        except Exception as e:
            # Handles all other exceptions
            print(f"An error occurred: {e}")
            return {}, 500
