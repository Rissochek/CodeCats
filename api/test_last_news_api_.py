import unittest
from unittest.mock import patch
from last_news_api import app


class TestGetLastNewsAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('requests.post')
    def test_get_last_news_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = [
            {"title": "News 1", "datetime": "2025-04-02T12:30:00", "article_text": "Text of news 1"},
            {"title": "News 2", "datetime": "2025-04-02T13:00:00", "article_text": "Text of news 2"},
            {"title": "News 3", "datetime": "2025-04-02T14:00:00", "article_text": "Text of news 3"},
            {"title": "News 4", "datetime": "2025-04-02T15:00:00", "article_text": "Text of news 4"},
            {"title": "News 5", "datetime": "2025-04-02T16:00:00", "article_text": "Text of news 5"},
            {"title": "News 6", "datetime": "2025-04-02T17:00:00", "article_text": "Text of news 6"},
        ]
        
        response = self.app.get('/get_last_news')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.json), 5)

        self.assertTrue(response.json[0]["datetime"] > response.json[1]["datetime"])

    @patch('requests.post')
    def test_get_last_news_failed(self, mock_post):
        mock_post.return_value.status_code = 500
        
        response = self.app.get('/get_last_news')

        self.assertIn("error", response.json)

    @patch('requests.post')
    def test_get_last_news_empty_response(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = []
        
        response = self.app.get('/get_last_news')

        self.assertEqual(len(response.json), 0)

    @patch('requests.post')
    def test_get_last_news_exception(self, mock_post):
        # Мокаем исключение при запросе
        mock_post.side_effect = Exception("Service is down")
        
        response = self.app.get('/get_last_news')

        # Проверяем, что при исключении возвращается ошибка
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json)


if __name__ == '__main__':
    unittest.main()
