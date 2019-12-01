from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from collections import defaultdict
from apscheduler.schedulers.blocking import BlockingScheduler
from config import *
import json

sched = BlockingScheduler()

class Tag(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    problem_id=db.Column(db.String(64))
    tag=db.Column(db.String(64))

class problem_tag(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    problem_official_name=db.Column(db.String(64))
    #first_tag:最も表の多いTag
    first_tag=db.Column(db.String(64))

class id_list(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    MAX_ID=db.Column(db.String(64))
    now_max_id=db.Column(db.String(64))
    NEXT_MAX_ID=db.Column(db.String(64))

### Functions
@sched.scheduled_job('interval', minutes=1)
def crawler():
    MAX_ID_ = int(db.session.query(id_list).first().MAX_ID)
    now_max_id_ = int(db.session.query(id_list).first().now_max_id)
    NEXT_MAX_ID_ = int(db.session.query(id_list).first().NEXT_MAX_ID)

    print(MAX_ID_)
    print(now_max_id_)
    print(NEXT_MAX_ID_)

    url = 'https://api.twitter.com/1.1/search/tweets.json'
    keyword = '#AtCoderTags'
    count = 180
    params = {'q': keyword, 'count': count, 'max_id': now_max_id}

    twitter = create_oath_session(oath_key_dict)

    while (True):

        if now_max_id != -1:
            params['max_id'] = now_max_id - 1
        req = twitter.get(url, params=params)

        print(req.status_code)

        if req.status_code == 200:
            search_timeline = json.loads(req.text)

            #ツイートがない場合は終了
            if search_timeline['statuses'] == []:
                db.session.query(id_list).first().now_max_id='-1'
                db.session.commit()
                return
                
            else:
                #次のループ時に止まる場所であるNEXT_MAX_IDを指定。
                if now_max_id == -1:
                    NEXT_MAX_ID_ = int(search_timeline['statuses'][0]['id'])
                    db.session.query(id_list).first().NEXT_MAX_ID=str(NEXT_MAX_ID_)
                    db.session.commit()
                    
            for tweet in search_timeline['statuses']:

                #既に見たツイートまで来た場合、終了する。
                if tweet['id'] == MAX_ID_:
                    MAX_ID_=NEXT_MAX_ID_
                    now_max_id_=-1
                    db.session.query(id_list).first().MAX_ID=str(NEXT_MAX_ID_)
                    db.session.query(id_list).first().now_max_id='-1'                    
                    return
                else:
                    text = tweet['text'].split('/')

                    #  #AtCoderTags/problem_id/Tag/ の形式出ない場合、飛ばす
                    if len(text)<4:
                        continue

                    problem_id = text[1]
                    tag = text[2]

                    print(problem_id)
                    print(tag)

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
        
            MAX_ID_ = NEXT_MAX_ID_
            now_max_id = search_timeline['statuses'][-1]['id']
            db.session.query(id_list).first().MAX_ID=str(NEXT_MAX_ID_)
            db.session.query(id_list).first().now_max=str(now_max_id_)
            db.session.commit()
        else:
            return

def create_oath_session(oath_key_dict):
    oath = OAuth1Session(oath_key_dict["consumer_key"],
                         oath_key_dict["consumer_secret"],
                         oath_key_dict["access_token"],
                         oath_key_dict["access_token_secret"])
    return oath


sched.start()