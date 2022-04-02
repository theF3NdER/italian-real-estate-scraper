from dataclasses import dataclass, field
from scrapers.bots.Scraper import Houses, House
from utils.custom_utils import swap_dict, typology_map
from nlp.others import handle_text_descriptions
import numpy as np


@dataclass
class ImmobiliareHouse(House):
    price: float = field(init=False)
    latitude: float = field(init=False)
    longitude: float = field(init=False)
    original_price: float = field(init=False)
    passedDays: float = field(init=False)
    surface: int = field(init=True)




@dataclass
class ImmobiliareHouses(Houses):
    
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
        self.df = self.df.assign(website = 'immobiliare')
        self.floor_preproc()
        self.df = self.df.assign(typology = self.df['typology'].map(swap_dict(typology_map['immobiliare'])))
        self.df, textFeatCol = handle_text_descriptions(self.df, 'title', 'description', self.logger)


        self.df = self.df.assign(interest = 0)
        self.df = self.df.assign(surface = self.df['surface'].str.extract(r"(\d+)"))
        self.df = self.df.replace(r'^\s*$', np.nan, regex=True)
        self.df = self.df.astype({'surface': float, 'price': float})
        self.df = self.df.assign(eur_mq = round(self.df['price']/self.df['surface'], 2))
        if "original_price" in self.df.columns:
            self.df = self.df.assign(original_price = self.df['original_price'].str.replace('.', '', regex=False))
            self.df = self.df.assign(original_price = self.df['original_price'].str.extract(r"(\d+)"))
        self.df.loc[:, textFeatCol] = self.df.loc[:, textFeatCol].astype(bool)
