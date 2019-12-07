from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from collections import defaultdict
from config import *
import numpy
import json
import time
import requests


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.String(64))
    tag = db.Column(db.String(64))


class problem_tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    problem_official_name = db.Column(db.String(64))
    # first_tag:最も表の多いTag
    first_tag = db.Column(db.String(64))


@app.route("/")
def index():
    category_list = [
        "Easy",
        "Searching",
        "Greedy-Methods",
        "String",
        "Mathematics",
        "Technique",
        "Construct",
        "Graph",
        "Dynamic-Programming",
        "Data-Structure",
        "Game",
        "Flow-Algorithms",
        "Geometry",
    ]

    # 問題の総数を求める。
    get_problem = requests.get(
        "https://kenkoooo.com/atcoder/resources/merged-problems.json"
    )
    get_problem = get_problem.json()
    ALL_PROBLEM_NUM = len(get_problem)

    # 正式な問題名かをチェックするための辞書
    add = defaultdict(int)

    for problem in get_problem:
        add[problem["id"]] += 1

    # 投票済みの問題の総数を求める。
    list = db.session.query(problem_tag).all()
    VOTED_PROBLEM_NUM = 0

    for tag in list:
        # 正しいカテゴリーかチェック
        for category in category_list:
            if tag.first_tag == category:
                # 問題名が正式かつタグのカテゴリーも正しいものならば総数に１加算される
                VOTED_PROBLEM_NUM += add[tag.problem_official_name]
                break

    # 投票済みパーセンテージ
    PERCENTAGE = round((VOTED_PROBLEM_NUM / ALL_PROBLEM_NUM) * 100, 3)

    return render_template("index.html", percentage=PERCENTAGE)


@app.route("/explain")
def explain():
    return render_template("tag_explain.html")


@app.route("/tag_search/<tag_name>")
def tag_search(tag_name):
    # コンテスト名取得のため、AtCoderProblemsAPIを利用する。
    get_problem = requests.get(
        "https://kenkoooo.com/atcoder/resources/merged-problems.json"
    )
    get_problem = get_problem.json()

    tagName = tag_name
    problems = db.session.query(problem_tag).filter_by(first_tag=tagName)

    dict = {}

    # 最新のコンテストの場合、API反映までに時間がかかるため、バグらせないように以下の処理をする必要がある。
    for problem in problems:
        dict[str(problem.problem_official_name)] = {
            "contest_id": problem.problem_official_name,
            "title": "Error",
            "solver_count": -1,
            "predict": -1,
        }

    # official_nameからコンテスト名を得るために辞書を作成する。
    for problem in get_problem:
        dict[str(problem["id"])] = problem

        if dict[str(problem["id"])]["predict"] == None:
            dict[str(problem["id"])]["predict"] = -1

        if dict[str(problem["id"])]["solver_count"] == None:
            dict[str(problem["id"])]["solver_count"] = -1

    # 問題を解かれた人数で並び替える。predictで並び替えるとnullがあるので死ぬ。
    problems = sorted(
        problems,
        key=lambda x: (
            dict[str(x.problem_official_name)]["solver_count"],
            -dict[str(x.problem_official_name)]["predict"],
        ),
        reverse=True,
    )

    return render_template(
        "tag_search.html", tagName=tagName, problems=problems, dict=dict
    )


