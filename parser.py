import requests
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod

class WebParser(ABC):
    def __init__(self) -> None:
        self.url = ''
        self.parser_type = 'html.parser'
        self.links_class_name = ''
        self.title_class_name = ''
        self.overview_class_name = ''
        self.article_class_name = ''
        self.datetime_class_name = ''
        self.article_scrape = ''
        self.article_body_scrape = ''
        self.data_store = []
    @abstractmethod
    def scrape_links(self) -> None:
        pass

    @abstractmethod
    def scrape_title(self) -> str:
        pass

    @abstractmethod
    def scrape_overview(self) -> str:
        pass
    
    @abstractmethod
    def scrape_article_body(self) -> None:
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
        response = requests.get(url=self.url)
        if (response.status_code != 200):
            print("Error: wrong status code", response.status_code)
            exit()

        scrape = BeautifulSoup(response.text, self.parser_type)
        return [i['href'] for i in scrape.find_all('a', class_=self.links_class_name)]
    
    def scrape_title(self) -> str:
        title = self.article_scrape.find('h1', class_=self.title_class_name).get_text(separator=" ", strip=True).replace("\xa0", " ")
        return title
    
    def scrape_overview(self) -> str:
        overview = self.article_body_scrape.find('div', class_=self.overview_class_name)
        if overview != None:
            overview = overview.get_text(separator=" ", strip=True).replace("\xa0", " ")
        else:
            overview = '-'
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
            'overview': self.scrape_overview(),
            'article_text': self.scrape_article_text(),
            'source': self.source
            })
        return self.data_store


            
            

