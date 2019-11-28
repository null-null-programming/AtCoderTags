from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from requests_oauthlib import OAuth1Session
from flask_migrate import Migrate
import os
import subprocess

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["SQLALCHEMY_DATABASE_URI"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db=SQLAlchemy(app)
migrate=Migrate(app,db)

### Constants                                                                                                                                                     
oath_key_dict = {
    "consumer_key": os.environ["consumer_key"],
    "consumer_secret": os.environ["consumer_secret"],
    "access_token": os.environ["access_token"],
    "access_token_secret": os.environ["access_token_secret"]
}