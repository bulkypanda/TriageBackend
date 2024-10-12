import requests
import datetime
from flask import Flask, jsonify
from newsapi import NewsApiClient
import os

app = Flask(__name__)

api = NewsApiClient(api_key="e194b22299a64a58bf96756191249647")

@app.route('/', methods=['GET'])
def get_home():
    toReturn = jsonify({"text": "Welcome to the Triage backend server! API requests may be requested from this URL."})
    toReturn.headers.add('Access-Control-Allow-Origin', '*')
    return toReturn


def lastweek(string=True):
    day = datetime.date.today() - datetime.timedelta(7)
    return day

@app.route('/news/<string:disasterName>', methods=['GET'])
def get_news(disasterName):
    lweek = lastweek(True)
    articles = api.get_everything(q=disasterName, from_param=lweek)

    toReturn = jsonify(articles)
    toReturn.headers.add('Access-Control-Allow-Origin', '*')
    return toReturn

@app.route('/question/<string:disasterName>', methods=['GET'])
def get_answer(disasterName):
    lweek = lastweek(True)
    articles = api.get_everything(q=disasterName, from_param=lweek, sort_by="relevancy", page_size=5, page=1)



    toReturn = jsonify(articles)
    toReturn.headers.add('Access-Control-Allow-Origin', '*')
    return toReturn

if (__name__ == "__main__"):
    # parser = argparse.ArgumentParser()
    # -flightnum
    # parser.add_argument("-flight", "--flightnum", help="Flight Number", required=True)
    # args = parser.parse_args()

    app.run(host="0.0.0.0", port="6969", debug=True)
