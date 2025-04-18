from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, create_engine
from flask_sqlalchemy import SQLAlchemy
from flask import Flask 
import time
from datetime import datetime
import requests

DATABASE_NAME = 'datastore.db'
engine = create_engine(f'sqlite:///{DATABASE_NAME}')
Session = sessionmaker(bind=engine)
db = SQLAlchemy()

def create_service():
    database_manager = Flask(__name__)
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

links_list = []

def check_article_is_unique(article):

    if isinstance(article, dict):
        if article["link"] not in links_list:
            links_list.append(article["link"])
            return True
        
    return False 

with app.app_context():
    db.create_all()
    while True:
        news_store = []

        interfax_news = send_request(parser_links_store["Interfax"])
        rbc_news = send_request(parser_links_store["RBC"])

        # interfax_news = [{
        #                 "link": "some link",
        #                 'title': "some title",
        #                 'datetime': "2025-04-18T17:50",
        #                 'article_text': "some text",
        #                 'type': "some type",
        #                 'source': "some source"}, "",]
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
        #                 ]

        news_store.extend([i for i in interfax_news] if interfax_news else "")
        news_store.extend([i for i in rbc_news] if rbc_news else "")
        
        links_list = load_data_from_database()
        for i in news_store:
            if check_article_is_unique(i):
                new_article = News(
                    link=i["link"],
                    title=i["title"],
                    datetime=datetime.strptime(i["datetime"], "%Y-%m-%dT%H:%M:%S%z"),
                    article_text=i["article_text"],
                    article_type=i["type"],
                    source=i["source"]
                )   
                db.session.add(new_article)
                db.session.commit()
        time.sleep(60*5)
    