from app_config import create_app, db
from extensions import sess
from models import User, Invitees, Beneficiary, Transaction, Card
from dotenv import load_dotenv


app = create_app()

load_dotenv()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Invitees': Invitees, 'Beneficiary': Beneficiary, 'Transaction': Transaction,
            'Card': Card}


if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    sess.init_app(app)
    app.run()
