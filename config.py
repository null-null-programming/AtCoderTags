from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from requests_oauthlib import OAuth1Session
from flask_migrate import Migrate
import os
import subprocess

app = Flask(__name__)

app.jinja_env.add_extension("jinja2.ext.loopcontrols")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["SQLALCHEMY_DATABASE_URI"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
