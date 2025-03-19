import requests
import pymorphy3
from flask import Flask, request, jsonify

app = Flask(__name__)
WEB_PARSER_URL = "http://localhost:8000/service.internal/RBC"

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

@app.route('/service.internal/get_company_news', methods=['POST'])
def get_company_news():
    try:
        data = request.get_json()
        companies = data.get("companies", [])
        limit = data.get("limit", 5)

        response = requests.post(WEB_PARSER_URL, json={"duration": 5})

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch news"}), 500

        all_news = response.json()

        company_news = []
        for news in all_news:
            text_words = normalize_text(news["title"] + " " + news["article_text"])
            for company in companies:
                if text_words & NORMALIZED_COMPANY_KEYWORDS.get(company, set()):
                    company_news.append(news)
                    break

        company_news = company_news[:limit]

        return jsonify(company_news)

    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(port=8006, debug=True)
