from config import *
import numpy
import os
import json
import time
import requests
import csv
import app
from urllib.request import urlopen
from bs4 import BeautifulSoup
import ssl
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

ssl._create_default_https_context = ssl._create_unverified_context


name_dict = {
    "Brute-Force": "全探索",
    "Binary-Search": "二分探索",
    "Ternary-Search": "三分探索",
    "DFS": "深さ優先探索",
    "BFS": "幅優先探索",
    "Bit-Brute-Force": "bit全探索",
    "Heuristic": "ヒューリスティック",
    "Other": "その他",
    "String-Operation": "文字列処理",
    "Rolling-Hash": "ローリングハッシュ",
    "Manacher": "Manacher",
    "Suffix-Array": "Suffix-Array",
    "Z-Algorithm": "Z-Algorithm",
    "Trie": "Trie",
    "Cumulative-Sum": "累積和",
    "imos": "imos法",
    "Two-Pointers": "尺取り法",
    "Split-And-List": "半分全列挙",
    "Square-Division": "平方分割",
    "Divide-And-Conquer": "分割統治法",
    "Doubling": "ダブリング",
    "Shortest-Path": "最短経路",
    "Minimum-Spanning-Tree": "最小全域木",
    "LCA": "最小共通祖先",
    "Strongly-Connected-Components": "強連結成分分解",
    "Topological-Sort": "トポロジカルソート",
    "Euler-Tour": "オイラーツアー",
    "HL-Decomposition": "HL分解",
    "Centroid-Decomposition": "重心分解",
    "Check-Tree": "木の同型判定",
    "Two-Edge-Connected-Components": "二重辺連結成分分解",
    "Bi-Connected-Components": "二重頂点連結成分分解",
    "Cycle-Basis": "サイクル基底",
    "dfs-tree": "dfs木",
    "Erdesh": "エルデシュガライの定理",
    "Simple-DP": "基礎DP",
    "String-DP": "文字列DP",
    "Section-DP": "区間DP",
    "Digit-DP": "桁DP",
    "Tree-DP": "木DP",
    "Every-Direction-DP": "全方位木DP",
    "Bit-DP": "bitDP",
    "Probability-DP": "確率DP",
    "Expected-Value-DP": "期待値DP",
    "Insert-DP": "挿入DP",
    "Link-DP": "連結DP",
    "Inline-DP": "インラインDP",
    "Matrix-Power": "行列累乗",
    "CHT": "Convex-Hull-Trick",
    "Monge-DP": "Monge-DP",
    "Alien-DP": "Alien-DP",
    "Kitamasa": "きたまさ法",
    "stack": "stack",
    "queue": "queue",
    "set": "set",
    "map": "map",
    "deque": "deque",
    "multiset": "multiset",
    "priority_queue": "priority_queue",
    "Union-Find-Tree": "Union-Find-Tree",
    "BIT": "Binary-Indexed-Tree",
    "Segment-Tree": "Segment-Tree",
    "Lazy-Segment-Tree": "Lazy-Segment-Tree",
    "Sparse-Table": "Sparse-Table",
    "WaveletMatrix": "WaveletMatrix",
    "Persistent-Data-Structures": "永続データ構造",
    "Balanced-Tree": "平衡二分探索木",
    "Nim": "Nim",
    "Grundy": "Grundy数",
    "Backtrack": "後退解析",
    "Mini-Max": "ミニマックス法",
    "unique": "特殊な性質",
    "Max-Flow": "最大流問題",
    "Min-Cost-Flow": "最小費用流問題",
    "Bipartite-Matching": "二部マッチング",
    "Min-Cut": "最小カット",
    "Burn": "燃やす埋める",
    "Convex-Hull": "凸包",
    "Declination-Sorting": "偏角ソート",
    "Three-D": "三次元",
    "Number": "整数",
    "Combinatorics": "組み合わせ",
    "Probability": "確率",
    "Expected-Value": "期待値",
    "Matrix": "行列",
    "Parsing": "構文解析",
    "Easy": "Easy",
    "Ad-Hoc": "Ad-Hoc",
    "Greedy-Methods": "Greedy-Methods",
    "Construct": "Construct",
    None: "None",
    "null": "None",
    "Enumerate": "数え上げ",
}


class problem_tag(db.Model):
    __tablename__ = "problem_tag"
    __table_args__ = {"extend_existing": True}


@scheduler.scheduled_job("interval", hour=1)
def calc_news():
    with open("news_data.json", "w") as f:
        try:
            html = urlopen("https://atcoder.jp/home")
            bsObj = BeautifulSoup(html, "html.parser")

            # テーブルを指定
            recent_table = bsObj.find(id="contest-table-recent")

            problem_list = []
            problem_name_list = []
            url_list = []

            if recent_table != None:
                table = recent_table.findAll("td")

                for i in range(0, len(table)):
                    # time and date は飛ばす
                    if i % 2 == 0:
                        continue

                    add_url = table[i].find("a").attrs["href"]
                    problem_name_list.append(table[i].find("a").text)
                    url_list.append(str("https://atcoder.jp" + add_url))

                    # problem_idを抜き出す
                    html2 = urlopen(str("https://atcoder.jp" + add_url + "/tasks"))
                    bsObj2 = BeautifulSoup(html2, "html.parser")
                    table2 = bsObj2.findAll("tr")

                    temp_list = []
                    for row in table2:
                        if len(row.findAll("a")) > 0:
                            temp_list.append(
                                row.findAll("a")[0].attrs["href"].split("/")[-1]
                            )

                    problem_list.append(temp_list)

            tag_list = []
            for problems in problem_list:
                temp_list = []
                for problem_id in problems:
                    tag = (
                        db.session.query(problem_tag)
                        .filter_by(problem_official_name=problem_id)
                        .first()
                    )
                    if tag == None:
                        temp_list.append("None")
                        continue

                    if tag.second_tag != None:
                        if tag.second_tag == "Other":
                            temp_list.append(
                                tag.first_tag + ":" + name_dict[tag.second_tag]
                            )
                        else:
                            temp_list.append(name_dict[tag.second_tag])
                    else:
                        temp_list.append(tag.first_tag)

                tag_list.append(temp_list)

            news = {
                "tag_list": tag_list,
                "problem_name_list": problem_name_list,
                "url_list": url_list,
            }

            json.dump(news, f)
        except Exception as e:
            print(e)

    with open("news_data.json", "r") as f:
        news = json.load(f)
        print(news)


scheduler.start()
