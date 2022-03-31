import logging
import os

def setup_logger(name, log_file,
                 formatter=logging.Formatter('%(asctime)s %(levelname)s %(message)s'),
                 level=logging.INFO):
    """
    Function to setup a generic loggers.

    :param name: name of the logger
    :type name: str
    :param log_file: file of the log
    :type log_file: str
    :param formatter: formatter to be used by the logger
    :type formatter: logging.Formatter
    :param level: level to display
    :type level: int
    :return: the logger
    :rtype: logging.Logger
    """
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger, handler

def log_start(args, debug_logger, name):
    debug_logger.info(f'=== {name} started ===')
    debug_logger.info(f'cwd {os.getcwd()}')
    msg = 'arguments:'
    for k, v in vars(args).items():
        msg = f'{msg} {k!r}: {v!r}'
    debug_logger.info(msg)


def log_end(debug_logger, name):
    debug_logger.info(f'=== {name} ended ===')



comuni_catania = [c.replace('\'', '-').replace(' ', '-').lower() for c in [
                    "Gravina di Catania",
                    "Mascalucia",
                    "Aci Castello",
                    "Catania",
                    "Acireale",
                    "Aci Catena",
                    "Giarre",
                    "San Giovanni la Punta",
                    "Tremestieri Etneo",
                    "Aci Sant'Antonio",
                    "Riposto",
                    "Pedara",
                    "Mascali",
                    "San Gregorio di Catania",
                    "Trecastagni",
                    "Sant'Agata Li Battiati",
                    "Viagrande",
                    "San Pietro Clarenza",
                    "Valverde",
                    "Nicolosi",
                    "Aci Bonaccorsi",
                    ]]

typology_map = {
    "subito": {
        "ville": ["ville-singole-e-a-schiera"],
        "appartamenti": ["appartamenti"],
    },
    "immobiliare": {
        "ville": ["Villa unifamiliare", "Villa bifamiliare", "Villa", "Villa a schiera"],
        "appartamenti": ["Appartamento in villa", "Villa plurifamiliare",
                        "Appartamento", "Attico"],
        "terratetti": ["Terratetto unifamiliare", "Terratetto plurifamiliare"],
        "rustici": ["Casale", "Cascina", "Rustico"],
        "mansarde": ["Mansarda"]
    }
}

def swap_dict(dict):
    newDict = {}
    for key,value in dict.items():
        for val in value:
            if val in newDict:
                newDict[val].append(key)
            else:
                newDict[val] = key
    return newDict

# Immobiliare
# {"Villa unifamiliare": "Villa",
# "Terratetto unifamiliare": "Terratetto",
# "Terratetto plurifamiliare": "Terratetto",
# "Villa a schiera": "Schiera",
# "Villa bifamiliare": "Villa",
# "Appartamento in villa": "Appartamento",
# "Villa plurifamiliare": "Appartamento",
# "Appartamento": "Appartamento",
# "Attico": "Appartamento",
# "Casale": "Rustico",
# "Cascina": "Rustico",
# "Rustico": "Rustico",
# "Villa": "Villa",
# "Terreno edificabile": "Terreno edificabile",
# "Terreno non edificabile": "Terreno Agricolo",
# "Terreno - Terreno agricolo": "Terreno Agricolo",
# "Terreno Agricolo": "Terreno Agricolo"}

synonyms_map = {
    "terrazza_text": ["terrazzo_text", "terrazzare_text", "terrazzino_text"],
    "luminoso_text": ["luminosità_text", "esposizione_text"],
    "mansarda_text": ["mansardato_text", "piano_ammezzare_text", "piano_mansardato_text", "piano_mansarda_text"],
    "balcone_text": ["balconata_text", "balconato_text", "balconati_text", "balconcino_text"],
    "nuovo_text": ["progetto_text", "costruzione_text", "consegna_text"],
    "garage_text": ["auto_text", "parcheggio_text", "posteggio_text"],
    "spazio_esterno_text": ["cortile_text" , "cortiletto_text" ],
    "panoramico_text": ["mozzafiato_text", "panorama_text", "vista_text"],
    "seminterrato_text": ["piano_seminterrato_text"],
    "mare_text": ["lungomare_text", "costa_text", "scogliera_text"],
    "primo_piano_text": ["piano_primo_text"],
    "piano_rialzato_text": ["rialzare_text", "piano_rialzare_text"],
    "etna_text": ["montagna_text"],
    "NO_text": ["fondachello_text", "galermo_text", "mercato_text", "picanello_text", "librino_text", "nesima_text", "fiumefreddo_text", "obelisco_text", "fasano_text", "castagnola_text", "lido_text", "palestro_text", "bummacaro_text", "villaggio_text", "faro_text", "augusta_text", "vaccarizzo_text"],
    "palazzo_piccolo_text": ["piccolo_palazzina_text", "piccolo_condominio_text", "piccolo_residence_text", "piccolo_contesto_text", "piccolo_palazzetto_text", "piccolo_complesso_text", "residenziale_text", "tranquillo_text", "silenzioso_text", "tranquillità_text"],
    "ritrutturato_text": ["totalmente_ristrutturare_text", "finemente_ristrutturare_text", "interamente_ristrutturare_text", "completamente_ristrutturare_text", "appena_ristrutturare_text", "parzialmente_ristrutturare_text", "ristrutturare_internamente_text", "ristrutturazione_text"]
}


