import requests
import random
from flask import Flask, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)
MOEX_API_URL = "http://localhost:8002/service.internal/moex_parser"
COMPANIES = ["SBER", "GAZP", "LKOH", "ROSN", "VTBR", "T"]


@app.route('/predict_prices', methods=['GET'])
def predict_prices():
    today = datetime.today().strftime("%Y-%m-%d")
    response = requests.post(MOEX_API_URL, json={"start_date": today, "end_date": today})

    if response.status_code != 200:
        return jsonify({"error": "Failed to get data from MOEX API"}), 500

    predictions = {}
    for company in COMPANIES:
        future_prices = []
        current_time = datetime.now()
        for i in range(10):
            future_time = current_time + timedelta(days=(i + 1))
            price = round(random.uniform(500, 1000), 2)
            future_prices.append([future_time.strftime("%Y-%m-%d"), price])
        predictions[company] = future_prices

    return jsonify(predictions)


if __name__ == '__main__':
    app.run(port=8007, debug=True)
