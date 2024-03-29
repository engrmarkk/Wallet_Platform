from base import VtpassBase
import requests
import json


class VtpassService(VtpassBase):
    def purchase_airtime(self, payload):

        url = self.base_url + "/api/pay"
        headers = self.set_headers()
        response = requests.post(url, headers=headers, data=json.dumps(payload))
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
            url = self.base_url + f"/api/merchant-verify"
            response = requests.post(
                url, self.set_headers(), json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(e)
            return None
