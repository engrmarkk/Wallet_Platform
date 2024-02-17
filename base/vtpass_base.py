import os


class VtpassBase:
    email = os.getenv("VTPASS_EMAIL")
    password = os.getenv("VTPASS_PASSWORD")
    api_key = os.getenv("VTPASS_API_KEY")
    pub_key = os.getenv("VTPASS_PUBLIC_KEY")
    secret_key = os.getenv("VTPASS_SECRET_KEY")
    base_url = os.getenv("VTPASS_BASE_URL")  # for testing only

    def __init__(self):
        self.__login_creds = {"email": self.email, "password": self.password}
        test_auth_ = f"{self.email}:{self.password}".encode()
        self.test_auth = f"Basic {b64encode(test_auth_).decode()}"

    def set_get_headers(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.test_auth,
            # "api-key": self.api_key,
            # "public-key": self.pub_key
        }

        return headers

    def set_post_headers(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.test_auth,
            # "api-key": self.api_key,
            # "public-key": self.pub_key
        }

        return headers
