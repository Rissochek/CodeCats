import requests
import json

url = "http://127.0.0.1:8000/save-articles/"
headers = {"Content-Type": "application/json"}
data = [
    {
        "title": "Test Title3",
        "datetime": "2023-10-01T12:00:00Z",
        "article_text": "This is a test article.",
        "source": "Test Source"
    },
    {
        "title": "Test Title1",
        "datetime": "2023-10-01T11:00:00Z",
        "article_text": "This is a test article.",
        "source": "Test Source"
    },
    {
        "title": "Test Title2",
        "datetime": "2023-10-01T14:00:00Z",
        "article_text": "This is a test article.",
        "source": "Test Source"
    }


]

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.status_code)
print(response.json())