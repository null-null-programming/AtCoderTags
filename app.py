from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from config import *
import json
import time
import requests

class Tag(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    problem_id=db.Column(db.String(64))
    tag=db.Column(db.String(64))

class problem_tag(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    problem_official_name=db.Column(db.String(64))
    #first_tag:最も表の多いTag
    first_tag=db.Column(db.String(64))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/category')
def category():
    return render_template('category.html')


@app.route('/tag_search', methods=['POST'])
def tag_search():
    #コンテスト名取得のため、AtCoderProblemsAPIを利用する。
    get_problem=requests.get('https://kenkoooo.com/atcoder/resources/problems.json')
    get_problem=get_problem.json()

    tagName = request.args.get('tagName')
    problems = db.session.query(problem_tag).filter_by(first_tag=tagName)

    dict={}
    for problem in get_problem:
        dict[str(problem['id'])]=problem

    return render_template('tag_search.html', tagName=tagName,problems=problems,dict=dict)

@app.cli.command('initdb')
def initdb_command():
    db.create_all()
