import requests
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time


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
    def scrape_links(self) -> list:
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
    def get_full_data(self) -> list:
        pass

class RBCParser(WebParser):
    def __init__(self) -> None:
        super().__init__()
        self.url = 'https://www.rbc.ru/economics/'
        self.links_class_name = 'item__link rm-cm-item-link js-rm-central-column-item-link'
        self.title_class_name = 'article__header__title-in js-slide-title'
        self.overview_class_name = 'article__text__overview'
        self.article_class_name = 'article__text article__text_free'
        self.datetime_class_name = 'article__header__date'
        self.source = 'РБК'
                
    def scrape_links(self) -> list:
        super().start_driver()
        self.driver.get(self.url)
        time.sleep(2)

        start_time = time.time()
        duration = 2

        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
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
    
    def get_full_data(self) -> list: #call this func only
        links = self.scrape_links()
        for link in links:
            self.scrape_article_body(link=link)
            self.data_store.append({
            'title': self.scrape_title(),
            'datetime': self.scrape_datetime(),
            'article_text': f'{self.scrape_overview()} {self.scrape_article_text()}',
            'source': self.source
            })
        return self.data_store

class InterfaxParser(WebParser):
    def __init__(self) -> None:
        super().__init__()
        self.url = "https://www.interfax.ru/business/"
        self.base_url = "https://www.interfax.ru"
        self.links_class_name = 'timeline'
        self.title_class_name = "headline" #this is .find(itemprop="headline") parameter
        self.overview_class_name = "in" #plus itemprop="description"
        self.article_class_name = "articleBody" #this is .find(itemprop="articleBody") parameter
        self.source = "Интерфакс"
    
    def scrape_links(self) -> list:
        super().start_driver()
        self.driver.get(self.url)
        time.sleep(2)

        start_time = time.time()
        duration = 2

        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if time.time() - start_time > duration:
                break
            
            if new_height == last_height:
                break
            last_height = new_height

        scrape = BeautifulSoup(self.driver.page_source, self.parser_type)
        links_scrape = scrape.find("div", class_="timeline")
        return [i['href'] for i in links_scrape.find_all('a')]
    
    def scrape_title(self) -> str:
        title = self.article_scrape.find("h1", itemprop=self.title_class_name)
        return title.get_text(separator=" ", strip=True).replace("\xa0", " ")

    def scrape_overview(self) -> str:
        return ''

    def scrape_article_body(self, link) -> None:
        response = requests.get(link)
        response.encoding = 'windows-1251'
        if response.status_code != 200:
            print("Error: wrong status code", response.status_code)
            exit()
        
        self.article_scrape = BeautifulSoup(response.text, self.parser_type)
        self.article_body_scrape = self.article_scrape.find("article", itemprop=self.article_class_name)
    
    def scrape_article_text(self) -> str:
        if (self.article_body_scrape != None):
            article_text = ' '.join([i.get_text(separator=" ", strip=True).replace("\xa0", " ") for i in self.article_body_scrape.find_all('p')])
        else:
            article_text = 'None'
        return article_text

    def scrape_datetime(self) -> str:
        date_element = self.article_scrape.find('time')
        if date_element and 'datetime' in date_element.attrs:
            datetime_value = date_element['datetime']
        else:
            datetime_value = '-'
        return datetime_value

    def get_full_data(self) -> list: #call this func only
        links = self.scrape_links()
        for link in links:
            link = self.base_url + link
            self.scrape_article_body(link=link)
            if self.scrape_article_text != 'None':
                self.data_store.append({
                    'title': self.scrape_title(),
                    'datetime': self.scrape_datetime(),
                    'article_text': f'{self.scrape_overview()} {self.scrape_article_text()}',
                    'source': self.source
                })
        return self.data_store