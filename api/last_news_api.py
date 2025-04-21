import requests
from flask import Flask, request, jsonify
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
WEB_PARSER_URL = "http://localhost:8008//service.internal/get_last_n_news"


@app.route('/get_last_news', methods=['POST'])
def get_last_news():
    number_of_news = int(request.get_json().get('number_of_news'))
    try:
        response = requests.post(WEB_PARSER_URL, json={
                                 "number_of_news": number_of_news})

        if response.status_code != 200:
            return jsonify({"error": "Failed to get data from web_parser"}), 500

        news = response.json()
        last_news = sorted(news, key=lambda x: x['datetime'], reverse=True)[
            :number_of_news]

        return jsonify(last_news)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=8004, debug=True)
