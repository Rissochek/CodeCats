import asyncio
import aiohttp
import aiomoex
from typing import Tuple
import pandas as pd
from flask import Flask, request
from flask_restful import Resource, Api
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
api = Api(app)

class MOEX_Parser(Resource):
    def __init__(self) -> None:
        self.start = '2025-04-19'
        self.end = '2025-04-19'
        self.companies = ["SBER", "GAZP", "LKOH", "ROSN", "VTBR", "T"]
        self.data_df = ''
    async def get_moex_data(self, company, start, end):
        async with aiohttp.ClientSession() as session:
            try:
                data = await aiomoex.get_board_candles(session, company, interval=60, start=start, end=end)
            except Exception as e:
                print("failed to get data", e)
                return None
            df = pd.DataFrame(data)
            df = df.drop(columns=["value", "high", "low", "volume"])
            df['company'] = company
            df = df[['company', 'open', 'close', 'begin', 'end']]
            return df

    async def main(self, start, end):
        tasks = [self.get_moex_data(company, start, end) for company in self.companies]
        results = await asyncio.gather(*tasks)
        return pd.concat(results, ignore_index=True)
        
    
    # def get(self) -> dict:
    #     return {"start_date":"put start_date in format YYYY-MM-DD", "end_date":"put end_date in format YYYY-MM-DD"}
    
    # def post(self) -> Tuple[dict, int]:
    #     data = request.get_json()
    #     try:
    #         user_start = data["start_date"]
    #         user_end = data["end_date"]
    #     except Exception as e:
    #         return {"error": "put int value"}, 400
    #     self.start = user_start
    #     self.end = user_end

    #     asyncio.run(self.main())
    #     self.data_df.to_json("data.json", orient='records', indent=4)
    #     return self.data_df.to_json(orient='records', indent=4), 200
parser = MOEX_Parser()
data = []
try:
    data = asyncio.run(parser.main(
        (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
        datetime.now().strftime("%Y-%m-%d")
    ))
except Exception as e:
    print("Failed to parse MOEX", e)
print(data[:10])
requests.post("http://localhost:8008/service.internal/load_prices_from_moex", json=data.to_dict(orient='records'))

# if __name__ == '__main__':
#     app.run(port=8002, debug=True)