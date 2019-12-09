from flask import Flask, login_user, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from requests_oauthlib import OAuth1Session
from flask_migrate import Migrate
from flask_login import UserMixin, logout_user
from rauth import OAuth1Service
import os
import subprocess

app = Flask(__name__)

app.jinja_env.add_extension("jinja2.ext.loopcontrols")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["SQLALCHEMY_DATABASE_URI"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    user_image_url = db.Column(db.String(120), index=True, unique=True)
    twitter_id = db.Column(db.String(64), nullable=False, unique=True)


service = OAuth1Service(
    name="twitter",
    consumer_key=os.environ["consumer_key"],
    consumer_secret=os.environ["consumer_secret"],
    request_token_url="https://api.twitter.com/oauth/request_token",
    authorize_url="https://api.twitter.com/oauth/authorize",
    access_token_url="https://api.twitter.com/oauth/access_token",
    base_url="https://api.twitter.com/1.1",
)
