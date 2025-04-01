import unittest
import json
from unittest.mock import patch
from company_news_api import app

class TestCompanyNewsAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('requests.post')
    def test_valid_request(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = [
            {"title": "Сбер увеличил прибыль", "article_text": "Сбербанк сообщил о росте прибыли."},
            {"title": "Газпром запустил новый проект", "article_text": "Газпром начал разработку нового месторождения."}
        ]
        
        response = self.app.post('/service.internal/get_company_news', json={"companies": ["SBER"], "limit": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertIn("Сбер", response.json[0]["title"])
    
    @patch('requests.post')
    def test_invalid_company(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = [
            {"title": "Роснефть инвестирует в добычу", "article_text": "Роснефть объявила о новых инвестициях."}
        ]
        
        response = self.app.post('/service.internal/get_company_news', json={"companies": ["UNKNOWN"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 0)
    
    @patch('requests.post')
    def test_no_companies_provided(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = [
            {"title": "Сбербанк снижает ставки", "article_text": "Сбербанк объявил о снижении процентных ставок."}
        ]
        
        response = self.app.post('/service.internal/get_company_news', json={"companies": []})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 0)
    
    @patch('requests.post')
    def test_limit_functionality(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = [
            {"title": "Сбербанк Новости 1", "article_text": "Новость 1."},
            {"title": "Сбербанк Новости 2", "article_text": "Новость 2."},
            {"title": "Сбербанк Новости 3", "article_text": "Новость 3."}
        ]
        
        response = self.app.post('/service.internal/get_company_news', json={"companies": ["SBER"], "limit": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 2)
    
    @patch('requests.post')
    def test_service_unavailable(self, mock_post):
        mock_post.return_value.status_code = 500
        
        response = self.app.post('/service.internal/get_company_news', json={"companies": ["SBER"]})
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json)

if __name__ == '__main__':
    unittest.main()
