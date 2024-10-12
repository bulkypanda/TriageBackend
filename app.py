import requests
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


@app.route('/api/<string:disasterName>', methods=['GET'])
def get_news(disasterName):
    # params = {
    #     'access_key': flightkey,
    #     'flight_iata': flightnum,
    #     'limit': 1
    # }
    # api_result = requests.get('http://api.aviationstack.com/v1/flights?access_key=' + flightnum, params)
    # api_response = api_result.json()
    # print(api_response)
    # print(api_response['data'])

    # gate = api_response['data'][0]['departure']['gate']
    # time = api_response['data'][0]['departure']['scheduled']
    # print(gate)

    all_articles = api.get_everything(q='disasterName',
                                      sources='bbc-news,the-verge',
                                      domains='bbc.co.uk,techcrunch.com',
                                      from_param='2017-12-01',
                                      to='2017-12-12',
                                      language='en',
                                      sort_by='relevancy',
                                      page=2)


    toReturn = jsonify({"gate": gate, 'time': time})
    toReturn.headers.add('Access-Control-Allow-Origin', '*')
    return toReturn

if (__name__ == "__main__"):
    # parser = argparse.ArgumentParser()
    # -flightnum
    # parser.add_argument("-flight", "--flightnum", help="Flight Number", required=True)
    # args = parser.parse_args()

    app.run(debug=True)
