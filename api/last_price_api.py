import requests
from flask import Flask, request, jsonify
from datetime import date

app = Flask(__name__)
MOEX_API_URL = "http://localhost:8008/service.internal/get_moex_from_database"
# COMPANIES = ["SBER", "GAZP", "LKOH", "ROSN", "VTBR", "T"]

@app.route('/get_last_prices', methods=['POST'])
def get_last_prices():

    company = request.json.get("company")
    number_of_prices = request.json.get('number_of_prices')

    response = requests.post(MOEX_API_URL, json={"number_of_prices": number_of_prices, "company": company})

    if response.status_code != 200:
        return jsonify({"error": "Failed to get data from MOEX API"}), 500

    data = response.json()
    return jsonify(data)

if __name__ == '__main__':
    app.run(port=8003, debug=True)
