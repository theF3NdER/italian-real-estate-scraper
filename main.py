from pathlib import Path
from spiders.immobiliare import main as immobiliare
from spiders.subito import main as subito
import custom_parser as parser
import os
import time
from utils.custom_utils import setup_logger, log_end, log_start, immobiliare_urls
import logging
import pandas as pd



def create_dir(scraper):
    download_dir = f"{os.getcwd()}/data/{scraper}/daily/"
    if not os.path.isdir(download_dir):
        os.makedirs(download_dir, 0o777, exist_ok=False)


def main(scraper_name, kind, comune=''):
    date = pd.Timestamp.now().strftime("%Y-%m-%d")
    start_time=time.time()
    # create_dir(parser.scraper)
    query = parser.query[0]
    custom_logger, handler = setup_logger('logger', f"logs/{query}_{date}.log", level=logging.DEBUG)

    if scraper_name=='immobiliare':

        immobiliare(query=query, url=immobiliare_urls[query], logger=custom_logger, handler=handler)

        elapsed_time = time.time()-start_time
        print("ended")
    elif scraper_name=='subito':
        custom_logger = setup_logger('logger', f"log/subito_{date}.log", level=logging.DEBUG)
        subito(cosa=kind, citta="catania", custom_logger=custom_logger)
                    

if __name__=='__main__':
    if "subito" in parser.scraper:
        for kind in parser.typologies:
            for comune in parser.comune:
                main(parser.scraper[0], kind, comune)

        p_gius = Path(f"{os.getcwd()}/data/subito/comuni/")
        comuni_to_concat = []
        for csv_file in list(p_gius.glob('*.csv')):
            df_comune = pd.read_csv(csv_file)
            comuni_to_concat.append(df_comune)
        comuni_df = pd.concat(comuni_to_concat, ignore_index=True)
        comuni_df.to_csv(f"{os.getcwd()}/data/subito/subito.csv", index=False)
    elif "immobiliare" in parser.scraper:
        main(parser.scraper[0], parser.typology, parser.comune)


    # for scraper_name in ['immobiliare', 'subito']:
    #     main(scraper_name)