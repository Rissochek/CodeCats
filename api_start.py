import subprocess


files = [r"./database_manager/database.py",
         r"./api/company_news_api.py", r"./api/last_news_api.py", r"./api/last_price_api.py"]
for file in files:
    subprocess.Popen(args=["start", "python", file],
                     shell=True, stdout=subprocess.PIPE)