@app.route("/tag_search/<tag_name>/<user_id>")
def user_tag_search(tag_name, user_id):
    # コンテスト名およびuser情報取得のため、AtCoderProblemsAPIを利用する。
    get_problem = requests.get(
        "https://kenkoooo.com/atcoder/resources/merged-problems.json"
    )
    get_user_info = requests.get(
        str("https://kenkoooo.com/atcoder/atcoder-api/results?user=" + user_id)
    )
    get_problem = get_problem.json()
    get_user_info = get_user_info.json()

    # コンテスト名取得
    ############################################################################################################
    tagName = tag_name
    problems = db.session.query(problem_tag).filter_by(first_tag=tagName)

    dict = {}

    # 最新のコンテストの場合、API反映までに時間がかかるため、バグらせないように以下の処理をする必要がある。
    for problem in problems:
        dict[str(problem.problem_official_name)] = {
            "contest_id": problem.problem_official_name,
            "title": "Error",
            "solver_count": -1,
            "predict": -1,
        }

    # official_nameからコンテスト名を得るために辞書を作成する。
    for problem in get_problem:
        dict[str(problem["id"])] = problem

        if dict[str(problem["id"])]["predict"] == None:
            dict[str(problem["id"])]["predict"] = -1

    # 問題を解かれた人数で並び替える。predictで並び替えるとnullがあるので死ぬ。
    problems = sorted(
        problems,
        key=lambda x: (
            dict[str(x.problem_official_name)]["solver_count"],
            -dict[str(x.problem_official_name)]["predict"],
        ),
        reverse=True,
    )

    ############################################################################################################

    # 以下user情報取得

    user_dict = {}

    # はじめに全ての問題をWAとする。
    for problem in problems:
        user_dict[str(problem.problem_official_name)] = "WA"

    # その後、ACの問題が見つかり次第、書き換える。
    for info in get_user_info:
        if info["result"] == "AC":
            user_dict[str(info["problem_id"])] = "AC"

    return render_template(
        "user_tag_search.html",
        tagName=tagName,
        problems=problems,
        dict=dict,
        user_id=user_id,
        user_dict=user_dict,
    )


@app.route("/vote")
def vote():
    return render_template("vote.html")


@app.route("/vote_result")
def vote_result():
    problem_id = request.args.get("problem_id")
    tag = request.args.get("tag")

    # 白紙投票がある場合
    if problem_id == "" or tag == None:
        return render_template("error.html")

    newTag = Tag(problem_id=problem_id, tag=tag)
    db.session.add(newTag)
    db.session.commit()

    search_tag = (
        db.session.query(problem_tag)
        .filter_by(problem_official_name=problem_id)
        .first()
    )

    # Tagが存在しない場合、投票されたTagがその問題のジャンルになる。
    if search_tag == None:
        tag_params = {"problem_official_name": problem_id, "first_tag": tag}
        newProblemTag = problem_tag(**tag_params)
        db.session.add(newProblemTag)
        db.session.commit()

    # Tagが存在する場合、その問題に投票された全てのTagを集計し直し、ジャンルを決定する。
    else:
        tags = db.session.query(Tag).filter(Tag.problem_id == problem_id)
        vote_num = defaultdict(int)

        for t in tags:
            vote_num[t.tag] += 1

        vote_num = sorted(vote_num.items(), key=lambda x: x[1], reverse=True)

        tag_ = None
        if len(vote_num) != 0:
            tag_ = vote_num[0][0]

        if tag != None:
            search_tag.first_tag = tag_
            db.session.commit()

    return render_template("success.html")


@app.route("/check")
def check():
    return render_template("check_problem.html")


@app.route("/check/<problem_id>")
def check_problem(problem_id):
    tag = (
        db.session.query(problem_tag)
        .filter_by(problem_official_name=problem_id)
        .first()
    )

    if tag == None:
        return render_template("check_error.html")
    else:
        tag_name = tag.first_tag

        # 各ジャンルタグ数
        sum_dict = {
            "Easy": 0,
            "Searching": 0,
            "Greedy-Methods": 0,
            "String": 0,
            "Mathematics": 0,
            "Technique": 0,
            "Construct": 0,
            "Graph": 0,
            "Dynamic-Programming": 0,
            "Data-Structure": 0,
            "Game": 0,
            "Flow-Algorithms": 0,
            "Geometry": 0,
        }

        tags = db.session.query(Tag).filter_by(problem_id=problem_id).all()

        for i in tags:
            sum_dict[i.tag] += 1

        return render_template(
            "check_problem_result.html", tag_name=tag_name, dict=sum_dict
        )


@app.route("/graph")
def graph():
    # ジャンル
    category_list = [
        "Easy",
        "Searching",
        "Greedy-Methods",
        "String",
        "Mathematics",
        "Technique",
        "Construct",
        "Graph",
        "Dynamic-Programming",
        "Data-Structure",
        "Game",
        "Flow-Algorithms",
        "Geometry",
    ]

    # 各ジャンルの問題総数
    sum_dict = {
        "Easy": 0,
        "Searching": 0,
        "Greedy-Methods": 0,
        "String": 0,
        "Mathematics": 0,
        "Technique": 0,
        "Construct": 0,
        "Graph": 0,
        "Dynamic-Programming": 0,
        "Data-Structure": 0,
        "Game": 0,
        "Flow-Algorithms": 0,
        "Geometry": 0,
    }

    for category in category_list:
        problem_list = db.session.query(problem_tag).filter_by(first_tag=category).all()
        sum_dict[category] = len(problem_list)

    return render_template("graph.html", sum_dict=sum_dict)


