import os
from dotenv import load_dotenv


load_dotenv()


class PaystackBase:
    def __init__(self):
        try:
            self.url = "https://api.paystack.co"
            self.secret = os.environ.get("PAYSTACK_SECRET")
            self.header = {"Authorization": f"Bearer {self.secret}"}
            self.country = "nigeria"
        except Exception as e:
            print(e, "error from paystack base")
