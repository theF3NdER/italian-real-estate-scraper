import abc
import re
import sys
from itertools import repeat
from multiprocessing import Pool
from timeit import default_timer as timer
from typing import Generator, Tuple, Sequence

import nltk
import pandas as pd

from nltk.stem.wordnet import WordNetLemmatizer
from psutil import cpu_count

from slrkit_utils.argument_parser import (AppendMultipleFilesAction,
                                          AppendMultiplePairsAction,
                                          ArgParse)
STOPWORD_PLACEHOLDER = '@'
RELEVANT_PREFIX = STOPWORD_PLACEHOLDER
PHYSICAL_CPUS = cpu_count(logical=False)


class Lemmatizer(abc.ABC):
    @abc.abstractmethod
    def lemmatize(self, text: Sequence[str]) -> Generator[Tuple[str, str], None, None]:
        pass


class EnglishLemmatizer(Lemmatizer):
    def __init__(self):
        self._lem = WordNetLemmatizer()

    def lemmatize(self, text: Sequence[str]) -> Generator[Tuple[str, str], None, None]:
        for word in text:
            yield (word, self._lem.lemmatize(word))


class ItalianLemmatizer(Lemmatizer):
    def __init__(self, treetagger_dir=None):
        import warnings
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=FutureWarning)
                import treetaggerwrapper as ttagger
        except ModuleNotFoundError:
            sys.exit('Module treetaggerwrapper not installed - It is required '
                     'by the italian lemmatizer')

        try:
            self._ttagger = ttagger.TreeTagger(TAGLANG='it',
                                               TAGDIR=treetagger_dir)
        except ttagger.TreeTaggerError as e:
            msg: str = e.args[0]
            if msg.startswith("Can't locate"):
                sys.exit('TreeTagger not installed - It is required by the '
                         'italian lemmatizer')
            elif (msg.startswith('Bad TreeTagger')
                  or msg.startswith('TreeTagger binary')):
                sys.exit('TreeTagger not properly installed - It is required by the '
                         'italian lemmatizer')
            elif msg.startswith('TreeTagger parameter file'):
                sys.exit('TreeTagger italian parameter file not properly '
                         'installed - It is required by the italian lemmatizer')
            else:
                raise

    def lemmatize(self, text: Sequence[str]) -> Generator[Tuple[str, str], None, None]:
        tags = self._ttagger.tag_text(' '.join(text))
        for t in tags:
            sp = t.split('\t')
            if sp[0].lower() in ['sai'] and sp[2] != 'sapere':
                yield (sp[0], 'sapere')
            elif sp[2] == 'essere|stare':
                yield (sp[0], 'stare')
            else:
                yield (sp[0], sp[2])


AVAILABLE_LEMMATIZERS = {
    'en': EnglishLemmatizer,
    'it': ItalianLemmatizer,
}


def get_lemmatizer(lang='en'):
    try:
        return AVAILABLE_LEMMATIZERS[lang]()
    except KeyError:
        pass

    raise ValueError(f'language {lang!r} not available')


def to_record(config):
    """
    Returns the list of files to record with git
    :param config: content of the script config file
    :type config: dict[str, Any]
    :return: the list of files
    :rtype: list[str]
    :raise ValueError: if the config file does not contains the right values
    """
    if not isinstance(config['stop-words'], list):
        raise ValueError('stop-words is not a list')
    files = list(config['stop-words'])
    if not isinstance(config['relevant-term'], list):
        raise ValueError('relevant-term is not a list')
    for r in config['relevant-term']:
        if not isinstance(r, list):
            raise ValueError('some elements in relevant-term are not lists')
        if len(r) < 1:
            continue
        files.append(r[0])

    return files


def to_ignore(config):
    """
    Returns the list of files to ignore with git
    :param config: content of the script config file
    :type config: dict[str, Any]
    :return: the list of files
    :rtype: list[str]
    :raise ValueError: if the config file does not contains the right values
    """
    file = config['output']
    if file is None or file == '':
        raise ValueError("'output' is not specified")
    if file == '-':
        return []

    return [str(file)]


