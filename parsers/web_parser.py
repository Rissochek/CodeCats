from flask import Flask, request
from flask_restful import Resource, Api
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from typing import Tuple
import requests
import re
from datetime import datetime
from random import uniform
import pymorphy3
import time

app = Flask(__name__)
api = Api(app)

banking_keywords = [
    "банк", "финанс", "кредит", "инвестиция", "актив", "курс",
    "процент", "ставка", "дебет", "кредитование", "капитал",
    "акция", "вклад", "прибыль", "убыток"
]

# ключевые слова Энергетики
oil_gas_keywords = [
    "нефть", "газ", "добыча", "бурение", "транспортировка",
    "переработка", "качество", "нефтепровод", "газопровод",
    "объём", "инфраструктура", "технология", "энергия",
    "рынок", "цена"
]

morph = pymorphy3.MorphAnalyzer()

def determine_sphere(article_text):

    banking_count = 0
    oil_gas_count = 0

    # разделение текста на слова
    words = re.findall(r'\w+', article_text.lower())

    for word in words:
        lemma = morph.parse(word)[0].normal_form

        if lemma in banking_keywords:
            banking_count += 1
        elif lemma in oil_gas_keywords:
            oil_gas_count += 1

    # определение сферы
    if banking_count > oil_gas_count:
        return "Финансы"
    elif oil_gas_count > banking_count:
        return "Энергетика"
    elif oil_gas_count == banking_count and oil_gas_count > 0:
        return "Финансы/Энергетика"
    else:
        return None  # если ключевые слова не найдены, возвращаем None

class WebParser(ABC):
    def __init__(self) -> None:
        self.url = ''
        self.driver = ''
        self.parser_type = 'html.parser'
        self.links_class_name = ''
        self.title_class_name = ''
        self.overview_class_name = ''
        self.article_class_name = ''
        self.datetime_class_name = ''
        self.article_scrape = ''
        self.article_body_scrape = ''
        self.source = ''
        self.data_store = []

    def start_driver(self) -> None:
        options = Options()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    @abstractmethod
    def scrape_links(self, user_duration) -> list:
        pass

    @abstractmethod
    def scrape_title(self) -> str:
        pass

    @abstractmethod
    def scrape_overview(self) -> str:
        pass
    
    @abstractmethod
    def scrape_article_body(self, link) -> None:
        pass

    @abstractmethod
    def scrape_article_text(self) -> str:
        pass

    @abstractmethod
    def scrape_datetime(self) -> str:
        pass

    @abstractmethod
    def get_full_data(self, user_duration) -> list:
        pass

    @abstractmethod
    def get(self) -> dict:
        pass

    @abstractmethod
    def post(self) -> Tuple[dict, int]:
        pass

