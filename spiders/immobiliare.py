import pandas as pd
import requests
import re
import numpy as np
from custom_parser import typology_map
from utils.custom_utils import swap_dict
from nlp.others import handle_text_descriptions
from scrapers.bots.Immobiliare import ImmobiliareHouses


class ImmobiliareSpider():
    def __init__(self, query, url, logger) -> None:
        self.name = "immobiliare"
        self.page = 1
        self.query = query
        self.url = url
        self.max_pages = 81 # 80 seems to be a kind of hard limit
        self.df_pages = []
        self.logger = logger
        self.df = pd.DataFrame()
    
    def set_max_pages(self, max_pages):
        self.max_pages = max_pages
    
def main(query, url, logger, handler):
    spider = ImmobiliareSpider(query, url, logger)
    response = requests.get(url).json()
    spider.set_max_pages(min(response['maxPages'], 81))
    date = pd.Timestamp.now().strftime("%Y-%m-%d")

    for page in range(1, spider.max_pages):
        response = requests.get(re.sub(r"(?<=pag\=)\d+", str(page), spider.url)).json()
        houses_response_dict = response['results']

        houses = [d['realEstate'] for d in houses_response_dict]
        df = pd.json_normalize(houses)
        properties = df['properties'].apply(pd.Series)[0]
        properties = pd.DataFrame(properties.tolist()).to_dict(orient='records')
        properties = pd.json_normalize(properties)
        df = df.drop(set(df.columns).intersection(set(properties.columns)), axis=1)
        df = df.drop('properties', axis=1)
        df = df.join(properties)
        df['link'] = df['id'].apply(lambda x: f"https://www.immobiliare.it/annunci/{x}/")
        spider.df_pages.append(df)

    spider.df = pd.concat(spider.df_pages, ignore_index=True)
    houses = ImmobiliareHouses(spider.df)
    houses.preprocess()
    houses.dump('immobiliare', date)