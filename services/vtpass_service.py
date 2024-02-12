from base import VtpassBase
import requests


class VtpassService(VtpassBase):
    def purchase_airtime(self, payload):

        url = self.url + "/api/pay"
        response = requests.post(
            url, self.headers, json=payload
        )
        response.raise_for_status()
        print(response.status_code)
        print(response.json())
        return response.json(), response.status_code

    def purchase_data(self, payload):
        pass

    def purchase_electricity(self, payload):
        pass

    def purchase_cable(self, payload):
        pass
