from app_config import create_app, db
from extensions import sess
from models import (
    User,
    Invitees,
    Beneficiary,
    Transaction,
    Card,
    TransactionCategories,
    UserSession,
    Admin,
    BankBeneficiary,
)
from dotenv import load_dotenv
import os


app = create_app()

load_dotenv()


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "Invitees": Invitees,
        "Beneficiary": Beneficiary,
        "Transaction": Transaction,
        "Card": Card,
        "TransactionCategories": TransactionCategories,
        "UserSession": UserSession,
        "Admin": Admin,
        "BankBeneficiary": BankBeneficiary,
    }


if __name__ == "__main__":
    app.secret_key = os.environ.get("SECRET_KEY")
    app.config["SESSION_TYPE"] = "filesystem"
    sess.init_app(app)
    app.run(debug=True, host="0.0.0.0", port=4000)