@app.route("/graph/<user_id>")
def user_graph(user_id):
    # AtCoderAPIからUser情報を取得する
    get_user_info = requests.get(
        str("https://kenkoooo.com/atcoder/atcoder-api/results?user=" + user_id)
    )
    get_user_info = get_user_info.json()

    # ジャンルリスト
    category_list = [
        "Easy",
        "Searching",
        "Greedy-Methods",
        "String",
        "Mathematics",
        "Technique",
        "Construct",
        "Graph",
        "Dynamic-Programming",
        "Data-Structure",
        "Game",
        "Flow-Algorithms",
        "Geometry",
    ]

    # ジャンル別の問題総数
    sum_dict = {
        "Easy": 0,
        "Searching": 0,
        "Greedy-Methods": 0,
        "String": 0,
        "Mathematics": 0,
        "Technique": 0,
        "Construct": 0,
        "Graph": 0,
        "Dynamic-Programming": 0,
        "Data-Structure": 0,
        "Game": 0,
        "Flow-Algorithms": 0,
        "Geometry": 0,
    }

    # ユーザーが各ジャンルの問題を何問解いたか
    user_sum_dict = {
        "Easy": 0,
        "Searching": 0,
        "Greedy-Methods": 0,
        "String": 0,
        "Mathematics": 0,
        "Technique": 0,
        "Construct": 0,
        "Graph": 0,
        "Dynamic-Programming": 0,
        "Data-Structure": 0,
        "Game": 0,
        "Flow-Algorithms": 0,
        "Geometry": 0,
    }

    # ジャンル毎にUserが何％ACしているか
    percent_dict = {
        "Easy": 0,
        "Searching": 0,
        "Greedy-Methods": 0,
        "String": 0,
        "Mathematics": 0,
        "Technique": 0,
        "Construct": 0,
        "Graph": 0,
        "Dynamic-Programming": 0,
        "Data-Structure": 0,
        "Game": 0,
        "Flow-Algorithms": 0,
        "Geometry": 0,
    }

    ###########################################################################################
    # ACリスト作成

    # userがその問題をACしているかどうかのリスト
    user_dict = {}
    # タグ付けされている全ての問題
    all_problems = db.session.query(problem_tag).all()
    # 一旦、全てをWAとする。
    for problem in all_problems:
        user_dict[str(problem.problem_official_name)] = "WA"
    # その後、ACの問題が見つかり次第、書き換える。
    for info in get_user_info:
        if info["result"] == "AC":
            user_dict[str(info["problem_id"])] = "AC"
    ############################################################################################

    for category in category_list:
        problem_list = db.session.query(problem_tag).filter_by(first_tag=category).all()
        sum_dict[category] = len(problem_list)

        for problem in problem_list:
            if user_dict[problem.problem_official_name] == "AC":
                user_sum_dict[category] = user_sum_dict[category] + 1

        if sum_dict[category] == 0:
            percent_dict[category] = 0
        else:
            percent_dict[category] = int(
                (user_sum_dict[category] / sum_dict[category]) * 100
            )

    return render_template(
        "user_graph.html", dict=percent_dict, user_id=user_id, sum_dict=sum_dict
    )


