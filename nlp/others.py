import pandas as pd
from nlp.text_preprocess import preprocess as process_description
from utils.custom_utils import synonyms_map, swap_dict

def get_n_grams(series, n_terms=1, min_frequency=5, placeholder=None,
            relevant_prefix=None):
    """
    Extracts n-grams from the corpus.

    The output is a dict of n-grams, where each dict item key
    is the n-gram and the value its the frequency, sorted by frequency.

    :param corpus: the text to extract terms from
    :type corpus: list[str]
    :param n_terms: maximum length of an n-gram in number of words
    :type n_terms: int
    :param min_frequency: min. number of occurrences. n-grams with less than
        this frequency are discarded
    :type min_frequency: int
    :param placeholder: placeholder for the stop-words. No n-gram with this
        placeholder is returned
    :type placeholder: str or None
    :param relevant_prefix: prefix used to mark the relevant terms. No n-gram
        containing a word with this prefix is returned
    :type relevant_prefix: str or None
    :return: the n-grams as a dict with the n-gram itself as the key and its
        frequency as the value
    :rtype: dict[str, int]
    """
    if relevant_prefix is None:
        # no prefix, use something that startswith can't find
        relevant_prefix = ' '

    ser = pd.Series(dtype=object)
    for idx, txt in series.iteritems():
        res = []
        for n in range(1, n_terms+1):
            doc_list = txt.split()  # default separator is the whitespace char
            doc_list = [d.lower() for d in doc_list]
            for i in range(len(doc_list) - n + 1):
                words = doc_list[i:i+n]
                # skip the terms that contain a placeholder or a relevant term
                if any(word == placeholder for word in words):
                    continue
                res.append('_'.join(words))
        ser.at[idx] = ' '.join(res)

    return ser


def handle_text_descriptions(df, title_column_name, column_name, logger):
    df = df.assign(title_desc = df[[title_column_name, column_name]].apply(lambda x : '{} {}'.format(x[0],x[1]), axis=1))
    lem_col = f"{column_name}_lem"
    desc = process_description(df, "title_desc", lem_col, logger, 'it')

    n_grams = get_n_grams(desc[lem_col], n_terms=2,
                                min_frequency=1, placeholder='@')
    desc = desc.assign(n_grams = n_grams)

    rel = pd.read_csv('nlp/words.csv')
    rel = rel[rel['label']=='relevant']['term']
    rilevanti = set(['_'.join(r.split()) for r in rel.to_list()])
    for idx, row in desc[~desc['n_grams'].isna()].iterrows():
        text = set(row['n_grams'].split())
        relevantsFound = text.intersection(rilevanti)
        if len(relevantsFound)<1:
            df.at[idx, 'relevants'] = ''
        else:
            df.at[idx, 'relevants'] = ' '.join(relevantsFound).strip()

    df['relevants'] = df['relevants'].fillna('')
    everyPossibleFeature = set([r.replace(' ', '_')+'_text' for r in rel])
    for f in everyPossibleFeature:
        # df[f] = False
        df = df.assign(**{f: False})
    for idx, riga in df.loc[:, ['relevants']].iterrows():
        fs = riga['relevants'].split()
        for f in fs:
            df.at[idx, f"{f.replace(' ', '_')}_text"] = True

    for k, v in synonyms_map.items():
        # Sometimesthe key is is not also part of the values. Like in "NO_text"
        df[k] = df.loc[:, [c for c in v+[k] if c in df.columns]].any(axis=1)
    df.drop(swap_dict(synonyms_map).keys(), axis=1, inplace=True)
    textFeatCol = [col for col in df.columns if col.endswith('_text')]
    # df.drop(['description', 'description_lem', 'relevants', 'title_desc'], axis=1, inplace=True)
    df.drop(['description', 'description_lem', 'title_desc'], axis=1, inplace=True)

    return df, textFeatCol