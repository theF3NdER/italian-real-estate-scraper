import argparse
from utils.custom_utils import comuni_catania, typology_map, immobiliare_urls
import pandas as pd

parser = argparse.ArgumentParser(prog="REAL ESTATE SCRAPER")
subparser = parser.add_subparsers(dest='command')

try:
        df = pd.read_csv('data/houses.csv')
        txt_choices = [c.split('_')[0] for c in df.columns if c.endswith('_text')]
except FileNotFoundError:
        txt_choices = []

if len(immobiliare_urls)>0:
        query_choices = [k for k in immobiliare_urls.keys() if '_' not in k]
else:
        query_choices = []

filter_parser = subparser.add_parser('filters',
                                        help='this will run the program in filtering mode')
filter_parser.add_argument('--txt_filters', '-f',
                                help="Select the textual features to keep",
                                type=str,
                                choices=txt_choices,
                                nargs = '+',
                                default=[],
                                dest="txt_filters")



scraping_parser = subparser.add_parser('scraping',
                                        help='this will run the program in scraping mode')
scraping_parser.add_argument('--scraper', '-s',
                                help="Select the scraper to run",
                                type=str,
                                choices=["immobiliare", "subito"],
                                nargs = 1,
                                default=["immobiliare"],
                                dest="scraper")
scraping_parser.add_argument('--query', '-q',
                                help="Select the query for immobiliare.it",
                                type=str,
                                choices=query_choices,
                                nargs = 1,
                                required=False,
                                default="small",
                                dest="query")
scraping_parser.add_argument('--municipality', '-m',
                                help="Seleziona il comune per subito",
                                type=str,
                                choices=comuni_catania,
                                nargs = '+',
                                required=False,
                                default=comuni_catania,
                                dest="municipality")
scraping_parser.add_argument('--typology', '-t',
                                help="Set the kind of realty (ig: apartment, villa)",
                                type=str,
                                choices=["ville", "appartamenti"],
                                nargs = '+',
                                required=False,
                                default=["appartamenti"],
                                dest="typology")
scraping_parser.add_argument('--trace',
                                help="Select whether or not to show the browser. True by default",
                                action='store_true',
                                dest='trace', default=False)
scraping_parser.add_argument('--headless',
                                help="Select whether or not to show the browser. True by default (showing)",
                                action='store_true',
                                dest='headless', default=False)

args =  parser.parse_args()

if args.command == "scraping":
        scraper = args.scraper

        typology = []
        for t in args.typology:
                for s in scraper:
                        typology.extend(typology_map[s][t])
        query = args.query
        municipality = args.municipality
        trace = args.trace
        headless = args.headless
elif args.command == "filters":
        txt_filters = args.txt_filters
        pass
