from flask import Flask, redirect, url_for, session, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from requests_oauthlib import OAuth1Session
from flask_migrate import Migrate
from flask_login import (
    UserMixin,
    logout_user,
    LoginManager,
    login_user,
    current_user,
    login_required,
)
from rauth import OAuth1Service
import os
import subprocess

app = Flask(__name__)
CORS(app)

app.jinja_env.add_extension("jinja2.ext.loopcontrols")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"].replace(
    "postgres://", "postgresql://"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ["secret_key"]
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "index"
migrate = Migrate(app, db)

service = OAuth1Service(
    name="twitter",
    consumer_key=os.environ["consumer_key"],
    consumer_secret=os.environ["consumer_secret"],
    request_token_url="https://api.twitter.com/oauth/request_token",
    authorize_url="https://api.twitter.com/oauth/authenticate",
    access_token_url="https://api.twitter.com/oauth/access_token",
    base_url="https://api.twitter.com/1.1/",
)
