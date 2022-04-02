from playwright.sync_api import sync_playwright
from utils.custom_utils import comuni_catania, typology_map, swap_dict
import numpy as np
from bs4 import BeautifulSoup
import logging
import pandas as pd
from tqdm import tqdm
import re
from urllib.parse import urlparse
from scrapers.bots.Scraper import House
from scrapers.bots.Subito import SubitoHouses
from math import ceil


def test(page):
    page.goto("https://www.subito.it/ville-singole-e-a-schiera/b-b-cod-a3-514-catania-372307732.htm")
    if page.is_visible("span:has-text('€')"):
        price = page.locator("span:has-text('€')").first.inner_text()
        print(price)


def open_context(browser, trace):
    context = browser.new_context(ignore_https_errors=True)
    if trace:
        context.tracing.start(screenshots=True, snapshots=True)
    context.set_default_timeout(60*1000)
    return context


def main(typology: str, municipality: list, trace: bool, headless: bool):
    logger = logging.getLogger("main_logger")

    if municipality==[]:
        municipality = comuni_catania
    municipality = [c.replace('\'', '-').replace(' ', '-').lower() for c in municipality]

    with sync_playwright() as spw:
        browser = spw.chromium.launch(headless=headless)
        context = open_context(browser, trace)

        page = context.new_page()

        house_links = {}
        for m in municipality:
            for t in typology:
                house_links[m] = {swap_dict(typology_map['subito'])[t]: []}
                try:
                    page.goto(f"https://www.subito.it/annunci-sicilia/vendita/{t}/catania/{m}")
                    navs_txt = ' '.join(page.locator("nav").all_inner_texts())
                    max_page = max([int(n) for n in re.findall(r"(\d+)", navs_txt)])
                except:
                    max_page = 1

                for page_n in range(1, max_page+1):
                    page.goto(f"https://www.subito.it/annunci-sicilia/vendita/{t}/catania/{m}/?o={page_n}",
                                wait_until='domcontentloaded', timeout=30*1000)
                    houses_html = page.locator('.items').first.inner_html()
                    soup = BeautifulSoup(houses_html, 'html.parser')
                    house_links[m][swap_dict(typology_map['subito'])[t]].extend([l['href'] for l in soup.find_all('a', href=True)
                                        if urlparse(l['href']).path.startswith('/'+t)])
            print(house_links.keys())
        page.close()
        context.close()

        houses = []
        for m in house_links.keys():
            for t in house_links[m].keys():
                hl_stacks = np.array_split(house_links[m][t], ceil(len(house_links[m][t])/250))
                for hl_stack in hl_stacks:
                    context = open_context(browser, trace)
                    for link in tqdm(hl_stack, total=len(hl_stack)):
                        page = context.new_page()
                        page.route(re.compile(r"(\.png$)|(\.jpg$)"), lambda route: route.abort())

                        page.goto(link, wait_until='domcontentloaded')
                        title = page.locator('h1').first.inner_text()
                        surface = page.locator("text=/\d+ mq/").first.inner_text()
                        description = page.locator('p:below(:text("Descrizione"))').first.inner_text()
                        index = int(re.findall(r"(\d+)", page.url)[-1])
                        house = House(index, 'subito', link, t, m, title, surface, description)
                        
                        if page.is_visible("span:has-text('€')"):
                            price = page.locator("span:has-text('€')").first.inner_text()
                            house.price = price
                        else:
                            house.price = ''

                        if page.is_visible('span:right-of(:text("Piano"))'):
                            ait = ' '.join(page.locator('span:right-of(:text("Piano"))').all_inner_texts())
                            house.floor = re.findall(r"\d{1}", ait)[0]
                        else:
                            house.floor = ''
                        
                        if page.is_visible('span:right-of(:text("Locali"))'):
                            ait = ' '.join(page.locator('span:right-of(:text("Locali"))').all_inner_texts())
                            house.rooms = re.findall(r"\d{1,2}", ait)[0]
                        else:
                            house.rooms = ''
                        houses.append(house)
                        page.close()
                    context.close()

        df = pd.DataFrame(houses)
        df.to_csv("house.csv", index=False)
        print(df)
        houses = SubitoHouses(df)
        houses.preprocess()
        houses.dump(pd.Timestamp.now().strftime("%Y-%m-%d"))
                    
