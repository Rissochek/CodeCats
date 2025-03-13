from parser import InterfaxParser, RBCParser
import json
import pandas as pd
interfax_scraper = InterfaxParser()
rbc_scraper = RBCParser()

with open("data.json", 'w', encoding='utf-8') as json_file:
    inter_data = interfax_scraper.get_full_data()
    rbc_data = rbc_scraper.get_full_data()
    full_data = inter_data + rbc_data
    df = pd.DataFrame(full_data)
    df.to_parquet('webnews.parquet', index=False)
    json.dump(full_data, json_file, ensure_ascii=False, indent=4)
