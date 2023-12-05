from error_codes import error_codes
from normalyzer import Normalyzer
from db import Db
from analyzer import Analyzer
from raw_parser import raw_parser
import nltk
from nltk.tokenize import word_tokenize

nltk.download('averaged_perceptron_tagger_ru', quiet=True)



class Parser(object):
    doc = None
    _content = {}
    _heading_content = {}
    _par_score_dict = {}
    _word_score_dict = {}
    _db = None
    _raw_parser = None
    _word_score_value = None
    _par_score_value = None

    def __init__(self):
        self._db = Db()
        self._raw_parser = raw_parser()

    def parse(self, file_name_to_analyze, subject_id):
        self._content, self._heading_content = self._raw_parser.raw_parse(
            file_name_to_analyze)
        self._normalizeScores(0)
        #self._db.insert_all(subject_id, file_name_to_analyze, self._par_score_value, self._word_score_value, self._heading_content)

    def parse_and_analyze(self, file_name_to_analyze, subject_id, file_name_to_stopwords, file_name_to_ignore_stopwords):
        self._content, self._heading_content = self._raw_parser.raw_parse(
            file_name_to_analyze)
        self._normalizeScores(0)
        analyzer = Analyzer(file_name_to_stopwords, file_name_to_ignore_stopwords)
        analyzer.analyze(self._word_score_value, self._par_score_value , file_name_to_analyze)
        #self._db.insert_all(subject_id, file_name_to_analyze, self._par_score_value, self._word_score_value, self._heading_content)

    def _prepare_for_scores(self):
        for key in self._content:
            self._par_score_dict[key] = len(self._content[key])
        for key in self._heading_content:
            self._word_score_dict[key] = len(
                word_tokenize(self._heading_content[key]))

    def _normalizeScores(self, smallIsBetter=0):
        self._prepare_for_scores()
        normalyzer = Normalyzer()
        self._par_score_dict = normalyzer.normalazye(
            self._par_score_dict, smallIsBetter)
        self._word_score_dict = normalyzer.normalazye(
            self._word_score_dict, smallIsBetter)
        self._word_score_value = sum(self._word_score_dict.values()) / len(self._word_score_dict)
        self._par_score_value = sum(
            self._par_score_dict.values()) / len(self._par_score_dict)
        del self._word_score_dict
        del self._par_score_dict
        
