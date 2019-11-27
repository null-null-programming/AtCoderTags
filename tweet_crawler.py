#!/usr/bin/env python
# -*- coding:utf-8 -*-

from requests_oauthlib import OAuth1Session
from datetime import datetime, timedelta
from secret_key import *
import json
import time

#スクレイピングする間隔:10分
SLEEP_TIME = 15 * 60


### Functions
def main():
    #これまでに見てきた中で最も大きいid
    MAX_ID = -1
    NEXT_MAX_ID = -1
    next_max_id = -1

    max_id = -1
    url = 'https://api.twitter.com/1.1/search/tweets.json'
    keyword = '#Python'
    count = 100
    params = {'q': keyword, 'count': count, 'max_id': max_id, 'lang': 'en'}

    twitter = create_oath_session(oath_key_dict)

    while (True):
        if max_id != -1:
            params['max_id'] = max_id - 1
        req = twitter.get(url, params=params)

        if req.status_code == 200:
            search_timeline = json.loads(req.text)

            #全てのツイートを取得した場合、最新ツイートに戻る。
            if search_timeline['statuses'] == []:
                max_id = -1
                params['max_id'] = -1
                req = twitter.get(url, params=params)
                search_timeline = json.loads(req.text)

                time.sleep(SLEEP_TIME)

                continue
            else:
                if max_id == -1:
                    NEXT_MAX_ID = search_timeline['statuses'][0]['id']

            max_id = search_timeline['statuses'][-1]['id']
            flag = False

            for tweet in search_timeline['statuses']:

                #既に見たツイートまで来た場合、最新ツイートに戻る。
                if tweet['id'] == MAX_ID:

                    while True:
                        max_id = -1
                        params['max_id'] = -1
                        req = twitter.get(url, params=params)
                        search_timeline = json.loads(req.text)

                        time.sleep(SLEEP_TIME)

                        if search_timeline['statuses'][0]['id'] != MAX_ID:
                            NEXT_MAX_ID = search_timeline['statuses'][0]['id']
                            max_id = -1
                            flag = True
                            break

                    break

                text = tweet['text']
                print(text)
                print(
                    '#################################################################################'
                )

            time.sleep(SLEEP_TIME)

            if flag:

                for tweet in search_timeline['statuses']:

                    #既に見たツイートまで来た場合、最新ツイートに戻る。
                    if tweet['id'] == MAX_ID:
                        break

                    text = tweet['text']
                    print(text)
                    print(
                        '#################################################################################'
                    )

            MAX_ID = NEXT_MAX_ID

        else:
            print('{}秒待ちます'.format(SLEEP_TIME))
            time.sleep(SLEEP_TIME)


def create_oath_session(oath_key_dict):
    oath = OAuth1Session(oath_key_dict["consumer_key"],
                         oath_key_dict["consumer_secret"],
                         oath_key_dict["access_token"],
                         oath_key_dict["access_token_secret"])
    return oath


### Execute
if __name__ == "__main__":
    main()
