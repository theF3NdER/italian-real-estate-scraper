import pandas as pd
import requests
import re
import numpy as np
from custom_parser import typology_map
from utils.custom_utils import swap_dict
from nlp.others import handle_text_descriptions


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
    
    def preprocess(self):
        # renaming
        self.df = self.df.drop('floor', axis=1)
        rename_mapping = {
                            "price.value": "price",
                            "location.latitude": "latitude",
                            "location.longitude": "longitude",
                            "typology.name": "typology",
                            "floor.value": "floor",
                            "price.loweredPrice.originalPrice": "original_price",
                            "price.loweredPrice.passedDays": "passedDays",
                            "id": "id",
                            "title": "title",
                            "rooms": "rooms",
                            "link": "link",
                            "surface": "surface",
                            "description": "description"
                        }
        self.df = self.df.rename(columns=rename_mapping, errors='ignore')
        self.df = self.df.loc[:, [v for v in rename_mapping.values() if v in self.df.columns]]
        self.floor_preproc()
        self.df = self.df.assign(typology = self.df['typology'].map(swap_dict(typology_map['immobiliare'])))
        self.df, textFeatCol = handle_text_descriptions(self.df, 'title', 'description', self.logger)


        self.df = self.df.assign(interess = 0)
        self.df = self.df.assign(surface = self.df['surface'].str.extract(r"(\d+)"))
        self.df = self.df.replace(r'^\s*$', np.nan, regex=True)
        self.df = self.df.astype({'surface': float, 'price': float})
        self.df = self.df.assign(eur_mq = round(self.df['price']/self.df['surface'], 2))
        if "original_price" in self.df.columns:
            self.df = self.df.assign(original_price = self.df['original_price'].str.replace('.', '', regex=False))
            self.df = self.df.assign(original_price = self.df['original_price'].str.extract(r"(\d+)"))
        self.df.loc[:, textFeatCol] = self.df.loc[:, textFeatCol].astype(bool)


    def dump(self, date):
        try:
            df_old = pd.read_csv(f"data/immobiliare/{self.query}.csv")

            removed = df_old[~df_old['id'].isin(self.df['id'])]
            new = self.df[~self.df['id'].isin(df_old['id'])]
            common = df_old[df_old['id'].isin(self.df['id'])]

            removed['remove_date'] = removed['remove_date'].fillna(date)
            new = new.assign(remove_date = np.nan)
            common = common.assign(remove_date = np.nan)

            removed = removed.assign(scrape_date = removed['scrape_date'])
            new = new.assign(scrape_date = date)
            common = common.assign(scrape_date = common['scrape_date'])

            # removed = removed.assign(last_check = date)
            new = new.assign(check_date = date)
            common = common.assign(check_date = date)

            self.df = pd.concat([new, removed, common], ignore_index=True)
        except FileNotFoundError:
            self.df = self.df.assign(remove_date = np.nan)
            self.df = self.df.assign(scrape_date = date)
            self.df = self.df.assign(check_date = date)
        
        self.df.to_csv(f"data/immobiliare/{self.query}.csv", index=False)


    def floor_preproc(self):
        p = self.df['floor']

        p = p.str.lower()
        p = p.str.replace(" terra", '0')
        p = p.str.replace(" rialzato", '0')
        p = p.str.replace(" con ascensore", '')
        p = p.str.replace("piano", '')
        p = p.str.replace(" con accesso disabili", '')
        p = p.str.replace('[^\w\s-]','', regex=True)
        p = p.str.replace("seminterrato", '-1')
        p = p.str.replace("interrato -1", '-1')
        p = p.str.replace("interrato -2", '-2')
        p = p.str.replace(' $', '', regex=True)

        piano = p.str.extract("(-?\d+).*(-?\d+)", expand=True)
        piano.columns = ['piano_min', 'piano_max']
        piano = piano.assign(PIÙ_LIVELLI = ~piano['piano_min'].isna())
        piano.loc[:, ['piano_min', 'piano_max']] = piano.loc[:, ['piano_min', 'piano_max']].astype(float, errors='ignore')
        piano['piano_max'] = piano['piano_max'].combine_first(p)

        self.df = self.df.assign(floor = piano['piano_max'])


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
    spider.preprocess()
    spider.dump(date)