# TODO refactor with f-strings and split arguments to grab from parser
immobiliare_urls = {
        'casetta': 'https://www.immobiliare.it/api-next/search-list/real-estates/?vrt=37.5149%2C15.105858%3B37.508483%2C15.101438%3B37.507615%2C15.082426%3B37.508058%2C15.075431%3B37.525043%2C15.059853%3B37.532327%2C15.059938%3B37.543216%2C15.061655%3B37.553356%2C15.059595%3B37.558187%2C15.059166%3B37.565603%2C15.05393%3B37.567168%2C15.042086%3B37.569617%2C15.034103%3B37.574923%2C15.033073%3B37.584106%2C15.03582%3B37.58669%2C15.047235%3B37.594512%2C15.046377%3B37.599952%2C15.051098%3B37.607364%2C15.042686%3B37.606752%2C15.025949%3B37.606752%2C15.014534%3B37.616951%2C15.009727%3B37.626333%2C15.013161%3B37.626672%2C15.032215%3B37.624089%2C15.0529%3B37.629392%2C15.05908%3B37.63279%2C15.066118%3B37.641966%2C15.174179%3B37.636325%2C15.192118%3B37.603488%2C15.184736%3B37.569481%2C15.181732%3B37.551859%2C15.161562%3B37.530285%2C15.128345%3B37.5149%2C15.105858&idContratto=1&idCategoria=1&prezzoMassimo=160000&superficieMinima=40&superficieMassima=80&criterio=dataModifica&ordine=desc&noAste=1&__lang=it&pag=1&paramsCount=11&path=%2Fsearch-list%2F',
        'casetta_link': 'https://www.immobiliare.it/search-list/?vrt=37.5149%2C15.105858%3B37.508483%2C15.101438%3B37.507615%2C15.082426%3B37.508058%2C15.075431%3B37.525043%2C15.059853%3B37.532327%2C15.059938%3B37.543216%2C15.061655%3B37.553356%2C15.059595%3B37.558187%2C15.059166%3B37.565603%2C15.05393%3B37.567168%2C15.042086%3B37.569617%2C15.034103%3B37.574923%2C15.033073%3B37.584106%2C15.03582%3B37.58669%2C15.047235%3B37.594512%2C15.046377%3B37.599952%2C15.051098%3B37.607364%2C15.042686%3B37.606752%2C15.025949%3B37.606752%2C15.014534%3B37.616951%2C15.009727%3B37.626333%2C15.013161%3B37.626672%2C15.032215%3B37.624089%2C15.0529%3B37.629392%2C15.05908%3B37.63279%2C15.066118%3B37.641966%2C15.174179%3B37.636325%2C15.192118%3B37.603488%2C15.184736%3B37.569481%2C15.181732%3B37.551859%2C15.161562%3B37.530285%2C15.128345%3B37.5149%2C15.105858&idContratto=1&idCategoria=1&prezzoMassimo=160000&superficieMinima=40&superficieMassima=80&criterio=dataModifica&ordine=desc&noAste=1&__lang=it&pag=1',

        'immobile_mare': 'https://www.immobiliare.it/api-next/search-list/real-estates/?vrt=37.214404,15.199156;37.221239,15.186281;37.237777,15.187054;37.241604,15.194778;37.242833,15.202246;37.247411,15.207825;37.250076,15.215635;37.247548,15.220528;37.241672,15.219755;37.240237,15.221214;37.242287,15.223703;37.244063,15.225935;37.244337,15.233488;37.240305,15.239925;37.237367,15.243273;37.237845,15.24765;37.240237,15.24662;37.242355,15.248766;37.245157,15.244904;37.248573,15.241642;37.259094,15.238209;37.279107,15.208855;37.287097,15.204306;37.289419,15.201645;37.281019,15.19598;37.278697,15.190487;37.278151,15.183363;37.288394,15.173664;37.288189,15.166969;37.292287,15.147829;37.301846,15.13298;37.309082,15.106115;37.312291,15.091438;37.332904,15.083284;37.334269,15.09264;37.352897,15.088348;37.397164,15.086975;37.408483,15.088863;37.415914,15.088348;37.415709,15.092039;37.455578,15.087748;37.478877,15.087318;37.491136,15.087404;37.496789,15.089636;37.500942,15.08852;37.5021,15.091438;37.502713,15.093842;37.509522,15.099678;37.521299,15.108776;37.523274,15.11384;37.526065,15.115213;37.52974,15.110836;37.532531,15.108519;37.534505,15.113583;37.534777,15.121136;37.536955,15.126801;37.539881,15.13092;37.543829,15.139589;37.551586,15.145254;37.55424,15.146799;37.557302,15.148859;37.55982,15.153751;37.560976,15.160275;37.561044,15.161047;37.564055,15.161862;37.567814,15.16418;37.570263,15.164909;37.574073,15.167785;37.575552,15.169458;37.576505,15.170767;37.576198,15.172935;37.576692,15.176024;37.580977,15.176625;37.586095,15.17581;37.593322,15.173149;37.598694,15.172334;37.605494,15.172248;37.61209,15.172248;37.614401,15.172977;37.617053,15.172205;37.618855,15.172935;37.619398,15.174737;37.620894,15.174737;37.626027,15.175724;37.632824,15.174222;37.635713,15.175853;37.636801,15.176389;37.637378,15.176904;37.637973,15.177763;37.638092,15.1789;37.638789,15.180852;37.639621,15.181775;37.639893,15.182719;37.640352,15.183942;37.643937,15.187483;37.647199,15.190229;37.648711,15.192719;37.648558,15.19347;37.649204,15.193748;37.650274,15.193985;37.651175,15.194736;37.652075,15.195272;37.653893,15.197868;37.655558,15.198812;37.657155,15.199113;37.659261,15.197482;37.660212,15.196581;37.660518,15.195744;37.661384,15.195851;37.662709,15.195444;37.663915,15.195723;37.675737,15.197697;37.683073,15.202074;37.684568,15.205851;37.704671,15.217867;37.70518,15.216107;37.707251,15.216279;37.709254,15.217524;37.711189,15.218382;37.713905,15.217867;37.718251,15.215292;37.726873,15.208983;37.729011,15.206966;37.731455,15.205035;37.734204,15.203962;37.737293,15.203404;37.740008,15.204391;37.742146,15.224948;37.604712,15.293312;37.4784,15.109634;37.404528,15.107574;37.313656,15.148773;37.298364,15.172806;37.297817,15.220184;37.255473,15.282326;37.212011,15.284042;37.193416,15.210228;37.214404,15.199156&idContratto=1&idCategoria=1&criterio=dataModifica&ordine=asc&noAste=1&__lang=it&pag=1&paramsCount=7&path=/search-list/',
        'immobile_mare_link': 'https://www.immobiliare.it/search-list/?vrt=37.214404%2C15.199156%3B37.221239%2C15.186281%3B37.237777%2C15.187054%3B37.241604%2C15.194778%3B37.242833%2C15.202246%3B37.247411%2C15.207825%3B37.250076%2C15.215635%3B37.247548%2C15.220528%3B37.241672%2C15.219755%3B37.240237%2C15.221214%3B37.242287%2C15.223703%3B37.244063%2C15.225935%3B37.244337%2C15.233488%3B37.240305%2C15.239925%3B37.237367%2C15.243273%3B37.237845%2C15.24765%3B37.240237%2C15.24662%3B37.242355%2C15.248766%3B37.245157%2C15.244904%3B37.248573%2C15.241642%3B37.259094%2C15.238209%3B37.279107%2C15.208855%3B37.287097%2C15.204306%3B37.289419%2C15.201645%3B37.281019%2C15.19598%3B37.278697%2C15.190487%3B37.278151%2C15.183363%3B37.288394%2C15.173664%3B37.288189%2C15.166969%3B37.292287%2C15.147829%3B37.301846%2C15.13298%3B37.309082%2C15.106115%3B37.312291%2C15.091438%3B37.332904%2C15.083284%3B37.334269%2C15.09264%3B37.352897%2C15.088348%3B37.397164%2C15.086975%3B37.408483%2C15.088863%3B37.415914%2C15.088348%3B37.415709%2C15.092039%3B37.455578%2C15.087748%3B37.478877%2C15.087318%3B37.491136%2C15.087404%3B37.496789%2C15.089636%3B37.500942%2C15.08852%3B37.5021%2C15.091438%3B37.502713%2C15.093842%3B37.509522%2C15.099678%3B37.521299%2C15.108776%3B37.523274%2C15.11384%3B37.526065%2C15.115213%3B37.52974%2C15.110836%3B37.532531%2C15.108519%3B37.534505%2C15.113583%3B37.534777%2C15.121136%3B37.536955%2C15.126801%3B37.539881%2C15.13092%3B37.543829%2C15.139589%3B37.551586%2C15.145254%3B37.55424%2C15.146799%3B37.557302%2C15.148859%3B37.55982%2C15.153751%3B37.560976%2C15.160275%3B37.561044%2C15.161047%3B37.564055%2C15.161862%3B37.567814%2C15.16418%3B37.570263%2C15.164909%3B37.574073%2C15.167785%3B37.575552%2C15.169458%3B37.576505%2C15.170767%3B37.576198%2C15.172935%3B37.576692%2C15.176024%3B37.580977%2C15.176625%3B37.586095%2C15.17581%3B37.593322%2C15.173149%3B37.598694%2C15.172334%3B37.605494%2C15.172248%3B37.61209%2C15.172248%3B37.614401%2C15.172977%3B37.617053%2C15.172205%3B37.618855%2C15.172935%3B37.619398%2C15.174737%3B37.620894%2C15.174737%3B37.626027%2C15.175724%3B37.632824%2C15.174222%3B37.635713%2C15.175853%3B37.636801%2C15.176389%3B37.637378%2C15.176904%3B37.637973%2C15.177763%3B37.638092%2C15.1789%3B37.638789%2C15.180852%3B37.639621%2C15.181775%3B37.639893%2C15.182719%3B37.640352%2C15.183942%3B37.643937%2C15.187483%3B37.647199%2C15.190229%3B37.648711%2C15.192719%3B37.648558%2C15.19347%3B37.649204%2C15.193748%3B37.650274%2C15.193985%3B37.651175%2C15.194736%3B37.652075%2C15.195272%3B37.653893%2C15.197868%3B37.655558%2C15.198812%3B37.657155%2C15.199113%3B37.659261%2C15.197482%3B37.660212%2C15.196581%3B37.660518%2C15.195744%3B37.661384%2C15.195851%3B37.662709%2C15.195444%3B37.663915%2C15.195723%3B37.675737%2C15.197697%3B37.683073%2C15.202074%3B37.684568%2C15.205851%3B37.704671%2C15.217867%3B37.70518%2C15.216107%3B37.707251%2C15.216279%3B37.709254%2C15.217524%3B37.711189%2C15.218382%3B37.713905%2C15.217867%3B37.718251%2C15.215292%3B37.726873%2C15.208983%3B37.729011%2C15.206966%3B37.731455%2C15.205035%3B37.734204%2C15.203962%3B37.737293%2C15.203404%3B37.740008%2C15.204391%3B37.742146%2C15.224948%3B37.604712%2C15.293312%3B37.4784%2C15.109634%3B37.404528%2C15.107574%3B37.313656%2C15.148773%3B37.298364%2C15.172806%3B37.297817%2C15.220184%3B37.255473%2C15.282326%3B37.212011%2C15.284042%3B37.193416%2C15.210228%3B37.214404%2C15.199156&idContratto=1&idCategoria=1&criterio=dataModifica&ordine=asc&noAste=1&__lang=it&pag=1',

        'small': 'https://www.immobiliare.it/api-next/search-list/real-estates/?raggio=800&centro=37.570864,15.068922&idContratto=1&idCategoria=1&prezzoMassimo=300000&criterio=dataModifica&ordine=desc&noAste=1&__lang=it&pag=1&paramsCount=10&path=/search-list/',

}