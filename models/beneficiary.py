from extensions import db
from flask_login import UserMixin
import uuid


def hexid():
    return uuid.uuid4().hex


# creating the User table in the database
class Beneficiary(db.Model, UserMixin):
    __tablename__ = "beneficiary"
    id = db.Column(db.String(100), default=hexid, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    account_number = db.Column(db.BigInteger)
    user_id = db.Column(db.String(100), db.ForeignKey("user.id"))

    # Define a representation with two attribute 'first_name' and 'last_name'
    def __repr__(self):
        return f"Beneficiary('{self.first_name}', '{self.last_name}')"


# bank beneficiary
class BankBeneficiary(db.Model, UserMixin):
    __tablename__ = "bank_beneficiary"
    id = db.Column(db.String(100), default=hexid, primary_key=True)
    full_name = db.Column(db.String(70))
    account_number = db.Column(db.String(50))
    bank_name = db.Column(db.String(50))
    bank_code = db.Column(db.String(50))
    user_id = db.Column(db.String(100), db.ForeignKey("user.id"))

    # Define a representation with two attribute 'first_name' and 'last_name'
    def __repr__(self):
        return f"BankBeneficiary('{self.full_name}', '{self.account_number}', '{self.bank_name}')"

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()


# save bank beneficiary
def save_bank_beneficiary(full_name, account_number, bank_name, bank_code, user_id):
    try:
        if BankBeneficiary.query.filter(
            BankBeneficiary.account_number == account_number,
            BankBeneficiary.user_id == user_id,
            BankBeneficiary.bank_code == bank_code,
            BankBeneficiary.bank_name.ilike(f"%{bank_name}%"),
        ).first():
            return None
        bank_ben = BankBeneficiary(
            full_name=full_name,
            account_number=account_number,
            bank_name=bank_name,
            bank_code=bank_code,
            user_id=user_id,
        )
        bank_ben.save()

        return bank_ben
    except Exception as e:
        print(e, "error in save_bank_beneficiary")
        db.session.rollback()
        return None


# get bank using bank id
def get_one_bank_beneficiary(bank_id):
    try:
        bank = BankBeneficiary.query.get(bank_id)
        return bank
    except Exception as e:
        print(e, "error in get_one_bank_beneficiary")
        db.session.rollback()
        return None
