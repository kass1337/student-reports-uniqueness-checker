from enum import Enum


class error_codes(Enum):
    FILE_NOT_FOUND = 1
    NO_DB_CONNECT = 2
    BAD_INIT_FILE = 3
    BAD_INIT = 4
    BAD_INSERT = 5
    BAD_QUERY = 6 # таких слов нет
    NOT_FOUND = 7 # комбинация таких слов не найдена
    BAD_FIND = 8
    BAD_SELECT = 9 # не получилось запросить score
    NO_CUSTOM_FILES = 10