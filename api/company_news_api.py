import requests
import pymorphy3
from flask import Flask, request, jsonify

app = Flask(__name__)
WEB_PARSER_URL = "http://localhost:8008/service.internal/get_last_n_news"

# ключевые слова для компаний
COMPANY_KEYWORDS = {
    "SBER": ["Сбербанк", "Сбербанк Онлайн", "СберМаркет", "Сберидентификация", "СберМобайл", "СберКредит", "Сбер", "СберМегаМаркет"],
    "GAZP": ["Газпром", "Газпромнефть", "Газпромбанк", "Ямал-Европа", "Северный поток", "Газпром экспорт", "Суджа"],
    "LKOH": ["Лукойл", "ЛУКОЙЛ-Энергосети", "Лукойл-Нижегороднефть", "Каспийский проект", "Запасы", "Лукойл-Инжиниринг"],
    "ROSN": ["Роснефть", "Ванкорнефть", "Роснефть-Нефтегаз", "ТЭК Роснефть", "Сахалин-1", "Роснефть-Геология"],
    "VTBR": ["ВТБ", "ВТБ Онлайн", "ВТБ24", "ВТБ Капитал", "ВТБ Лизинг", "ВТБ Страхование"],
    "T": ["Тинькофф", "Тинькофф Банк", "Тинькофф Инвестиции", "Тинькофф Платежи", "Тинькофф Кредитные карты", "Тинькофф Страхование", "Т-банк", "Т Инвестиции"]
}

morph = pymorphy3.MorphAnalyzer()

def normalize_text(text):
    words = text.split()
    return {morph.parse(word)[0].normal_form for word in words}

def normalize_keywords():
    normalized = {}
    for company, keywords in COMPANY_KEYWORDS.items():
        normalized[company] = {morph.parse(word)[0].normal_form for word in keywords}
    return normalized

NORMALIZED_COMPANY_KEYWORDS = normalize_keywords()

@app.route('/get_company_news', methods=['POST'])
def get_company_news():
    data = request.get_json()
    number_of_news = int(data.get("number_of_news"))
    company_news = []
    count = 0

    while(len(company_news) < number_of_news):
        try:
            company = data.get("company", [])
            response = requests.post(WEB_PARSER_URL, json={"number_of_news": 50})
            
            if response.status_code != 200:
                return jsonify({"error": "Failed to fetch news"}), 500
            
            if count > 5:
                return 200
            all_news = response.json()
            for article in all_news:
                text_words = normalize_text(article["title"] + " " + article["article_text"])
                if text_words & NORMALIZED_COMPANY_KEYWORDS.get(company, set()):
                    company_news.append(article)
            count += 1

        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
        
    company_news = company_news[:number_of_news]
    return jsonify(company_news)

if __name__ == '__main__':
    app.run(port=8006, debug=False)
