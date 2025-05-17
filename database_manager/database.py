from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, create_engine
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify
from flask_cors import CORS
import time
from datetime import datetime
import requests

DATABASE_NAME = 'datastore.db'
COMPANIES = ["SBER", "GAZP", "LKOH", "ROSN", "VTBR", "T"]

engine = create_engine(f'sqlite:///{DATABASE_NAME}')
Session = sessionmaker(bind=engine)
db = SQLAlchemy()


def create_service():
    database_manager = Flask(__name__)
    CORS(database_manager)
    database_manager.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DATABASE_NAME}"
    db.init_app(app=database_manager)
    return database_manager


app = create_service()


class News(db.Model):
    __tablename__ = 'News'
    id: int = Column(Integer, primary_key=True)
    link: str = Column(String)
    title: str = Column(String)
    datetime: str = Column(DateTime)
    article_text: str = Column(String)
    article_type: str = Column(String)
    source: str = Column(String)


class MOEX(db.Model):
    __tablename__ = 'MOEX'
    id: int = Column(Integer, primary_key=True)
    begin: str = Column(DateTime)
    end: str = Column(DateTime)
    open: float = Column(Float)
    close: float = Column(Float)  # Исправлено: close теперь Float
    high: float = Column(Float)   # Добавлено поле high
    low: float = Column(Float)    # Добавлено поле low
    company: str = Column(String)


parser_links_store = {"Interfax": "http://localhost:8000/service.internal/Interfax",
                      "RBC": "http://localhost:8000/service.internal/RBC"}


def send_request(parser_link):
    response = None
    try:
        response = requests.post(parser_link, json={"number_of_news": "5"})
        print(f"Response status: {response.status_code}")
    except Exception as e:
        print(f"Response error: {e}")
    return response.json() if response else None


def load_data_from_database():
    links_list = []
    records = News.query.limit(10).all()
    for record in records:
        link = record.link
        links_list.append(link)
    return links_list


def load_news_from_database(number_of_news):
    news_list = []
    records = News.query.limit(number_of_news).all()
    for record in records:
        record_dict = {
            "link": record.link,
            "title": record.title,
            "datetime": record.datetime,
            "article_text": record.article_text,
            "article_type": record.article_type,
            "source": record.source
        }
        news_list.append(record_dict)
    return news_list


links_list = []


def check_article_is_unique(article):
    if isinstance(article, dict):
        if article["link"] not in links_list:
            links_list.append(article["link"])
            return True
    return False

# with app.app_context():
#     db.create_all()
#     while True:
#         news_store = []

#         interfax_news = send_request(parser_links_store["Interfax"])
#         rbc_news = send_request(parser_links_store["RBC"])

#         # interfax_news = [{
#         #                 "link": "some link",
#         #                 'title': "some title",
#         #                 'datetime': "2025-04-18T17:50",
#         #                 'article_text': "some text",
#         #                 'type': "some type",
#         #                 'source': "some source"}, "",]
    # rbc_news = [{
    #                 "link": "4",
    #                 'title': "some title",
    #                 'datetime': "2025-04-18T17:50",
    #                 'article_text': "some text",
    #                 'type': "some type",
    #                 'source': "some source"}, "",
    #                 {
    #                 "link": "5",
    #                 'title': "some title",
    #                 'datetime': "2025-04-18T17:50",
    #                 'article_text': "some text",
    #                 'type': "some type",
    #                 'source': "some source"}
#         #                 ]

#         news_store.extend([i for i in interfax_news] if interfax_news else "")
#         news_store.extend([i for i in rbc_news] if rbc_news else "")


#         links_list = load_data_from_database()
#         for i in news_store:
#             if check_article_is_unique(i):
#                 new_article = News(
#                     link=i["link"],
#                     title=i["title"],
#                     datetime=datetime.strptime(i["datetime"], "%Y-%m-%dT%H:%M:%S%z"),
#                     article_text=i["article_text"],
#                     article_type=i["type"],
#                     source=i["source"]
#                 )
#                 db.session.add(new_article)
#                 db.session.commit()
#         time.sleep(60*5)
with app.app_context():
    db.create_all()


@app.route('/service.internal/get_num_of_news', methods=['POST'])
def get_num_of_news():
    num_of_news_requested = request.json.get('number_of_news')
    links = load_data_from_database()
    return jsonify(links)


@app.route("/service.internal/actual_news_gainer", methods=["POST"])
def actual_news_gainer():
    actual_news = request.json
    print(actual_news)
    if actual_news != []:
        for i in actual_news:
            new_article = News(
                link=i["link"],
                title=i["title"],
                datetime=datetime.strptime(
                    i["datetime"], "%Y-%m-%dT%H:%M:%S%z"),
                article_text=i["article_text"],
                article_type=i["type"],
                source=i["source"]
            )
            db.session.add(new_article)
            db.session.commit()
    return "200"


@app.route("/service.internal/get_last_n_news", methods=["POST"])
def get_last_n_news():
    num_of_news_requested = request.json.get('number_of_news')
    news = load_news_from_database(num_of_news_requested)
    return jsonify(news)

# @app.route("/service.internal/get_last_n_company_news", methods=["POST"])
# def get_last_n_company_news():
#     num_of_news_requested = request.json.get('number_of_news')
#     company_requested = request.json.get('company')


# !!!
# This section is about moex logic


@app.route("/service.internal/load_prices_from_moex", methods=['POST'])
def load_prices_from_moex():
    moex_list = request.json
    for i in moex_list:
        current = MOEX(
            begin=datetime.strptime(
                f"{i['begin']}+03:00", "%Y-%m-%d %H:%M:%S%z"),
            end=datetime.strptime(f"{i['end']}+03:00", "%Y-%m-%d %H:%M:%S%z"),
            open=i["open"],
            close=i["close"],
            high=i["high"],  # Добавлено
            low=i["low"],    # Добавлено
            company=i["company"]
        )
        if db.session.query(MOEX).filter_by(
            begin=current.begin, end=current.end,
            open=current.open, close=current.close,
            high=current.high, low=current.low,
            company=current.company
        ).first() is None:
            db.session.add(current)
    db.session.commit()
    return "200"


@app.route("/service.internal/get_moex_from_database", methods=["POST"])
def get_moex_from_database():
    company = request.json.get('company')
    number_of_prices = request.json.get('number_of_prices')
    prices = db.session.query(MOEX).filter_by(
        company=company).limit(number_of_prices).all()
    return jsonify([{
        "begin": i.begin,
        "end": i.end,
        "open": i.open,
        "close": i.close,
        "high": i.high,  # Добавлено
        "low": i.low,    # Добавлено
        "company": i.company
    } for i in prices])


if __name__ == '__main__':
    app.run(port=8008, debug=False)
