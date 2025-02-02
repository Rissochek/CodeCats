from parser import InterfaxParser, RBCParser
import json

interfax_scraper = InterfaxParser()
rbc_scraper = RBCParser()

with open("data.json", 'w', encoding='utf-8') as json_file:
    inter_data = interfax_scraper.get_full_data()
    rbc_data = rbc_scraper.get_full_data()
    full_data = inter_data + rbc_data
    json.dump(full_data, json_file, ensure_ascii=False, indent=4)