class RBCParser(Resource, WebParser):
    def __init__(self) -> None:
        super().__init__()
        self.url = 'https://www.rbc.ru/economics/'
        self.links_class_name = 'item__link rm-cm-item-link js-rm-central-column-item-link'
        self.title_class_name = 'article__header__title-in js-slide-title'
        self.overview_class_name = 'article__text__overview'
        self.article_class_name = 'article__text article__text_free'
        self.datetime_class_name = 'article__header__date'
        self.source = 'РБК'
                
    def scrape_links(self, user_num) -> list:
        super().start_driver()
        self.driver.get(self.url)
        link_elements = []

        while len(link_elements) < user_num:
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                scrape = BeautifulSoup(self.driver.page_source, self.parser_type)
                link_elements = [i['href'] for i in scrape.find_all('a', class_=self.links_class_name)]
            except Exception as e:
                print("Failed scrape links:", e)
        self.driver.quit()
        return link_elements[:user_num]

    def scrape_title(self) -> str:
        title = self.article_scrape.find('h1', class_=self.title_class_name).get_text(separator=" ", strip=True).replace("\xa0", " ")
        return title
    
    def scrape_overview(self) -> str:
        overview = self.article_body_scrape.find('div', class_=self.overview_class_name)
        if overview != None:
            overview = overview.get_text(separator=" ", strip=True).replace("\xa0", " ")
        else:
            overview = ''
        return overview
    
    def scrape_article_body(self, link) -> None:
        time.sleep(uniform(0, 2))
        try:
            response = requests.get(link)
        except Exception as e:
            self.article_body_scrape = ""
            print("Failed scrape article body", e)
            return

        self.article_scrape = BeautifulSoup(response.text, self.parser_type)
        self.article_body_scrape = self.article_scrape.find("div", self.article_class_name)

    def scrape_article_text(self) -> str:
        if self.article_body_scrape != "":
            article_text = ' '.join([i.get_text(separator=" ", strip=True).replace("\xa0", " ") for i in self.article_body_scrape.find_all('p')])
        else:
            article_text = "None"
        return article_text

    def scrape_datetime(self) -> str:
        date_element = self.article_scrape.find('time', class_=self.datetime_class_name)
        if date_element and 'datetime' in date_element.attrs:
            datetime_value = date_element['datetime']
        else:
            datetime_value = '-'
        return datetime_value
    
    def get_full_data(self, user_num) -> list: #call this func only
        links = self.scrape_links(user_num)
        count = 0
        for link in links:
            print(f'link {count} was readed')
            count += 1
            self.scrape_article_body(link=link)
            article_text = f'{self.scrape_overview()} {self.scrape_article_text()}'
            article_type = determine_sphere(article_text)
            if self.scrape_article_text != 'None' and article_type is not None:
                self.data_store.append({
                    'link': link,
                    'title': self.scrape_title(),
                    'datetime': self.scrape_datetime(),
                    'article_text': article_text,
                    'type': article_type,
                    'source': self.source
                })
        return self.data_store
    
    def get_new_data(self, links):
        count = 1
        data_store = []
        for link in links:
            print(f'link {count} was readed')
            count += 1
            self.scrape_article_body(link=link)
            article_text = f'{self.scrape_overview()} {self.scrape_article_text()}'
            article_type = determine_sphere(article_text)
            if self.scrape_article_text != 'None' and article_type is not None:
                data_store.append({
                    "link": link,
                    'title': self.scrape_title(),
                    'datetime': f"{self.scrape_datetime()}",
                    'article_text': article_text,
                    'type': article_type,
                    'source': self.source
                })
        return data_store
    
    def get(self) -> dict:
        msg = {"number_of_news": "In post request enter num of news u need"}
        return msg
    
    def post(self) -> Tuple[dict, int]:
        data = request.get_json()
        try:
            num_of_news = int(data["number_of_news"])
        except Exception as e:
            return {"error": "put int or float value"}, 400
        
        news = self.get_full_data(num_of_news)
        news = [i for i in news if i != ""]
        print(len(news))
        return news, 200
        
        

