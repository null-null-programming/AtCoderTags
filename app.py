from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
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
    tag_second =db.Column(db.String(64))


class problem_tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    problem_official_name = db.Column(db.String(64))
    # first_tag:最も表の多いTag
    first_tag = db.Column(db.String(64))
    second_tag=db.Column(db.String(64))

class User_(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    user_image_url = db.Column(db.String(120), index=True, unique=True)
    twitter_id = db.Column(db.String(64), nullable=False, unique=True)
    vote_count=db.Column(db.Integer)


name_dict={"Brute-Force":"全探索","Binary-Search":"二分探索","Ternary-Search":"三分探索","DFS":"深さ優先探索",
"BFS":"幅優先探索","Bit-Brute-Force":"bit全探索","Heuristic":"ヒューリスティック","Other":"その他","String-Operation":"文字列処理",
"Rolling-Hash":"ローリングハッシュ","Manacher":"Manacher","Suffix-Array":"Suffix-Array","Z-Algorithm":"Z-Algorithm",
"Trie":"Trie","Cumulative-Sum":"累積和","imos":"imos法","Two-Pointers":"尺取り法","Split-And-List":"半分全列挙",
"Square-Division":"平方分割","Divid-And-Conquer":"分割統治法","Doubling":"ダブリング","Shortest-Path":"最短経路",
"Minimum-Spanning-Tree":"最小全域木","LCA":"最小共通祖先","Strongly-Connected-Components":"強連結成分分解","Topological-Sort":"トポロジカルソート",
"Euler-Tour":"オイラーツアー","HL-Decomposition":"HL分解","Centroid-Decomposition":"重心分解","Check-Tree":"木の同型判定",
"Two-Edge-Connected-Components":"二重辺連結成分分解","Bi-Connected-Components":"二重頂点連結成分分解","Cycle-Basis":"サイクル基底",
"dfs-tree":"dfs木","Erdesh":"エルデシュガライの定理","Simple-DP":"基礎DP","String-DP":"文字列DP","Section-DP":"区間DP","Digit-DP":"桁DP",
"Tree-DP":"木DP","Every-Direction-DP":"全方位木DP","Bit-DP":"bitDP","Probability-DP":"確率DP","Expected-Value-DP":"期待値DP",
"Insert-DP":"挿入DP","Link-DP":"連結DP","Inline-DP":"インラインDP","Matrix-Power":"行列累乗","CHT":"Convex-Hull-Trick","Monge-DP":"Monge-DP",
"Alien-DP":"Alien-DP","Kitamasa":"きたまさ法","stack":"stack","queue":"queue","set":"set","map":"map","deque":"deque",
"multiset":"multiset","priority_queue":"priority_queue","Union-Find-Tree":"Union-Find-Tree","BIT":"Binary-Indexed-Tree","Segment-Tree":"Segment-Tree",
"Lazy-Segment-Tree":"Lazy-Segment-Tree","Sparse-Table":"Sparse-Table","WaveletMatrix":"WaveletMatrix","Persistent-Data-Structures":"永続データ構造",
"Balanced-Tree":"平衡二分探索木","Nim":"Nim","Grundy":"Grundy数","Backtrack":"後退解析","Mini-Max":"ミニマックス法","unique":"特殊な性質",
"Max-Flow":"最大流問題","Min-Cost-Flow":"最小費用流問題","Bipartite-Matching":"二部マッチング","Min-Cut":"最小カット","Burn":"燃やす埋める",
"Convex-Hull":"凸包","Declination-Sorting":"偏角ソート","Three-D":"三次元","Number":"整数","Combinatorics":"組み合わせ","Probability":"確率","Expected-Value":"期待値"}

@app.route("/")
def index():
    category_list = [
        "Easy",
        "Ad-Hoc",
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
    all_tag=db.session.query(Tag).all()

    ALL_VOTED_NUM=len(all_tag)

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

    return render_template("index.html", percentage=PERCENTAGE,voted_num=ALL_VOTED_NUM)


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
    tag2= request.args.get("tag2")

    # 白紙投票がある場合
    if problem_id == "" or tag == None:
        return render_template("error.html")
    
    if not current_user.is_anonymous:
        user=db.session.query(User_).filter_by(id=current_user.id).first()
        user.vote_count+=1
        db.session.commit()

    newTag = Tag(problem_id=problem_id, tag=tag,tag_second=tag2)
    db.session.add(newTag)
    db.session.commit()

    search_tag = (
        db.session.query(problem_tag)
        .filter_by(problem_official_name=problem_id)
        .first()
    )

    # Tagが存在しない場合、投票されたTagがその問題のジャンルになる。
    if search_tag == None:
        tag_params = {"problem_official_name": problem_id, "first_tag": tag,"second_tag":tag2}
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

        if search_tag.first_tag in ["Easy","Ad-Hoc","Greedy-Methods","Construct"]:
            search_tag.second_tag=None
            db.session.commit()
            return render_template("success.html")
        
        if tag2 != None:
            vote_num2 = defaultdict(int)

            second_tags=db.session.query(Tag).filter(Tag.problem_id==problem_id,Tag.tag==search_tag.first_tag)

            for t in second_tags:
                vote_num2[t.tag_second] += 1

            vote_num2 = sorted(vote_num2.items(), key=lambda x: x[1], reverse=True)

            tag_ = None
            if len(vote_num2) != 0:
                if vote_num2[0][0] !=None:
                    tag_ = vote_num2[0][0]
                elif len(vote_num2)>1:
                    tag_ = vote_num2[1][0]

            if tag != None:
                search_tag.second_tag = tag_
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
        second_tag=None

        if tag.second_tag!=None and tag.second_tag!='null':
            second_tag = name_dict[tag.second_tag]

        # 各ジャンルタグ数
        sum_dict = {
            "Easy":0,
            "Ad-Hoc":0,
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

        second_sum_dict=defaultdict(int)

        name_list=set()

        tags = db.session.query(Tag).filter_by(problem_id=problem_id).all()

        for i in tags:
            if i.tag!=None:
                sum_dict[i.tag] += 1
            if i.tag_second !=None and i.tag_second !='null':
                second_sum_dict[name_dict[i.tag_second]]+=1
                name_list.add(name_dict[i.tag_second])

        name_list=list(name_list)

        return render_template(
            "check_problem_result.html", tag_name=tag_name, dict=sum_dict,second_tag=second_tag,list=name_list,second_dict=second_sum_dict
        )


@app.route("/graph")
def graph():
    # ジャンル
    category_list = [
        "Easy",
        "Ad-Hoc",
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
        "Easy":0,
        "Ad-Hoc":0,
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
        "Ad-Hoc",
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
        "Easy":0,
        "Ad-Hoc":0,
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
        "Easy":0,
        "Ad-Hoc":0,
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
        "Easy":0,
        "Ad-Hoc":0,
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
        "Ad-Hoc",
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
        "Easy":0,
        "Ad-Hoc":0,
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
        "Easy":0,
        "Ad-Hoc":0,
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
        "Easy":0,
        "Ad-Hoc":0,
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
        "Easy":0,
        "Ad-Hoc":0,
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
        "Easy":0,
        "Ad-Hoc":0,
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
        "Ad-Hoc",
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
    probability = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,0,0]
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
                if user_dict[str(problem.problem_official_name)]=="Error":
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
                if user_dict[str(problem.problem_official_name)]=="Error":
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
    # コンテスト名取得のため、AtCoderProblemsAPIを利用する。
    get_problem = requests.get(
        "https://kenkoooo.com/atcoder/resources/merged-problems.json"
    )
    get_problem = get_problem.json()

    tagName = second_tag
    problems = db.session.query(problem_tag).filter_by(second_tag=tagName)

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
        "second_tag_search.html",first_tag=first_tag, tagName=tagName, problems=problems, dict=dict,name_dict=name_dict
    )
    return

@app.route('/tags/<first_tag>/<second_tag>/<user_id>')
def user_explain_second_tag(first_tag,second_tag,user_id):
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
    tagName = second_tag
    problems = db.session.query(problem_tag).filter_by(second_tag=tagName)

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
        "user_second_tag_search.html",
        first_tag=first_tag,
        tagName=tagName,
        problems=problems,
        dict=dict,
        user_id=user_id,
        user_dict=user_dict,
        name_dict=name_dict
    )

############################################################
#ログイン処理

@app.route('/login')
def login():
    user=User_.query.get(id=request.form['id'])
    login_user(user,True)
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/oauth/twitter')
def oauth_authorize():
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    else:
        request_token=service.get_request_token(
            params={'oauth_callback':url_for('oauth_callback',provider='twitter',_external=True)}
        )
        session['request_token'] = request_token
        
        return redirect(service.get_authorize_url(request_token[0]))

@app.route('/oauth/twitter/callback')
def oauth_callback():
    request_token = session.pop('request_token',None)
    oauth_session = service.get_auth_session(
        request_token[0],
        request_token[1],
        data={'oauth_verifier':request.args['oauth_verifier']}
    )

    profile = oauth_session.get('account/verify_credentials.json').json()
    twitter_id = str(profile.get('id'))
    username=str(profile.get('name'))
    profile_image_url = str(profile.get('profile_image_url'))



    user=db.session.query(User_).filter(User_.twitter_id==twitter_id).first()

    if user:
        user.twitter_id=twitter_id
        user.username=username
    else:
        user=User_(twitter_id=twitter_id,username=username,user_image_url=profile_image_url,vote_count=0)
        db.session.add(user)

    db.session.commit()

    login_user(user,True)
    return redirect(url_for('index'))

@login_manager.user_loader
def load_user(id):
    return User_.query.get(int(id))

################################################################

@app.route('/user_page/<user_id>')
def user_page(user_id):
    user=db.session.query(User_).filter_by(id=user_id).first()
    
    #順位計算
    rank_dict=dict({})
    all_user=db.session.query(User_).order_by(desc(User_.vote_count)).all()

    for  i in all_user:
        rank_dict[i.vote_count]=-1
        
    for i in range(0,len(all_user)):
        if rank_dict[all_user[i].vote_count]!=-1:
            continue
        else:
            rank_dict[all_user[i].vote_count]=i+1

    rank=rank_dict[user.vote_count]
    return render_template('user_page.html',user=user,rank=rank)

@app.route('/ranking/<int:page>')
def ranking(page=1):
    #ページネーション
    per_page = 100
    users=db.session.query(User_).order_by(desc(User_.vote_count)).paginate(page, per_page, error_out=False)

    #順位計算（繰り上がり処理付き）
    rank=dict({})
    user=db.session.query(User_).order_by(desc(User_.vote_count)).all()
    for  i in user:
        rank[i.vote_count]=-1
    
    print(rank)
    
    for i in range(0,len(user)):
        print(user[i].vote_count)
        if rank[user[i].vote_count]!=-1:
            continue
        else:
            rank[user[i].vote_count]=i+1
        print(rank[user[i].vote_count])
        print(' ')

    return render_template('ranking.html',users=users,page=page,per_page=per_page,rank=rank)