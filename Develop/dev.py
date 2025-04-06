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
from fake_useragent import UserAgent
import requests
import re
import asyncio
import httpx
import pymorphy3
import time

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
        options.add_argument(f"user-agent={self.ua.random}")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    @abstractmethod
    def scrape_links(self, num_of_news) -> list:
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
    def get_full_data(self, num_of_news) -> list:
        pass

    @abstractmethod
    def get(self) -> dict:
        pass

    @abstractmethod
    def post(self) -> Tuple[dict, int]:
        pass

class InterfaxParser(Resource, WebParser):

    def __init__(self) -> None:
        super().__init__()
        self.ua = UserAgent()
        super().start_driver()
        self.url = "https://www.interfax.ru/business/"
        self.links_class_name = 'timeline'
        self.async_client = httpx.AsyncClient()
        self.ua = UserAgent()
        self.title_class_name = "headline" #this is .find(itemprop="headline") parameter
        self.overview_class_name = "in" #plus itemprop="description"
        self.article_class_name = "articleBody" #this is .find(itemprop="articleBody") parameter
        self.source = "Интерфакс"
        self.links = []
    
    def scrape_links(self, num_of_news_requested) -> list:
        self.driver.get(self.url)
        link_elements = []
        while len(link_elements) < num_of_news_requested:
            WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.timeline a')))
            link_elements = self.driver.find_elements(By.CSS_SELECTOR, '.timeline a')
            self.driver.execute_script("getMoreTimeline()")

        self.links = [element.get_attribute('href') for element in link_elements][:num_of_news_requested+20]
    
    def scrape_title(self, article_scrape) -> str:
        try:
            title = article_scrape.find("h1", itemprop=self.title_class_name)
            title.text.strip()
        except AttributeError:
            return "No Title"
        
        return title.get_text(separator=" ", strip=True).replace("\xa0", " ")

    def scrape_overview(self) -> str:
        return ''

    async def scrape_article_body(self, link) -> None:
        headers = {
            "User-Agent": self.ua.random,
            "Accept-Language": "ru-RU,ru;q=0.9",
            "Referer": "https://www.google.com/",
            "Accept-Encoding": "gzip, deflate, br"
        }
        try: 
            response = await self.async_client.get(link, headers=headers)
        except Exception as e:
            print("failed get article body", e)
            return None, None
        
        response.encoding = 'windows-1251'
        article_scrape = BeautifulSoup(response.text, self.parser_type)
        article_body_scrape = article_scrape.find("article", itemprop=self.article_class_name)
        return article_scrape, article_body_scrape
    
    def scrape_article_text(self, article_body_scrape) -> str:
        if (article_body_scrape != None):
            article_text = ' '.join([i.get_text(separator=" ", strip=True).replace("\xa0", " ") for i in article_body_scrape.find_all('p')])
        else:
            article_text = 'None'
        return article_text

    def scrape_datetime(self, article_scrape) -> str:
        try:
            date_element = article_scrape.find('time')
        except Exception as e:
            print("error data", e)
            datetime_value = '-'
            return
        if date_element and 'datetime' in date_element.attrs:
            datetime_value = date_element['datetime']
        else:
            datetime_value = '-'
        return datetime_value

    def get_full_data(self, num_of_news) -> list: #call this func only
        self.scrape_links(num_of_news)
        results = asyncio.run(self.async_get_data())
        return results
        
    async def async_get_data(self):
        tasks = [self.get_data(link) for link in self.links]
        results = await asyncio.gather(*tasks)
        return results
    
    async def get_data(self, link):
        try:
            article_scrape, article_body_scrape = await self.scrape_article_body(link=link)
        except Exception as e:
            print("cant get article", e)
            return
        article_text = f'{self.scrape_overview()} {self.scrape_article_text(article_body_scrape)}'
        article_type = determine_sphere(article_text)
        if self.scrape_article_text(article_body_scrape) != 'None' and article_type is not None:
            return {
                    'title': self.scrape_title(article_scrape),
                    'datetime': self.scrape_datetime(article_scrape),
                    'article_text': article_text,
                    'type': article_type,
                    'source': self.source
                }
        else:
            return ''
            
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
        return news, 200
    
    def __del__(self):
        if self.driver:
            self.driver.quit()
        if self.async_client:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.async_client.aclose())
                else:
                    loop.run_until_complete(self.async_client.aclose())
            except RuntimeError:
                asyncio.run(self.async_client.aclose())
            except Exception as e:
                print(f"Error closing client: {e}")
    
app = Flask(__name__)
api = Api(app)

api.add_resource(InterfaxParser, '/service.internal/Interfax')

if __name__ == '__main__':
    app.run(port=8000, debug=False)















# options = Options()
# options.add_argument("--headless")
# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
# print(driver.service.path)

#C:\Users\rusla\.wdm\drivers\chromedriver\win64\134.0.6998.165\chromedriver-win32/chromedriver.exe