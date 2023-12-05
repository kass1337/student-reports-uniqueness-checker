from datasketch import MinHash, MinHashLSH
from db import Db
from raw_parser import raw_parser
from error_codes import error_codes
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.util import ngrams
nltk.download('averaged_perceptron_tagger_ru', quiet=True)
nltk.download('stopwords', quiet=True)


class Analyzer(object):

    _unique_reports = None
    _db = None
    _raw_reports_to_compare = list()
    _raw_report_to_analyze = None
    _tokenized_reports_to_compare = None
    _tokenized_report_to_analyze = None
    _cleaned_reports_to_analyze = None
    _cleaned_report_to_check = None
    _ignore_headings = []  # TODO PARSE CONFIG
    _ignore_stopwords = []

    _minhash_to_compare = None
    _minhash_to_analyze = None

    def __init__(self, file_name_to_ignore_stopwords, file_name_to_ignore_headings):
        self._db = Db()
        self._fill_custom(file_name_to_ignore_stopwords, file_name_to_ignore_headings)

    def _fill_custom(self, file_name_to_ignore_stopwords, file_name_to_ignore_headings):
        try:
            with open(file_name_to_ignore_stopwords, 'r', encoding='utf-8') as stopwords_file, open(file_name_to_ignore_headings, 'r', encoding='utf-8') as headings_file:
                stopwords = stopwords_file.read()
                headings = headings_file.read()
                self._ignore_headings = headings.split(sep=',')
                self._ignore_stopwords = stopwords.split(sep=',')
        except FileNotFoundError:
            exit(error_codes.NO_CUSTOM_FILES.value)


    def _get_unique_reports(self, word_score, par_score):
        word_reports = self._db.select_closest_word(
            word_score)  # выбор по метрике по количеству слов
        # выбор по метрике по количеству параграфов
        par_reports = self._db.select_closest_par(par_score)
        merged = word_reports + par_reports
        unique_dict = {}
        for item in merged:
            key = item[0]
            if key not in unique_dict:
                unique_dict[key] = item
        unique_dict = list(unique_dict.values())
        self._unique_reports = unique_dict

    def _pars_reports(self, file_path):
        pars = raw_parser()
        for i, report in enumerate(self._unique_reports):
            self._raw_reports_to_compare.insert(
                i, pars.raw_parse(report[2])[1])
        self._raw_report_to_analyze = pars.raw_parse(file_path)[1]

    def _tokenize(self):
        self._tokenized_reports_to_compare = []
        for i, content in enumerate(self._raw_reports_to_compare):
            self._tokenized_reports_to_compare.insert(i, {})
            for key in content:
                if content[key] and key not in self._ignore_headings:
                    self._tokenized_reports_to_compare[i][key] = word_tokenize(
                        content[key])
                    self._tokenized_reports_to_compare[i][key] = [word.lower(
                    ) for word in self._tokenized_reports_to_compare[i][key] if word.lower() not in stopwords.words('russian') + self._ignore_stopwords]
        self._tokenized_report_to_analyze = {}
        for key in self._raw_report_to_analyze:
            if self._raw_report_to_analyze[key] and key not in self._ignore_headings:
                self._tokenized_report_to_analyze[key] = word_tokenize(
                    self._raw_report_to_analyze[key])
                self._tokenized_report_to_analyze[key] = [word.lower(
                ) for word in self._tokenized_report_to_analyze[key] if word.lower() not in stopwords.words('russian') + self._ignore_stopwords] 

    def _minhash(self):
        self._minhash_to_compare = []
        for i, content in enumerate(self._cleaned_reports_to_analyze):
            content = [tuple(map(lambda x: x.encode('utf-8'), tup))
                       for tup in content]
            m = MinHash(num_perm=128)
            for word in content:
                m.update(str(word).encode('utf-8'))
            self._minhash_to_compare.insert(i, list(m.digest()))
        m = MinHash(num_perm=128)
        self._cleaned_report_to_check = [tuple(
            map(lambda x: x.encode('utf-8'), tup)) for tup in self._cleaned_report_to_check]
        for key in self._cleaned_report_to_check:
            m.update(str(key).encode('utf-8'))
        self._minhash_to_analyze = (list(m.digest()))

    def _ngram(self):
        n = 3
        self._cleaned_reports_to_analyze = []
        output = []
        for i, content in enumerate(self._tokenized_reports_to_compare):
            self._cleaned_reports_to_analyze.insert(i, [])
            for key in content:
                if key not in self._ignore_headings:
                    output += list(ngrams(content[key], n))
            if output:
                self._cleaned_reports_to_analyze[i] = [tuple([ngram[i] for i in range(len(
                    ngram))]) for ngram in output]
            output = []
        for key in self._tokenized_report_to_analyze:
            output += list(ngrams(self._tokenized_report_to_analyze[key], n))
        if output:
            self._cleaned_report_to_check = [tuple([ngram[i] for i in range(len(
                ngram))]) for ngram in output]

    def _eval(self):
        hash_to_analyze = MinHash(hashvalues=self._minhash_to_analyze)
        for i, report in enumerate(self._minhash_to_compare):
            hash_to_compare = MinHash(hashvalues=report)
            print("MINHASH NGRAM {} TO {}".format(hash_to_compare.jaccard(hash_to_analyze), self._unique_reports[i][2]))

    def analyze(self, word_score, par_score, file_path):
        self._get_unique_reports(word_score, par_score)
        self._pars_reports(file_path)
        self._tokenize()
        self._ngram()
        self._minhash()
        self._eval()