def init_argparser():
    """Initialize the command line parser."""
    parser = ArgParse()
    parser.add_argument('datafile', action='store', type=str,
                        help='input CSV data file', input=True)
    parser.add_argument('--output', '-o', metavar='FILENAME',
                        default='-',
                        help='output file name. If omitted or %(default)r '
                             'stdout is used',
                        suggest_suffix='_preproc.csv', output=True)
    parser.add_argument('--placeholder', '-p',
                        default=STOPWORD_PLACEHOLDER,
                        help='Placeholder for stopwords. Also used as a '
                             'prefix for the relevant words. '
                             'Default: %(default)r')
    parser.add_argument('--stop-words', '-s',
                        action=AppendMultipleFilesAction, nargs='+',
                        metavar='FILENAME', dest='stopwords_file',
                        help='stop words file name')
    parser.add_argument('--relevant-term', '-r', nargs='+',
                        metavar=('FILENAME', 'PLACEHOLDER'),
                        dest='relevant_terms_file',
                        action=AppendMultiplePairsAction, unique_first=True,
                        help='relevant terms file name and the placeholder to '
                             'use with those terms. The placeholder must not '
                             'contains any space. The placeholder is optional. '
                             'If it is omitted, each relevant term from this '
                             'file, is replaced with the stopword placeholder, '
                             'followed by the term itself with each space '
                             'changed with the "_" character and then another '
                             'stopword placeholder.')
    parser.add_argument('--acronyms', '-a',
                        help='TSV files with the approved acronyms')
    parser.add_argument('--target-column', '-t', action='store', type=str,
                        default='abstract', dest='target_column',
                        help='Column in datafile to process. '
                             'If omitted %(default)r is used.')
    parser.add_argument('--output-column', action='store', type=str,
                        default='abstract_lem', dest='output_column',
                        help='name of the column to save. '
                             'If omitted %(default)r is used.')
    parser.add_argument('--input-delimiter', action='store', type=str,
                        default='\t', dest='input_delimiter',
                        help='Delimiter used in datafile. '
                             'Default %(default)r')
    parser.add_argument('--output-delimiter', action='store', type=str,
                        default='\t', dest='output_delimiter',
                        help='Delimiter used in output file. '
                             'Default %(default)r')
    parser.add_argument('--rows', '-R', type=int, dest='input_rows',
                        help="Select maximum number of samples")
    parser.add_argument('--language', '-l', default='en',
                        help='language of text. Must be a ISO 639-1 two-letter '
                             'code. Default: %(default)r')
    parser.add_argument('--logfile', default='slr-kit.log',
                        help='log file name. If omitted %(default)r is used',
                        logfile=True)
    parser.add_argument('--regex', help='Regex .csv for specific substitutions')
    return parser


