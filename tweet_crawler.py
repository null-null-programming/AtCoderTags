from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from collections import defaultdict
from config import *
import json
import time

class Tag(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    problem_id=db.Column(db.String(64))
    tag=db.Column(db.String(64))

class problem_tag(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    problem_official_name=db.Column(db.String(64))
    #first_tag:最も表の多いTag
    first_tag=db.Column(db.String(64))

#スクレイピングする間隔:15分
SLEEP_TIME = 15 * 60

### Functions
def main():
    #これまでに見てきた中で最も大きいid
    MAX_ID = -1
    NEXT_MAX_ID = -1

    max_id = -1
    url = 'https://api.twitter.com/1.1/search/tweets.json'
    keyword = '#HogeHogeTest'
    count = 1
    params = {'q': keyword, 'count': count, 'max_id': max_id, 'lang': 'en'}

    twitter = create_oath_session(oath_key_dict)

    while (True):
        if max_id != -1:
            params['max_id'] = max_id - 1
        req = twitter.get(url, params=params)

        if req.status_code == 200:
            search_timeline = json.loads(req.text)

            #ツイートがない場合は終了
            if search_timeline['statuses'] == []:
                return
            else:
                #次のループ時に止まる場所であるNEXT_MAX_IDを指定。
                if max_id == -1:
                    NEXT_MAX_ID = search_timeline['statuses'][0]['id']
            
            for tweet in search_timeline['statuses']:

                #既に見たツイートまで来た場合、終了する。
                if tweet['id'] == MAX_ID:
                    MAX_ID=NEXT_MAX_ID
                    return
                else:
                    text = tweet['text'].split('/')

                    #  #AtCoderTags/problem_id/Tag の形式出ない場合、飛ばす
                    if len(text)!=3:
                        continue

                    problem_id = text[1]
                    tag = text[2]

                    print(problem_id+":"+tag)

                    newTag=Tag(problem_id=problem_id,tag=tag)
                    db.session.add(newTag)
                    db.session.commit()

                    tag=db.session.query(problem_tag).filter_by(problem_official_name=problem_id).first()

                    #Tagが存在しない場合、投票されたTagがその問題のジャンルになる。
                    if tag==None:
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
        else:
            return


def create_oath_session(oath_key_dict):
    oath = OAuth1Session(oath_key_dict["consumer_key"],
                         oath_key_dict["consumer_secret"],
                         oath_key_dict["access_token"],
                         oath_key_dict["access_token_secret"])
    return oath


### Execute
if __name__ == "__main__":
    main()