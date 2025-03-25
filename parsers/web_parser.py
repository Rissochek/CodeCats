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
                
    def scrape_links(self, user_duration) -> list:
        super().start_driver()
        self.driver.get(self.url)
        time.sleep(2)

        start_time = time.time()
        duration = user_duration

        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if time.time() - start_time > duration:
                break
            
            if new_height == last_height:
                break
            last_height = new_height

        scrape = BeautifulSoup(self.driver.page_source, self.parser_type)
        return [i['href'] for i in scrape.find_all('a', class_=self.links_class_name)]
    
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
        response = requests.get(link)
        if response.status_code != 200:
            print("Error: wrong status code", response.status_code)
            exit()

        self.article_scrape = BeautifulSoup(response.text, self.parser_type)
        self.article_body_scrape = self.article_scrape.find("div", self.article_class_name)

    def scrape_article_text(self) -> str:
        article_text = ' '.join([i.get_text(separator=" ", strip=True).replace("\xa0", " ") for i in self.article_body_scrape.find_all('p')])
        return article_text

    def scrape_datetime(self) -> str:
        date_element = self.article_scrape.find('time', class_=self.datetime_class_name)
        if date_element and 'datetime' in date_element.attrs:
            datetime_value = date_element['datetime']
        else:
            datetime_value = '-'
        return datetime_value
    
    def get_full_data(self, user_duration) -> list: #call this func only
        links = self.scrape_links(user_duration)
        count = 0
        for link in links:
            print(f'link {count} was readed')
            count += 1
            self.scrape_article_body(link=link)
            article_text = f'{self.scrape_overview()} {self.scrape_article_text()}'
            article_type = determine_sphere(article_text)
            if self.scrape_article_text != 'None' and article_type is not None:
                self.data_store.append({
                    'title': self.scrape_title(),
                    'datetime': self.scrape_datetime(),
                    'article_text': article_text,
                    'type': article_type,
                    'source': self.source
                })
        return self.data_store
    
    def get(self) -> dict:
        msg = {"duration": "In post request enter duration in seconds 1 second is 50 news (approximately)"}
        return msg
    
    def post(self) -> Tuple[dict, int]:
        data = request.get_json()
        try:
            user_duration = float(data["duration"])
        except Exception as e:
            return {"error": "put int or float value"}, 400
        
        news = self.get_full_data(user_duration)
        return news, 200
        
        

class InterfaxParser(Resource, WebParser):

    def __init__(self) -> None:
        super().__init__()
        self.url = "https://www.interfax.ru/business/"
        self.base_url = "https://www.interfax.ru"
        self.links_class_name = 'timeline'
        self.title_class_name = "headline" #this is .find(itemprop="headline") parameter
        self.overview_class_name = "in" #plus itemprop="description"
        self.article_class_name = "articleBody" #this is .find(itemprop="articleBody") parameter
        self.source = "Интерфакс"
    
    def scrape_links(self, user_duration) -> list:
        super().start_driver()
        self.driver.get(self.url)
        time.sleep(2)

        start_time = time.time()
        duration = user_duration

        while True:
            print(f'{time.time() - start_time} - loaded data')
            link_elements = self.driver.find_elements(By.CSS_SELECTOR, '.timeline a')
            print(len(link_elements))
            self.driver.execute_script("getMoreTimeline()")
            time.sleep(1)
            if time.time() - start_time > duration:
                break

        link_elements = self.driver.find_elements(By.CSS_SELECTOR, '.timeline a')
        print(len(link_elements))
        return [element.get_attribute('href') for element in link_elements]
    
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

    def get_full_data(self, user_duration) -> list: #call this func only
        links = self.scrape_links(user_duration)
        count = 1
        for link in links:
            print(f'link {count} was readed')
            count += 1
            self.scrape_article_body(link=link)
            article_text = f'{self.scrape_overview()} {self.scrape_article_text()}'
            article_type = determine_sphere(article_text)
            if self.scrape_article_text != 'None' and article_type is not None:
                self.data_store.append({
                    'title': self.scrape_title(),
                    'datetime': self.scrape_datetime(),
                    'article_text': article_text,
                    'type': article_type,
                    'source': self.source
                })
        return self.data_store
    
    def get(self) -> dict:
        msg = {"duration": "In post request enter duration in seconds 1 second is 50 news (approximately)"}
        return msg
    
    def post(self) -> Tuple[dict, int]:
        data = request.get_json()
        try:
            user_duration = float(data["duration"])
        except Exception as e:
            return {"error": "put int or float value"}, 400
        
        news = self.get_full_data(user_duration)
        return news, 200

api.add_resource(RBCParser, '/service.internal/RBC')
api.add_resource(InterfaxParser, '/service.internal/Interfax')

if __name__ == '__main__':
    app.run(port=8000, debug=True)