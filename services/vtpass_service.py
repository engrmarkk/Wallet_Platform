from base import VtpassBase
import requests
import json
from dotenv import load_dotenv


load_dotenv()


class VtpassService(VtpassBase):
    def purchase_product(self, payload):
        print(payload, "payload")
        url = self.base_url + "/api/pay"
        headers = self.set_headers()
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print(response.status_code)
        print(response.json())
        return response.json(), response.status_code

    def purchase_data(self, payload):
        url = self.base_url + "/api/pay"
        headers = self.set_headers()
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print(response.status_code)
        print(response.json())
        return response.json(), response.status_code

    def purchase_electricity(self, payload):
        pass

    def purchase_cable(self, payload):
        pass

    def service_identifier(self, service_id):
        try:
            url = self.base_url + f"/api/services?identifier={service_id}"
            response = requests.get(
                url, self.set_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(e)
            return None

    def variation_codes(self, service_id):
        try:
            url = self.base_url + f"/api/service-variations?serviceID={service_id}"
            response = requests.get(
                url, self.set_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(e)
            return None

    def verify_meter_and_smartcard_number(self, payload):
        try:
            print(payload, "payload")
            print(self.set_headers(), "headers")
            url = self.base_url + "/api/merchant-verify"
            # url = "https://sandbox.vtpass.com/api/merchant-verify"
            response = requests.post(
                url, headers=self.set_headers(), data=json.dumps(payload)
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(e)
            return None
