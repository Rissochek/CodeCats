import unittest
from unittest.mock import patch
from predict_price import app

class TestPredictPricesAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('requests.post')
    def test_predict_prices_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = [
            {"company": "SBER", "end": "2025-04-02", "close": 250.5},
            {"company": "GAZP", "end": "2025-04-02", "close": 150.2},
            {"company": "LKOH", "end": "2025-04-02", "close": 350.0},
            {"company": "ROSN", "end": "2025-04-02", "close": 120.8},
            {"company": "VTBR", "end": "2025-04-02", "close": 5.1},
            {"company": "T", "end": "2025-04-02", "close": 450.3},
        ]
        
        response = self.app.get('/predict_prices')
        self.assertEqual(response.status_code, 200)
        self.assertIn('SBER', response.json)
        self.assertIn('GAZP', response.json)
        self.assertIn('LKOH', response.json)
        self.assertIn('ROSN', response.json)
        self.assertIn('VTBR', response.json)
        self.assertIn('T', response.json)

    @patch('requests.post')
    def test_predict_prices_failed(self, mock_post):
        mock_post.return_value.status_code = 500
        
        response = self.app.get('/predict_prices')
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json)

    @patch('requests.post')
    def test_predict_prices_no_data(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = []
        
        response = self.app.get('/predict_prices')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 0)

if __name__ == '__main__':
    unittest.main()
