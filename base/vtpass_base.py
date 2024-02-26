import os
from base64 import b64encode


class VtpassBase:
    email = os.getenv("VTPASS_EMAIL")
    password = os.getenv("VTPASS_PASSWORD")
    api_key = os.getenv("VTPASS_API_KEY")
    pub_key = os.getenv("VTPASS_PUBLIC_KEY")
    secret_key = os.getenv("VTPASS_SECRET_KEY")
    base_url = os.getenv("VTPASS_BASE_URL")

    print("email: ", email, "password: ", password, "api_key: ", api_key, "pub_key: ",
          pub_key, "secret_key: ", secret_key, "base_url: ", base_url)

    def __init__(self):
        self.__login_creds = {"email": self.email, "password": self.password}
        test_auth_ = f"{self.email}:{self.password}".encode()
        self.test_auth = f"Basic {b64encode(test_auth_).decode()}"

        print(self.test_auth, "test_auth")

    def set_headers(self):
        headers = {
            "Content-Type": "application/json",
            # "Authorization": self.test_auth,
            "api-key": self.api_key,
            "secret-key": self.secret_key
        }

        return headers