def load_stopwords(input_file):
    """
    Loads a list of stopwords from a file

    This functions skips all the lines that starts with a '#'.

    :param input_file: file to read
    :type input_file: str
    :return: the loaded words as a set of string
    :rtype: set[str]
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            stop_words_list = f.read().splitlines()
    except FileNotFoundError as err:
        msg = 'Error: file {!r} not found'
        sys.exit(msg.format(err.filename))

    stop_words_list = {w for w in stop_words_list if w != '' and w[0] != '#'}
    # Creating a list of custom stopwords
    return stop_words_list


def replace_ngram(text, n_grams):
    """
    Replace the given n-grams with a placeholder in the specified text

    The n-grams and their placeholder are taken from the generator n_grams, that
    must be a generator that yields a tuple (placeholder, n-gram). Each n-gram
    must be a tuple of strings.

    :param text: the text to search
    :type text: list[str]
    :param n_grams: generator that yields n-grams and their placeholder
    :type n_grams: Generator[tuple[str, tuple[str]], Any, None]
    :return: the transformed text
    :rtype: list[str]
    """
    text2 = list(text)
    for placeholder, ngram in n_grams:
        end = False
        index = -1
        length = len(ngram)
        while not end:
            try:
                # index + 1 to skip the previous match
                index = text2.index(ngram[0], index + 1)
                if tuple(text2[index:index + length]) == ngram:
                    # found!
                    text2[index:index + length] = [placeholder]
            except ValueError:
                end = True

    return text2


def language_specific_regex(text, lang='it'):
    """
    Applies some regex specific for a language

    This function marks everything that is a barrier with '---'. This is done
    because the regex may delete all special character included the ones in the
    barrier placeholder, but the '-' is always preserved.
    Remember to change the '---' with the barrier.
    :param text: text to elaborate
    :type text: str
    :param lang: code of the language (e.g. 'en' for english)
    :type lang: str
    :return: the elaborated text
    :rtype: str
    """
    # The first step in every language is to change punctuations to the stop-word
    # placeholder. The stop-word placeholder can be anything, so we have to change
    # the punctuation with something that will survive the special char removal.
    # '---' it's ok because hyphens are preserved in every language.
    if lang == 'en':
        # punctuation
        # remove commas
        out_text = re.sub(',', ' ', text)
        # other punctuation is considered as a barrier
        out_text = re.sub('[.;:!?()"\']', ' --- ', out_text)
        # Remove special characters (not the hyphen) and digits
        # also preserve the '__' used by some placeholders
        return re.sub(r'(\d|[^-\w])+|(?<=[^_])_(?=[^_])', ' ', out_text)
    if lang == 'it':
        # punctuation
        # remove commas
        try:
            out_text = re.sub(',', ' ', text)
        except Exception as e:
            print(e)
        # preserve "'" but other punctuation is considered as a barrier
        out_text = re.sub('[,.;:!?()"]', ' --- ', out_text)
        # Remove special characters (not the hyphen) and digits. but preserve
        # accented letters. Also preserve "'" if surrounded by non blank chars
        # and the '__' used by some placeholders
        return re.sub(r'(\d|[^-\wàèéìòù_\']'
                      r'|(?<=\s)\'(?=\S)|(?<=\S)\'(?!\S))+'
                      r'|(?<=[^_])_(?=[^_])',
                      ' ', out_text)


def regex(text, stopword_placeholder=STOPWORD_PLACEHOLDER, lang='it',
          regex_df=None):
    """
    Applies some regex to a text

    This function applies the regex defined in the regex_df.
    It also applies the language specific regex and some standard regex and it
    changes the '---' with the barrier.
    :param text: text to elaborate
    :type text: str
    :param stopword_placeholder: string used as placeholder for the stopwords
        and the barriers
    :type stopword_placeholder: str
    :param lang: code of the language (e.g. 'en' for english)
    :type lang: str
    :param regex_df: dataframe with the regex to apply
    :type regex_df: pd.DataFrame
    :return: the elaborated text
    :rtype: str
    """
    # If a regex DataFrame for the specific project is passed,
    # this function will replace the patterns with the corresponding repl
    # parameter
    if regex_df is not None:
        # Some of the regex are not actually regex. Like <br>
        not_regex = regex_df[~regex_df['regexBoolean']]
        for _, row in not_regex.iterrows():
            text = text.replace(row['pattern'], '__{}__'.format(row['repl']))

        regex_df = regex_df[~regex_df['pattern'].isin(not_regex['pattern'])]
        regex_with_spaces = regex_df[regex_df['pattern'].str.contains(r'\s',
                                                                      regex=False)]

        for _, row in regex_with_spaces.iterrows():
            text = re.sub(row['pattern'], '__{}__'.format(row['repl']), text,
                          flags=re.IGNORECASE)

        rows = regex_df[~regex_df['pattern'].isin(regex_with_spaces['pattern'])]
        for _, row in rows.iterrows():
            text = ' '.join([re.sub(row['pattern'],
                                    '__{}__'.format(row['repl']), gram,
                                    flags=re.IGNORECASE)
                             for gram in text.split()])
    # Change punctuation and remove special characters (not the hyphen) and
    # digits. The definition of special character and punctuation, changes with
    # the language
    text = language_specific_regex(text, lang)
    # now we can search for ' --- ' and place the stop-word placeholder
    # the positive look-ahead and look-behind are to preserve the spaces
    text = re.sub(r'---', stopword_placeholder, text)
    # remove any run of hyphens not surrounded by non space
    text = re.sub(r'(\s+-+\s+|(?<=\S)-+\s+|\s+-+(?=\S))|(-{2,})', ' ', text)

    return text


def relevant_generator(relevant, relevant_prefix):
    for rel_set, placeholder in relevant:
        ph = f'{relevant_prefix}{placeholder}{relevant_prefix}'
        for rel in rel_set:
            if placeholder is not None:
                yield ph, rel
            else:
                yield f'{relevant_prefix}{"_".join(rel)}{relevant_prefix}', rel


def preprocess_item(item, relevant_terms, stopwords, language='en',
                    placeholder=STOPWORD_PLACEHOLDER,
                    relevant_prefix=RELEVANT_PREFIX, regex_df=None):
    """
    Preprocess the text of a document.

    It lemmatizes the text. Then it searches for the relevant terms. The
    relevant_terms argument is a list of tuples. Each tuple contains a set of
    relevant terms to search for, and a placeholder. If the placeholder is None,
    each relevant term found is replaced with a string composed with the
    relevant_prefix, then all the words composing the term separated
    with '_' and finally the relevant_prefix. If the placeholder is not None,
    then each term associated with that prefix is replaced with a string
    composed by the relevant_prefix, the placeholder and then the
    relevant_prefix.
    The function then searches for the acronyms, changing the words composing
    them with the corresponding abbreviation.
    It also filters the stop-words changing them with the stopword_placeholder
    string as placeholder.

    :param item: the text to process
    :type item: str
    :param relevant_terms: the relevant words to search. Each n-gram must be a
        tuple of strings
    :type relevant_terms: list[tuple[set[tuple[str]], str or None]]
    :param stopwords: the stop-words to filter
    :type stopwords: set[str]
    :param acronyms: the acronyms to replace in each document. Must have two
        columns 'term' and 'label'. See the acronyms_generato documentation for
        info about the format.
    :type acronyms: pd.DataFrame
    :param language: code of the language to be used to lemmatize text
    :type language: str
    :param placeholder: placeholder for the stop-words
    :type placeholder: str
    :param relevant_prefix: prefix string used when replacing the relevant terms
    :type relevant_prefix: str
    :param regex_df: dataframe with the regex to apply
    :type regex_df: pd.DataFrame
    :return: the processed text
    :rtype: list[str]
    """
    lem = get_lemmatizer(language)
    # replace acronym abbreviation - it's done here because we need to search
    # the abbreviation in case sensitive mode. To mark the barrier, we use '---'
    # as placeholder because is preserved and substituted with the proper string
    # by the regex function
    text = item

    # apply some regex to clean the text
    text = regex(text, placeholder, language, regex_df=regex_df)
    text = text.split(' ')

    text2 = [lem_word for _, lem_word in lem.lemmatize(text)]

    # mark relevant terms
    text2 = replace_ngram(text2,
                          relevant_generator(relevant_terms, relevant_prefix))

    if len(stopwords) != 0:
        for i, word in enumerate(text2):
            if word in stopwords:
                text2[i] = placeholder

    text2 = ' '.join(text2)
    return text2


def process_corpus(dataset, relevant_terms, stopwords, language='en',
                   placeholder=STOPWORD_PLACEHOLDER,
                   relevant_prefix=RELEVANT_PREFIX, regex_df=None):
    """
    Process a corpus of documents.

    Each documents is processed using the preprocess_item function

    :param dataset: the corpus of documents
    :type dataset: pd.Sequence
    :param relevant_terms: the related terms to search in each document
    :type relevant_terms: list[tuple[set[tuple[str]], str]]
    :param stopwords: the stop-words to filter in each document
    :type stopwords: set[str]
    :param acronyms: the acronyms to replace in each document. Must have two
        columns 'term' and 'label'. See the acronyms_generato documentation for
        info about the format.
    :type acronyms: pd.Dataframe
    :param language: code of the language to be used to lemmatize text
    :type language: str
    :param placeholder: placeholder for the stop-words
    :type placeholder: str
    :param relevant_prefix: prefix used to replace the relevant terms
    :type relevant_prefix: str
    :param regex_df: dataframe with the regex to apply
    :type regex_df: pd.DataFrame or None
    :return: the corpus processed
    :rtype: list[str]
    """
    with Pool(processes=PHYSICAL_CPUS) as pool:
        # preprocess_item(dataset, relevant_terms, stopwords, language)
        corpus = pool.starmap(preprocess_item, zip(dataset,
                                                repeat(relevant_terms),
                                                repeat(stopwords),
                                                repeat(language),
                                                repeat(placeholder),
                                                repeat(relevant_prefix),
                                                repeat(regex_df)))
    return corpus


def load_relevant_terms(input_file):
    """
    Loads a list of relevant terms from a file

    This functions skips all the lines that starts with a '#'.
    Each term is split in a tuple of strings

    :param input_file: file to read
    :type input_file: str
    :return: the loaded terms as a set of tuples of strings
    :rtype: set[tuple[str]]
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            rel_words_list = f.read().splitlines()
    except FileNotFoundError as err:
        msg = 'Error: file {!r} not found'
        sys.exit(msg.format(err.filename))

    rel_words_list = {tuple(w.split(' '))
                      for w in rel_words_list
                      if w != '' and w[0] != '#'}

    return rel_words_list


