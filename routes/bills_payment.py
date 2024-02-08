from datetime import datetime

from werkzeug.exceptions import RequestEntityTooLarge

from extensions import mail, db
from flask_mail import Message
from flask_login import current_user, login_required
from flask import redirect, url_for, flash, request, \
    render_template, Blueprint, make_response, jsonify
from models import User, Transaction, Beneficiary, Card, Invitees
from form import *
# from func import check_user_activity
from werkzeug.security import generate_password_hash
import random
import datetime
import cloudinary
import os
import requests
import cloudinary.uploader
import cloudinary_config
from routes.auth import login

bills = Blueprint("bills", __name__, template_folder='../templates')
