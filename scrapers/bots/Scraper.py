from dataclasses import dataclass, field
import logging
import pandas as pd
import numpy as np

@dataclass
class House:
    id: int = field(init=True)
    website: str = field(init=True)
    link: str = field(init=True)
    typology: str = field(init=True)
    municipality: str = field(init=True)
    title: str = field(init=True)
    surface: str = field(init=True)
    description: str = field(init=True)
    price: str = field(init=False)
    floor: str = field(init=False)
    rooms: str = field(init=False)

@dataclass
class Houses:
    df: pd.DataFrame = field(init=True)
    logger = logging.getLogger("main_logger")


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


    def dump(self, date):
        try:
            df_old = pd.read_csv(f"data/houses.csv")

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
        
        self.df.to_csv(f"data/houses.csv", index=False)