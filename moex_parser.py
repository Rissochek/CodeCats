import asyncio
import aiohttp
import aiomoex
from typing import Tuple
import pandas as pd
from flask import Flask, request
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)


class MOEX_Parser(Resource):
    def __init__(self) -> None:
        self.start = '2025-01-01'
        self.end = '2025-01-02'
        self.companies = ["SBER", "GAZP", "LKOH", "ROSN", "VTBR", "T"]
        self.data_df = ''

    async def get_moex_data(self, company):
        async with aiohttp.ClientSession() as session:
            try:
                data = await aiomoex.get_board_candles(session, company, interval=60, start=self.start, end=self.end)
            except Exception as e:
                print(f"Failed to get data for {company}: {e}")
                return pd.DataFrame()  # Возвращаем пустой DataFrame

            if not data:  # Проверяем, есть ли данные
                print(f"No data received for {company}")
                return pd.DataFrame()  # Возвращаем пустой DataFrame

            df = pd.DataFrame(data)

            # Проверяем, есть ли нужные столбцы перед удалением
            drop_columns = ["value", "high", "low", "volume"]
            existing_columns = [col for col in drop_columns if col in df.columns]
            df = df.drop(columns=existing_columns, errors='ignore')

            df['company'] = company
            df = df[['company', 'open', 'close', 'begin', 'end']] if not df.empty else pd.DataFrame()

            return df

    async def main(self):
        tasks = [self.get_moex_data(company) for company in self.companies]
        results = await asyncio.gather(*tasks)
        self.data_df = pd.concat(results, ignore_index=True)

    def get(self) -> dict:
        return {"start_date": "put start_date in format YYYY-MM-DD", "end_date": "put end_date in format YYYY-MM-DD"}

    def post(self) -> Tuple[dict, int]:
        data = request.get_json()
        try:
            user_start = data["start_date"]
            user_end = data["end_date"]
        except Exception as e:
            return {"error": "put int value"}, 400
        self.start = user_start
        self.end = user_end

        asyncio.run(self.main())
        self.data_df.to_json("data.json", orient='records', indent=4)
        return self.data_df.to_json(orient='records', indent=4), 200


api.add_resource(MOEX_Parser, '/service.internal/moex_parser')

if __name__ == '__main__':
    app.run(port=8002, debug=True)