class InterfaxParser(Resource, WebParser):

    def __init__(self) -> None:
        super().__init__()
        super().start_driver()
        self.url = "https://www.interfax.ru/business/"
        self.base_url = "https://www.interfax.ru"
        self.links_class_name = 'timeline'
        self.title_class_name = "headline" #this is .find(itemprop="headline") parameter
        self.overview_class_name = "in" #plus itemprop="description"
        self.article_class_name = "articleBody" #this is .find(itemprop="articleBody") parameter
        self.source = "Интерфакс"
        self.links = []
    
    def scrape_links(self, num_of_news_requested) -> list:
        self.driver.get(self.url)
        link_elements = []
        while len(link_elements) < num_of_news_requested:
            try:
                WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.timeline a')))
                link_elements = self.driver.find_elements(By.CSS_SELECTOR, '.timeline a')
                self.driver.execute_script("getMoreTimeline()")
            except Exception as e:
                print("Failed to load source page:", e)
        self.links = [element.get_attribute('href') for element in link_elements][:num_of_news_requested]
        self.driver.quit()
        print(self.links)
    
    def scrape_title(self) -> str:
        try:
            title = self.article_scrape.find("h1", itemprop=self.title_class_name)
        except Exception as e:
            print("no title", e)
            return "No Title"
        
        return title.get_text(separator=" ", strip=True).replace("\xa0", " ")

    def scrape_overview(self) -> str:
        return ''

    def scrape_article_body(self, link) -> None:
        time.sleep(uniform(0, 2))
        try: 
            response = requests.get(link)
        except Exception as e:
            print("failed get article body", e)
            self.article_body_scrape = None
            return
        
        response.encoding = 'windows-1251'
        self.article_scrape = BeautifulSoup(response.text, self.parser_type)
        self.article_body_scrape = self.article_scrape.find("article", itemprop=self.article_class_name)
    
    def scrape_article_text(self) -> str:
        if (self.article_body_scrape != None):
            article_text = ' '.join([i.get_text(separator=" ", strip=True).replace("\xa0", " ") for i in self.article_body_scrape.find_all('p')])
        else:
            article_text = 'None'
        return article_text

    def scrape_datetime(self) -> str:
        try:
            date_element = self.article_scrape.find('time')
        except Exception as e:
            print("error data", e)
            datetime_value = '-'
            return
        if date_element and 'datetime' in date_element.attrs:
            datetime_value = date_element['datetime']
        else:
            datetime_value = '-'
        return datetime_value

    def get_full_data(self, user_num) -> list: #call this func only
        count = 1
        self.scrape_links(user_num)
        for link in self.links:
            print(f'link {count} was readed')
            count += 1
            self.scrape_article_body(link=link)
            article_text = f'{self.scrape_overview()} {self.scrape_article_text()}'
            article_type = determine_sphere(article_text)
            if self.scrape_article_text != 'None' and article_type is not None:
                self.data_store.append({
                    "link": link,
                    'title': self.scrape_title(),
                    'datetime': f"{self.scrape_datetime()}:00+03:00",
                    'article_text': article_text,
                    'type': article_type,
                    'source': self.source
                })
        return self.data_store
    
    def get_new_data(self, links):
        count = 1
        data_store = []
        for link in links:
            print(f'link {count} was readed')
            count += 1
            self.scrape_article_body(link=link)
            article_text = f'{self.scrape_overview()} {self.scrape_article_text()}'
            article_type = determine_sphere(article_text)
            if self.scrape_article_text != 'None' and article_type is not None:
                data_store.append({
                    "link": link,
                    'title': self.scrape_title(),
                    'datetime': f"{self.scrape_datetime()}:00+03:00",
                    'article_text': article_text,
                    'type': article_type,
                    'source': self.source
                })
        return data_store
    
    def get(self) -> dict:
        msg = {"number_of_news": "In post request enter num of news u need"}
        return msg
    
    def post(self) -> Tuple[dict, int]:
        data = request.get_json()
        try:
            num_of_news = int(data["number_of_news"])
        except Exception as e:
            return {"error": "put int or float value"}, 400
        
        news = self.get_full_data(num_of_news)
        news = [i for i in news if i != ""]
        print(len(news))
        return news, 200

interfax_parser = InterfaxParser()
rbc_parser = RBCParser()
while True:
    response = requests.post("http://localhost:8008/service.internal/get_num_of_news", json={"number_of_news": "10"})
    if response.status_code == 200:
        data = response.json()
        print(data)
        interfax_parser.scrape_links(5)
        interfax_links = interfax_parser.links
        rbc_links = rbc_parser.scrape_links(5)
        rbc_new_links = [i for i in rbc_links if i not in data]
        interfax_new_links = [i for i in interfax_links if i not in data]
        print(rbc_new_links)
        print(interfax_new_links)
        actual_news = []
        # actual_news = [    [{
        #                     "link": "some link",
        #                     'title': "some title",
        #                     'datetime': "2025-04-18T17:50",
        #                     'article_text': "some text",
        #                     'type': "some type",
        #                     'source': "some source"}, "",{
        #                     "link": "4",
        #                     'title': "some title",
        #                     'datetime': "2025-04-18T17:50",
        #                     'article_text': "some text",
        #                     'type': "some type",
        #                     'source': "some source"}, "",
        #                     {
        #                     "link": "5",
        #                     'title': "some title",
        #                     'datetime': "2025-04-18T17:50",
        #                     'article_text': "some text",
        #                     'type': "some type",
        #                     'source': "some source"}]]
        if rbc_new_links != []:
            actual_news.extend(rbc_parser.get_new_data(rbc_new_links))
        if interfax_new_links != []:
            actual_news.extend(interfax_parser.get_new_data(interfax_new_links))
        print(actual_news)
        requests.post("http://localhost:8008/service.internal/actual_news_gainer", json=actual_news)
    time.sleep(60*5)


# api.add_resource(InterfaxParser, '/service.internal/Interfax')
# api.add_resource(RBCParser, '/service.internal/RBC')

# if __name__ == '__main__':
#     app.run(port=8000, debug=True)