def preprocess(dataset, target_column, output_column, debug_logger, language,
                relevant_terms_file=None, stopwords_file=None, regex=None, placeholder='@'):
    # download wordnet
    try:
        nltk.download('wordnet', quiet=True, raise_on_error=True)
    except ValueError as e:
        msg = 'Download of nltk wordnet failed: nltk reported: {}'
        sys.exit(msg.format(e.args[0]))

    if language not in AVAILABLE_LEMMATIZERS:
        print(f'Language {language!r} is not available', file=sys.stderr)
        sys.exit(1)
    else:
        # try to instantiate the lemmatizer to detect import/install errors
        # before starting the multiprocess machinery
        get_lemmatizer(language)


    dataset.fillna('', inplace=True)
    # filter the paper using the information from the filter_paper script
    try:
        dataset = dataset[dataset['status'] == 'good'].copy()
    except KeyError:
        # no column 'status', so no filtering
        pass
    else:
        dataset.drop(columns='status', inplace=True)
        dataset.reset_index(drop=True, inplace=True)

    debug_logger.debug('Dataset loaded {} items'.format(len(dataset[target_column])))

    # csvFileName da CLI
    if regex is not None:
        try:
            regex_df = pd.read_csv(regex, sep=',', quotechar='"')
        except FileNotFoundError as err:
            msg = 'Error: file {!r} not found'
            sys.exit(msg.format(err.filename))

        regex_df['repl'].fillna('', inplace=True)
    else:
        regex_df = None

    placeholder = placeholder
    relevant_prefix = placeholder

    stopwords = set()
    if stopwords_file is not None:
        for sfile in stopwords_file:
            stopwords |= load_stopwords(sfile)

        debug_logger.debug('Stop-words loaded and updated')

    # :type relevant_terms: list[tuple[set[tuple[str]], str or None]]

    # TODO here, rivedere come lo gestiva guido. Lui passava 2 cose dal parser noi solo il file
    rel_terms = []
    if relevant_terms_file is not None:
        rels = relevant_terms_file[relevant_terms_file['label']=='relevant']['term']
        rel_terms = list(set(rels.values))

        debug_logger.debug('Relevant words loaded and updated')

    corpus = process_corpus(dataset[target_column], rel_terms, stopwords,
                            language=language, placeholder=placeholder,
                            relevant_prefix=relevant_prefix, regex_df=regex_df)
    debug_logger.debug('Corpus processed')
    dataset[output_column] = corpus

    return dataset


def main():
    parser = init_argparser()
    args = parser.parse_args()
    return preprocess(args)


if __name__ == '__main__':
    main()
