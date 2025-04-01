import unittest
from unittest.mock import patch
from app import app

class TestGetLastPricesAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('requests.post')
    def test_get_last_prices_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = [
            {"company": "SBER", "end": "2025-04-02", "close": 250.5},
            {"company": "GAZP", "end": "2025-04-02", "close": 150.2},
            {"company": "LKOH", "end": "2025-04-02", "close": 350.0},
            {"company": "ROSN", "end": "2025-04-02", "close": 120.8},
            {"company": "VTBR", "end": "2025-04-02", "close": 5.1},
            {"company": "T", "end": "2025-04-02", "close": 450.3},
        ]
        
        response = self.app.get('/get_last_prices')
        self.assertEqual(response.status_code, 200)
        self.assertIn('SBER', response.json)
        self.assertEqual(response.json['SBER'], 250.5)
        self.assertEqual(response.json['GAZP'], 150.2)
        self.assertEqual(response.json['LKOH'], 350.0)
        self.assertEqual(response.json['ROSN'], 120.8)
        self.assertEqual(response.json['VTBR'], 5.1)
        self.assertEqual(response.json['T'], 450.3)

    @patch('requests.post')
    def test_get_last_prices_no_data(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = []
        
        response = self.app.get('/get_last_prices')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['SBER'], None)
        self.assertEqual(response.json['GAZP'], None)
        self.assertEqual(response.json['LKOH'], None)
        self.assertEqual(response.json['ROSN'], None)
        self.assertEqual(response.json['VTBR'], None)
        self.assertEqual(response.json['T'], None)

    @patch('requests.post')
    def test_get_last_prices_failed(self, mock_post):
        mock_post.return_value.status_code = 500
        
        response = self.app.get('/get_last_prices')
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json)

    @patch('requests.post')
    def test_get_last_prices_invalid_response(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = "invalid data"
        
        response = self.app.get('/get_last_prices')
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json)

if __name__ == '__main__':
    unittest.main()
