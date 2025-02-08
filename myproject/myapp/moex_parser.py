import requests
from datetime import datetime, timedelta
from .models import Exchanges

# Коды компаний
COMPANIES = {
    "SBER": "Сбербанк",
    "VTBR": "ВТБ",
    "ALFB": "Альфа-Банк",
    "GAZP": "Газпром",
    "LKOH": "Лукойл",
    "ROSN": "Роснефть",
}

def fetch_historical_data(ticker, start_date, end_date):
    """
    Получает исторические данные для указанного тикера.
    """
    url = f"https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
    params = {
        "from": start_date,
        "till": end_date,
        "interval": 1,  # 1 час
        "iss.meta": "off",
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Парсим данные
        history = data["history"]["data"]
        for entry in history:
            timestamp = datetime.strptime(entry[1], "%Y-%m-%d")  # Время
            price = entry[11]  # Цена закрытия

            # Сохраняем данные в базу
            Exchanges.objects.create(
                company_name=COMPANIES[ticker],
                price=price,
                datetime=timestamp
            )

        print(f"Данные для {ticker} успешно загружены.")
    except Exception as e:
        print(f"Ошибка при загрузке данных для {ticker}: {e}")

def fetch_all_companies_data():
    """
    Загружает данные для всех компаний.
    """
    start_date = "2025-01-01"  # Начальная дата
    end_date = datetime.now().strftime("%Y-%m-%d")  # Текущая дата

    for ticker in COMPANIES:
        fetch_historical_data(ticker, start_date, end_date)