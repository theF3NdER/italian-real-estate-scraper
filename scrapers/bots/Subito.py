from dataclasses import dataclass
from scrapers.bots.Scraper import Houses
from utils.custom_utils import swap_dict, typology_map
from nlp.others import handle_text_descriptions
import numpy as np

@dataclass
class SubitoHouses(Houses):

    def preprocess(self):
        self.floor_preproc()
        # self.df = self.df.drop('floor', axis=1)
        self.df = self.df.assign(typology = self.df['typology'].map(swap_dict(typology_map['subito'])))
        self.df, textFeatCol = handle_text_descriptions(self.df, 'title', 'description', self.logger)


        self.df = self.df.assign(interest = 0)
        self.df = self.df.assign(surface = self.df['surface'].str.extract(r"(\d+)"))
        # self.df = self.df.assign(price = self.df['price'].str.extract(r"(\d+.?\d+.?\d+)"))
        # self.df['price'] = self.df['price'].replace(r"(?<=\d)\.", '', regex=True)
        self.df['price'] = self.df['price'].str.replace('€', '')
        self.df['price'] = self.df['price'].str.replace('.', '')
        self.df = self.df.replace(r'^\s*$', np.nan, regex=True)

        try:
            self.df = self.df.astype({'surface': float, 'price': float})
            self.df = self.df.assign(eur_mq = round(self.df['price']/self.df['surface'], 2))
        except:
            pass
        
        self.df.loc[:, textFeatCol] = self.df.loc[:, textFeatCol].astype(bool)