@app.route("/graph/<user_id>/<rival_id>")
def user_and_rival_graph(user_id, rival_id):
    # AtCoderAPIからUser情報を取得する
    get_user_info = requests.get(
        str("https://kenkoooo.com/atcoder/atcoder-api/results?user=" + user_id)
    )
    get_user_info = get_user_info.json()

    get_rival_info = requests.get(
        str("https://kenkoooo.com/atcoder/atcoder-api/results?user=" + rival_id)
    )
    get_rival_info = get_rival_info.json()

    # ジャンルリスト
    category_list = [
        "Easy",
        "Searching",
        "Greedy-Methods",
        "String",
        "Mathematics",
        "Technique",
        "Construct",
        "Graph",
        "Dynamic-Programming",
        "Data-Structure",
        "Game",
        "Flow-Algorithms",
        "Geometry",
    ]

    # ジャンル別の問題総数
    sum_dict = {
        "Easy": 0,
        "Searching": 0,
        "Greedy-Methods": 0,
        "String": 0,
        "Mathematics": 0,
        "Technique": 0,
        "Construct": 0,
        "Graph": 0,
        "Dynamic-Programming": 0,
        "Data-Structure": 0,
        "Game": 0,
        "Flow-Algorithms": 0,
        "Geometry": 0,
    }

    # ユーザーが各ジャンルの問題を何問解いたか
    user_sum_dict = {
        "Easy": 0,
        "Searching": 0,
        "Greedy-Methods": 0,
        "String": 0,
        "Mathematics": 0,
        "Technique": 0,
        "Construct": 0,
        "Graph": 0,
        "Dynamic-Programming": 0,
        "Data-Structure": 0,
        "Game": 0,
        "Flow-Algorithms": 0,
        "Geometry": 0,
    }

    rival_sum_dict = {
        "Easy": 0,
        "Searching": 0,
        "Greedy-Methods": 0,
        "String": 0,
        "Mathematics": 0,
        "Technique": 0,
        "Construct": 0,
        "Graph": 0,
        "Dynamic-Programming": 0,
        "Data-Structure": 0,
        "Game": 0,
        "Flow-Algorithms": 0,
        "Geometry": 0,
    }

    # ジャンル毎にUserが何％ACしているか
    percent_dict = {
        "Easy": 0,
        "Searching": 0,
        "Greedy-Methods": 0,
        "String": 0,
        "Mathematics": 0,
        "Technique": 0,
        "Construct": 0,
        "Graph": 0,
        "Dynamic-Programming": 0,
        "Data-Structure": 0,
        "Game": 0,
        "Flow-Algorithms": 0,
        "Geometry": 0,
    }

    rival_percent_dict = {
        "Easy": 0,
        "Searching": 0,
        "Greedy-Methods": 0,
        "String": 0,
        "Mathematics": 0,
        "Technique": 0,
        "Construct": 0,
        "Graph": 0,
        "Dynamic-Programming": 0,
        "Data-Structure": 0,
        "Game": 0,
        "Flow-Algorithms": 0,
        "Geometry": 0,
    }

    ###########################################################################################
    # ACリスト作成

    # userがその問題をACしているかどうかのリスト
    user_dict = {}
    rival_dict = {}

    # タグ付けされている全ての問題
    all_problems = db.session.query(problem_tag).all()
    # 一旦、全てをWAとする。
    for problem in all_problems:
        user_dict[str(problem.problem_official_name)] = "WA"
        rival_dict[str(problem.problem_official_name)] = "WA"

    # その後、ACの問題が見つかり次第、書き換える。
    for info in get_user_info:
        if info["result"] == "AC":
            user_dict[str(info["problem_id"])] = "AC"

    for info in get_rival_info:
        if info["result"] == "AC":
            rival_dict[str(info["problem_id"])] = "AC"
    ############################################################################################

    for category in category_list:
        problem_list = db.session.query(problem_tag).filter_by(first_tag=category).all()
        sum_dict[category] = len(problem_list)

        for problem in problem_list:
            if user_dict[problem.problem_official_name] == "AC":
                user_sum_dict[category] = user_sum_dict[category] + 1
            if rival_dict[problem.problem_official_name] == "AC":
                rival_sum_dict[category] = rival_sum_dict[category] + 1

        if sum_dict[category] == 0:
            percent_dict[category] = 0
            rival_percent_dict[category] = 0
        else:
            percent_dict[category] = int(
                (user_sum_dict[category] / sum_dict[category]) * 100
            )
            rival_percent_dict[category] = int(
                (rival_sum_dict[category] / sum_dict[category]) * 100
            )

    return render_template(
        "user_and_rival_graph.html",
        user_dict=percent_dict,
        rival_dict=rival_percent_dict,
        user_id=user_id,
        rival_id=rival_id,
        sum_dict=sum_dict,
    )


@app.route("/collect")
def collect():
    return render_template("collect.html")


