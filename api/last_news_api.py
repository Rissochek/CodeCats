import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
WEB_PARSER_URL = "http://localhost:8000/service.internal/Interfax"  # Можно добавить Interfax
N = 5  # количество последних новостей


@app.route('/get_last_news', methods=['GET'])
def get_last_news():
    try:
        response = requests.post(WEB_PARSER_URL, json={"duration": 2})  # Запрашиваем новости за 2 секунды

        if response.status_code != 200:
            return jsonify({"error": "Failed to get data from web_parser"}), 500

        news = response.json()
        last_news = sorted(news, key=lambda x: x['datetime'], reverse=True)[:N]

        return jsonify(last_news)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=8004, debug=True)
