import requests
from flask import Flask, request, jsonify
from datetime import date

app = Flask(__name__)
MOEX_API_URL = "http://localhost:8002/service.internal/moex_parser"
COMPANIES = ["SBER", "GAZP", "LKOH", "ROSN", "VTBR", "T"]

@app.route('/get_last_prices', methods=['GET'])
def get_last_prices():
    today = date.today().strftime("%Y-%m-%d")
    response = requests.post(MOEX_API_URL, json={"start_date": today, "end_date": today})

    if response.status_code != 200:
        return jsonify({"error": "Failed to get data from MOEX API"}), 500

    data = response.json()
    if isinstance(data, str):
        import json
        data = json.loads(data)

    last_prices = {}
    for company in COMPANIES:
        company_data = [entry for entry in data if entry['company'] == company]
        if company_data:
            last_entry = sorted(company_data, key=lambda x: x['end'], reverse=True)[0]
            last_prices[company] = last_entry['close']
        else:
            last_prices[company] = None

    return jsonify(last_prices)

if __name__ == '__main__':
    app.run(port=8003, debug=True)
