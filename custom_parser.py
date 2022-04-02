import argparse
from utils.custom_utils import comuni_catania, typology_map

parser = argparse.ArgumentParser()
parser.add_argument('--scraper', '-s',
                    help="Select the scraper to run",
                    type=str,
                    choices=["immobiliare", "subito"],
                    nargs = 1,
                    default="immobiliare",
                    dest="scraper")
parser.add_argument('--query', '-q',
                    help="Select the query for immobiliare.it",
                    type=str,
                    choices=["studenti", "villetta_sacro_cuore", 
                            "immobile_mare_ct_riposto", "immobile_mare",
                            "singola_area_provincia", "immobile_area_provincia",
                            "mamma_globale", "small", "casetta"
                            ],
                    nargs = 1,
                    required=False,
                    default="small",
                    dest="query")
parser.add_argument('--municipality', '-m',
                    help="Seleziona il comune per subito",
                    type=str,
                    choices=comuni_catania,
                    nargs = '+',
                    required=False,
                    default=comuni_catania,
                    dest="municipality")
parser.add_argument('--typology', '-t',
                    help="Set the kind of realty (ig: apartment, villa)",
                    type=str,
                    choices=["ville", "appartamenti"],
                    nargs = '+',
                    required=False,
                    default=["appartamenti"],
                    dest="typology")
parser.add_argument('--trace',
                    help="Select whether or not to show the browser. True by default",
                    action='store_true',
                    dest='trace', default=False)
parser.add_argument('--headless',
                    help="Select whether or not to show the browser. True by default (showing)",
                    action='store_true',
                    dest='headless', default=False)

args =  parser.parse_args()
scraper = args.scraper

typology = []
for t in args.typology:
    for s in scraper:
        typology.extend(typology_map[s][t])
query = args.query
municipality = args.municipality
trace = args.trace
headless = args.headless