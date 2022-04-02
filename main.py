from pathlib import Path
from spiders.immobiliare import main as immobiliare
from scrapers.subito import main as subito
# from spiders.subito import main as subito
from modules.filters import main as filters
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


def main(scraper_name):
    date = pd.Timestamp.now().strftime("%Y-%m-%d")
    start_time=time.time()
    create_dir(parser.scraper[0])
    query = parser.query
    custom_logger, handler = setup_logger('main_logger', f"logs/{scraper_name}_{date}.log", level=logging.DEBUG)

    if scraper_name=='immobiliare':
        immobiliare(query=query, url=immobiliare_urls[query], logger=custom_logger, handler=handler)
    elif scraper_name=='subito':
        subito(typology=parser.typology, municipality=parser.municipality, trace=parser.trace, headless=parser.headless)
                    

if __name__=='__main__':
    if parser.mode=='filters':
        filters(parser.txt_filters, parser.price_filter, parser.surface_filter, parser.txt_hide)
    elif parser.mode=='scraping':
        if "subito" in parser.scraper:
            main("subito")
        elif "immobiliare" in parser.scraper:
            main("immobiliare")