@app.route("/collect/<user_id>")
def user_collect(user_id):
    # コンテスト名およびuser情報取得のため、AtCoderProblemsAPIを利用する。
    get_problem = requests.get(
        "https://kenkoooo.com/atcoder/resources/merged-problems.json"
    )
    get_user_info = requests.get(
        str("https://kenkoooo.com/atcoder/atcoder-api/results?user=" + user_id)
    )
    get_problem = get_problem.json()
    get_user_info = get_user_info.json()

    category_list = [
        "Easy",
        "Searching",
        "Greedy-Methods",
        "String",
        "Mathematics",
        "Technique",
        "Construct",
        "Graph",
        "Dynamic-Programming",
        "Data-Structure",
        "Game",
        "Flow-Algorithms",
        "Geometry",
    ]

    # 各カテゴリーの出題確率
    probability = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    problem_sum = 0
    SIZE = len(category_list)

    for i in range(0, SIZE):
        num = db.session.query(problem_tag).filter_by(first_tag=category_list[i]).all()
        probability[i] = len(num)
        problem_sum += len(num)

    probability_sum = 0
    for i in range(0, SIZE - 1):
        probability[i] = probability[i] / problem_sum
        probability_sum += probability[i]

    probability[SIZE - 1] = 1 - probability_sum

    return_list = []
    problem_set = set()
    timer = 0

    while True:

        if len(return_list) > 3:
            break

        timer += 1
        if timer > 100:
            break

        # ランダムにカテゴリーを選ぶ
        tagName = numpy.random.choice(category_list, p=probability)
        problems = db.session.query(problem_tag).filter_by(first_tag=tagName)

        dict = {}

        # 最新のコンテストの場合、API反映までに時間がかかるため、バグらせないように以下の処理をする必要がある。
        for problem in problems:
            dict[str(problem.problem_official_name)] = {
                "contest_id": problem.problem_official_name,
                "title": "Error",
                "solver_count": -1,
                "predict": -1,
            }

        # official_nameからコンテスト名を得るために辞書を作成する。
        for problem in get_problem:
            dict[str(problem["id"])] = problem

            if dict[str(problem["id"])]["predict"] == None:
                dict[str(problem["id"])]["predict"] = -1

            if dict[str(problem["id"])]["solver_count"] == None:
                dict[str(problem["id"])]["solver_count"] = -1

        # 問題を解かれた人数で並び替える。predictで並び替えるとnullがあるので死ぬ。
        problems = sorted(
            problems,
            key=lambda x: (
                dict[str(x.problem_official_name)]["solver_count"],
                -dict[str(x.problem_official_name)]["predict"],
            ),
            reverse=True,
        )

        ############################################################################################################

        # 以下user情報取得

        user_dict = {}

        # はじめに全ての問題をWAとする。
        for problem in problems:
            user_dict[str(problem.problem_official_name)] = "WA"
            if dict[str(problem.problem_official_name)] == "Error":
                user_dict[str(problem.problem_official_name)] = "Error"

        # その後、ACの問題が見つかり次第、書き換える。
        for info in get_user_info:
            if info["result"] == "AC":
                user_dict[str(info["problem_id"])] = "AC"

        # 総AC数をカウントする
        AC_Count = 0
        for problem in problems:
            if user_dict[problem.problem_official_name] == "AC":
                AC_Count += 1

        # 返す問題は「ACしたことのある問題の中央値」の一つ前または一つ後ろの問題
        now = 0
        target = int(AC_Count / 2)
        for problem in problems:
            if user_dict[problem.problem_official_name] == "AC":
                now += 1

            if now >= target and user_dict[problem.problem_official_name] == "WA":
                if problem.problem_official_name in problem_set:
                    continue

                problem_set.add(problem.problem_official_name)
                return_list.append(dict[problem.problem_official_name])
                break

        now = 0
        problems.reverse()
        for problem in problems:
            if user_dict[problem.problem_official_name] == "AC":
                now += 1

            if now >= target and user_dict[problem.problem_official_name] == "WA":
                if problem.problem_official_name in problem_set:
                    continue

                problem_set.add(problem.problem_official_name)
                return_list.append(dict[problem.problem_official_name])
                break

    return render_template("user_collect.html", dict_list=return_list)


@app.route("/tags/<tag>")
def explain_tag(tag):
    html_name = tag + ".html"
    return render_template(html_name)


@app.route("/tags/<first_tag>/<second_tag>")
def explain_second_tag(first_tag, second_tag):
    #TODO
    return

