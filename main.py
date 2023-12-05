import argparse

from work import Parser


def parse_args_and_proc():
    p = Parser()
    parser = argparse.ArgumentParser(
        description='Parse docx and insert it`s content to DB, analyze for copy-paste')
    parser.add_argument('-f', type=str, help='Path to the docx',
                        metavar='path/to/file.docx', required=True)
    parser.add_argument('-i', type=int, help='Subject id in DB',
                        metavar='N', required=True)
    parser.add_argument('-a', action='store_true', help='With Analyze')
    parser.add_argument('-s', help='path/to/custom_stopwords', type=str)
    parser.add_argument('-c', help='path/to/ignore_headings', type=str)
    args = parser.parse_args()
    if args.a:
        if args.c and args.s:
            p.parse_and_analyze(args.f, args.i, args.s, args.c)
        else:
            exit("Stopwords to ignore and Headings to ignore must be specified")
    else:
        p.parse(args.f, args.i)


if __name__ == "__main__":
    parse_args_and_proc()
