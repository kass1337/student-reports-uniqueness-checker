from error_codes import error_codes
from db import Db
from normalyzer import Normalyzer
import argparse
from collections import OrderedDict
class Finder(object):
    _db = None
    def __init__(self):
        self._db = Db()
    def _frequency_score(self, rowsLoc):
        rows_mapped = {}
        for row in rowsLoc:
            try:
                rows_mapped[row] += 1
            except KeyError:
                rows_mapped[row] = 1
        normalyzer = Normalyzer()
        return normalyzer.normalazye(rows_mapped, 0)
    def find_by_freq(self, query, certain_subject):
        query = query.split(" ")
        word_id_list = self._db.get_words_ids(query)
        freq_pars = self._frequency_score(self._db.get_match_rows(query, word_id_list))
        data = self._db.get_data_by_par_id(freq_pars, certain_subject)
        data = OrderedDict(sorted(data.items(), key=lambda kv : kv[1], reverse=True))
        print(data)


if __name__ == "__main__":
    finder = Finder()
    parser = argparse.ArgumentParser(
        description='Find report by query')
    parser.add_argument('-q', type=str, help='Query string to find',
                        metavar='Word1 Word2', required=True)
    parser.add_argument('-s', type=int, help='Certain subhect id to find',
                        metavar='N')
    args = parser.parse_args()
    if args.s is not None:
        rows = finder.find_by_freq(args.q, args.s)
    else:
        
        rows = finder.find_by_freq(args.q, 0)
    
        