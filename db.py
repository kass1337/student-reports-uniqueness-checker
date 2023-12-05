import psycopg2
from error_codes import error_codes
import os
import nltk
from nltk.tokenize import word_tokenize
nltk.download('punkt', quiet=True)


class Db(object):
    _conn = None
    _cur = None

    def __init__(self):
        self._initDB()

    def _initDB(self):
        try:
            self._conn = psycopg2.connect(
                dbname='uniq_control', user='postgres', password='postgres', host='localhost') #CREATE DOCKER
        except Exception:
            exit(error_codes.NO_DB_CONNECT.value)
        try:
            with open('init.txt', 'r') as file:
                sql_commands = file.read()
        except Exception:
            exit(error_codes.BAD_INIT_FILE.value)
        try:
            self._cur = self._conn.cursor()
            self._cur.execute(sql_commands)
            self._conn.commit()
        except Exception:
            if self._conn is not None:
                self._conn.rollback()
                self._conn.close()
            exit(error_codes.BAD_INIT.value)

    def select_closest_par(self, inserted_score):
        data = None
        query = f"SELECT * FROM\
           (\
                (SELECT score.id, score.score_par, report.name FROM score, report WHERE score_par >= {inserted_score} and report.id=score.report_id ORDER BY score_par LIMIT 5)\
                UNION ALL\
                (SELECT score.id, score.score_par, report.name  FROM score, report WHERE score_par < {inserted_score} and report.id=score.report_id ORDER BY score_par DESC LIMIT 5)\
                ) as foo ORDER BY abs({inserted_score}-score_par) LIMIT 5".format(inserted_score=inserted_score)
        try:
            self._cur.execute(query)
            data = self._cur.fetchall()
        except Exception:
            exit(error_codes.BAD_SELECT.value)
        #if data < coef del data
        return data
    def select_closest_word(self, inserted_score):
        data = None
        query = f"SELECT * FROM\
           (\
                (SELECT score.id, score.score_word, report.name FROM score, report WHERE score_word >= {inserted_score} and report.id=score.report_id ORDER BY score_word LIMIT 5)\
                UNION ALL\
                (SELECT score.id, score.score_word, report.name  FROM score, report WHERE score_word < {inserted_score} and report.id=score.report_id ORDER BY score_word DESC LIMIT 5)\
                ) as foo ORDER BY abs({inserted_score}-score_word) LIMIT 5".format(inserted_score=inserted_score)
        try:
            self._cur.execute(query)
            data = self._cur.fetchall()
        except Exception:
            exit(error_codes.BAD_SELECT.value)
        #if data < coef del data
        return data

    def insert_all(self, subject_id, file_name, par_score, word_score, content):
        try:
            # insert report
            self._cur.execute("INSERT INTO report(subject_id, name) VALUES (%s, %s) RETURNING id",
                              (subject_id, os.path.abspath(file_name)))
            inserted_report_id = self._cur.fetchone()[0]
            # insert score
            self._cur.execute("INSERT INTO score(report_id, score_par, score_word) VALUES (%s, %s, %s)", (
                inserted_report_id, par_score, word_score))  # AVG SCORE
            # insert words, header, make link
            for key in content:
                self._cur.execute("INSERT INTO paragraph(name, report_id) VALUES (%s, %s) RETURNING id", (
                    key, inserted_report_id))  # insert paragraph
                inserted_header_id = self._cur.fetchone()[0]
                if content[key]:
                    word_list = word_tokenize(content[key])
                    word_list = [word.lower() for word in word_list]
                    if word_list:
                        for word in word_list:
                            try:
                                self._conn.commit()
                                self._cur.execute(
                                    "INSERT INTO word (word) VALUES (%s) RETURNING id", (word,))
                                inserted_word_id = self._cur.fetchone()[0]
                            except psycopg2.IntegrityError:
                                self._conn.rollback()
                                self._cur.execute(
                                    "SELECT id FROM word WHERE word = %s", (word,))
                                inserted_word_id = self._cur.fetchone()[0]
                            self._conn.commit()
                            self._cur.execute("INSERT INTO paragraph_and_word(paragraph_id, word_id) VALUES(%s, %s)", (
                                inserted_header_id, inserted_word_id))

            self._conn.commit()
        except Exception as e:
            print(e)
            exit(error_codes.BAD_INSERT.value)
        return inserted_report_id

    def get_words_ids(self, query_list):
        id_list = list()
        for word in query_list:
            self._cur.execute("select id from word where word = %s", (word, ))
            res = self._cur.fetchone()
            if res is not None:
                row = int(res[0])
                id_list.append(row)
            else:
                exit(error_codes.BAD_QUERY.value)
        return id_list

    def get_match_rows(self, query_list, word_list):
        sql_name = list()  # имена столбцов
        sql_join = list()  # INNER JOIN
        sql_condition = list()  # условия WHERE
        sql_full_query = """"""
        for word_index in range(0, len(word_list)):
            word_id = word_list[word_index]
            if word_index == 0:
                sql_name.append("""w0.paragraph_id parid """)
                sql_condition.append(
                    """WHERE w0.word_id={} """.format(word_id))
            else:
                if len(word_list) >= 2:
                    sql_join.append("""INNER JOIN paragraph_and_word w{}
                   on w0.paragraph_id=w{}.paragraph_id""".format(word_index, word_index))
                    sql_condition.append(
                        """  AND w{}.word_id={}""".format(word_index, word_id))
                    pass
            pass
        sql_full_query += "SELECT "
        for sql in sql_name:
            sql_full_query += "\n"
            sql_full_query += sql
        sql_full_query += "\n"
        sql_full_query += "FROM paragraph_and_word w0 "
        for sql in sql_join:
            sql_full_query += "\n"
            sql_full_query += sql
        for sql in sql_condition:
            sql_full_query += "\n"
            sql_full_query += sql
        try:
            self._cur.execute(sql_full_query)
            rows_temp = self._cur.fetchall()
            rows = [row[0] for row in rows_temp]
        except Exception:
            exit(error_codes.BAD_FIND.value)
        return rows

    def get_data_by_par_id(self, par_id_dict, certain_subject):
        data = dict()
        if par_id_dict:
            for id in par_id_dict.keys():
                try:
                    if certain_subject == 0:
                        self._cur.execute("SELECT paragraph.name, paragraph.report_id, r.name, r.subject_id, s.name\
                                        from paragraph\
                                        inner join report r on r.id=paragraph.report_id\
                                        inner join subject s on r.subject_id=s.id\
                                        where paragraph.id= %s", (id,))
                    else:
                        self._cur.execute("SELECT paragraph.name, paragraph.report_id, r.name, r.subject_id, s.name\
                                        from paragraph\
                                        inner join report r on r.id=paragraph.report_id\
                                        inner join subject s on r.subject_id=s.id\
                                        where paragraph.id=%s and s.id=%s", (id, certain_subject))
                    rows = self._cur.fetchall()
                    data[id] = rows, par_id_dict[id]
                except Exception:
                    exit(error_codes.BAD_FIND.value)
            if data:
                return data

            else:
                exit(error_codes.NOT_FOUND.value)

        else:
            exit(error_codes.NOT_FOUND.value)

    def get_subject_by_id(self, subject_id_list):
        subject_name_list = list()
        if subject_id_list:
            for id in subject_id_list:
                self._cur.execute(
                    "SELECT name FROM subject where id = %s", (id, ))
                row = self._cur.fetchall()
                subject_name_list.append((row[0], id))
            if subject_name_list:
                return subject_name_list
            else:
                exit(error_codes.NOT_FOUND.value)
        else:
            exit(error_codes.NOT_FOUND.value)
