from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from collections import defaultdict
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
    #問題の総数を求める。
    get_problem=requests.get('https://kenkoooo.com/atcoder/resources/merged-problems.json')
    get_problem=get_problem.json()
    ALL_PROBLEM_NUM=len(get_problem)

    #投票済みの問題の総数を求める。
    list=db.session.query(problem_tag).all()
    VOTED_PROBLEM_NUM=len(list)

    #投票済みパーセンテージ
    PERCENTAGE=round((VOTED_PROBLEM_NUM/ALL_PROBLEM_NUM)*100,3)

    return render_template('index.html',percentage=PERCENTAGE)

@app.route('/explain')
def explain():
    return render_template('tag_explain.html')

@app.route('/category')
def category():
    return render_template('category.html')


@app.route('/tag_search/<tag_name>')
def tag_search(tag_name):
    #コンテスト名取得のため、AtCoderProblemsAPIを利用する。
    get_problem=requests.get('https://kenkoooo.com/atcoder/resources/merged-problems.json')
    get_problem=get_problem.json()

    tagName = tag_name
    problems = db.session.query(problem_tag).filter_by(first_tag=tagName)

    dict={}

    #最新のコンテストの場合、API反映までに時間がかかるため、バグらせないように以下の処理をする必要がある。
    for problem in problems:
        dict[str(problem.problem_official_name)]={"contest_id":problem.problem_official_name,"title":"しばらくお待ち下さい","solver_count":-1,"predict":-1}
    
    #official_nameからコンテスト名を得るために辞書を作成する。
    for problem in get_problem:
        dict[str(problem['id'])]=problem

        if dict[str(problem['id'])]['predict']==None:
            dict[str(problem['id'])]['predict']=-1
    
    #問題を解かれた人数で並び替える。predictで並び替えるとnullがあるので死ぬ。
    problems=sorted(problems,key=lambda x:(dict[str(x.problem_official_name)]["solver_count"],-dict[str(x.problem_official_name)]["predict"]),reverse=True)

    return render_template('tag_search.html', tagName=tagName,problems=problems,dict=dict)

@app.route('/tag_search/<tag_name>/<user_id>')
def user_tag_search(tag_name,user_id):
    #コンテスト名およびuser情報取得のため、AtCoderProblemsAPIを利用する。
    get_problem=requests.get('https://kenkoooo.com/atcoder/resources/merged-problems.json')
    get_user_info=requests.get(str('https://kenkoooo.com/atcoder/atcoder-api/results?user='+user_id))
    get_problem=get_problem.json()
    get_user_info=get_user_info.json()

    #コンテスト名取得
    ############################################################################################################
    tagName = tag_name
    problems = db.session.query(problem_tag).filter_by(first_tag=tagName)

    dict={}

    #最新のコンテストの場合、API反映までに時間がかかるため、バグらせないように以下の処理をする必要がある。
    for problem in problems:
        dict[str(problem.problem_official_name)]={"contest_id":problem.problem_official_name,"title":"しばらくお待ち下さい","solver_count":-1,"predict":-1}
    
    #official_nameからコンテスト名を得るために辞書を作成する。
    for problem in get_problem:
        dict[str(problem['id'])]=problem

        if dict[str(problem['id'])]['predict']==None:
            dict[str(problem['id'])]['predict']=-1
    
    #問題を解かれた人数で並び替える。predictで並び替えるとnullがあるので死ぬ。
    problems=sorted(problems,key=lambda x:(dict[str(x.problem_official_name)]["solver_count"],-dict[str(x.problem_official_name)]["predict"]),reverse=True)

    ############################################################################################################

    #以下user情報取得

    user_dict={}

    #はじめに全ての問題をWAとする。
    for problem in problems:
        user_dict[str(problem.problem_official_name)]="WA"
    
    #その後、ACの問題が見つかり次第、書き換える。
    for info in get_user_info:
        if info["result"]=="AC":
            user_dict[str(info["problem_id"])]="AC"

    return render_template('user_tag_search.html', tagName=tagName,problems=problems,dict=dict,user_id=user_id,user_dict=user_dict)

@app.route('/vote')
def vote():
    return render_template('vote.html')

@app.route('/vote_result',methods=['POST'])
def vote_result():
    problem_id=request.form['problem_id']
    tag=request.form['tag']

    #白紙投票がある場合
    if problem_id=="" or tag=="":
        return render_template('error.html')

    newTag=Tag(problem_id=problem_id,tag=tag)
    db.session.add(newTag)
    db.session.commit()

    search_tag=db.session.query(problem_tag).filter_by(problem_official_name=problem_id).first()

    #Tagが存在しない場合、投票されたTagがその問題のジャンルになる。
    if search_tag==None:
        tag_params={
            'problem_official_name':problem_id,
            'first_tag':tag
        }
        newProblemTag=problem_tag(**tag_params)
        db.session.add(newProblemTag)
        db.session.commit()

    #Tagが存在する場合、その問題に投票された全てのTagを集計し直し、ジャンルを決定する。
    else:
        tags=db.session.query(Tag).filter(Tag.problem_id==problem_id)
        vote_num=defaultdict(int)

        for t in tags:
            vote_num[t.tag]+=1
        
        vote_num= sorted(vote_num.items(), key=lambda x:x[1],reverse=True)

        tag_=None
        if len(vote_num)!=0:
            tag_=vote_num[0][0]
        
        if tag !=None:
            search_tag.first_tag=tag_
            db.session.commit()
    
    return render_template('success.html')

@app.cli.command('initdb')
def initdb_command():
    db.create_all()
