import os


class VtpassBase:
    def __init__(self):
        self.url = os.getenv("VTPASS_BASE_URL")
        self.headers = {"Content-Type": "application/json"}
        self.public_key = os.getenv("VTPASS_PUBLIC_KEY")
        self.secret_key = os.getenv("VTPASS_SECRET_KEY")
        self.api_key = os.getenv("VTPASS_API_KEY")
