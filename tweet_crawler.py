from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from collections import defaultdict
from apscheduler.schedulers.blocking import BlockingScheduler
from config import *
import json
import pickle

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

### Functions
@sched.scheduled_job('interval', minutes=1)
def crawler():
    with open('id.pickle', mode='rb') as f:
        id=pickle.load(f)
    
    MAX_ID = id['MAX_ID']
    max_id= id['max_id']
    NEXT_MAX_ID = id['NEXT_MAX_ID']

    url = 'https://api.twitter.com/1.1/search/tweets.json'
    keyword = '#AtCoderTags'
    count = 15
    params = {'q': keyword, 'count': count, 'max_id': max_id}

    twitter = create_oath_session(oath_key_dict)

    while (True):
        if max_id != -1:
            params['max_id'] = max_id - 1
        req = twitter.get(url, params=params)
        print(req.status_code)
        if req.status_code == 200:
            search_timeline = json.loads(req.text)

            #ツイートがない場合は終了
            if search_timeline['statuses'] == []:
                id['max_id']=-1

                with open('id.pickle',mode='wb') as f:
                    pickle.dump(id,f)
                return
            else:
                #次のループ時に止まる場所であるNEXT_MAX_IDを指定。
                if max_id == -1:
                    NEXT_MAX_ID = search_timeline['statuses'][0]['id']
                    id['NEXT_MAX_ID']=NEXT_MAX_ID

                    with open('id.pickle', mode='wb') as f:
                        pickle.dump(id, f)
                    
            for tweet in search_timeline['statuses']:

                #既に見たツイートまで来た場合、終了する。
                if tweet['id'] == MAX_ID:
                    MAX_ID=NEXT_MAX_ID
                    max_id=-1
                    id['MAX_ID']=NEXT_MAX_ID
                    id['max_id']=-1

                    with open('id.pickle', mode='wb') as f:
                        pickle.dump(id, f)
                                        
                    return
                else:
                    text = tweet['text'].split('/')
                    print(tweet['text'])

                    #  #AtCoderTags/problem_id/Tag/ の形式出ない場合、飛ばす
                    if len(text)<4:
                        continue

                    problem_id = text[1]
                    tag = text[2]

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
                            tag.first_tag=tag_
                            db.session.commit()
        
            MAX_ID = NEXT_MAX_ID
            max_id = search_timeline['statuses'][-1]['id']
            id['MAX_ID']=NEXT_MAX_ID
            id['max_id']=max_id

            with open('id.pickle', mode='wb') as f:
                pickle.dump(id,f)
            
        else:
            return

def create_oath_session(oath_key_dict):
    oath = OAuth1Session(oath_key_dict["consumer_key"],
                         oath_key_dict["consumer_secret"],
                         oath_key_dict["access_token"],
                         oath_key_dict["access_token_secret"])
    return oath


sched.start()