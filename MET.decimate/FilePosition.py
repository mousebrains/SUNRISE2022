#! /usr/bin/env python3
#
# PostgreSQL table of file positions
#
import logging
import os.path

class FilePosition:
    def __init__(self, table:str="filePosition") -> None:
        self.__create =f"CREATE TABLE IF NOT EXISTS {table} (\n"
        self.__create+= "  filename TEXT PRIMARY KEY,\n"
        self.__create+= "  position INTEGER NOT NULL CHECK(position > 0)\n"
        self.__create+=f"); -- {table}"

        self.__get = f"SELECT position FROM {table} WHERE filename=%s;"

        self.__set =f"INSERT INTO {table} VALUES (%s,%s)"
        self.__set+= " ON CONFLICT (filename)"
        self.__set+= " DO UPDATE SET position = EXCLUDED.position;"

        logging.info("FilePos\n%s\n%s\n%s", self.__create, self.__get, self.__set)

    def mkTable(self, cur) -> None:
        cur.execute(self.__create)

    def get(self, fn:str, cur) -> int:
        fn = os.path.abspath(os.path.expanduser(fn))
        cur.execute(self.__get, (fn,))
        for row in cur:
            return row[0]
        return None

    def set(self, fn:str, pos:int, cur) -> bool:
        try:
            fn = os.path.abspath(os.path.expanduser(fn))
            cur.execute(self.__set, (fn, pos))
            return True
        except:
            logging.exception("Trying to set fn=%s pos=%s", fn, pos)
            return False

if __name__ == "__main__":
    from argparse import ArgumentParser
    import psycopg2

    parser = ArgumentParser()
    parser.add_argument("--db", type=str, default="sunrise", help="Database to use")
    parser.add_argument("--filename", type=str, default="probar.probar", help="Filename to use")
    parser.add_argument("--set", type=int, help="Position to set for filename")
    args = parser.parse_args()

    fp = FilePosition()
    fn = args.filename

    with psycopg2.connect(f"dbname={args.db}") as db:
        cur = db.cursor()
        cur.execute("BEGIN;")
        fp.mkTable(cur)
        cur.execute("COMMIT;")
        print("fn", args.filename, "get", fp.get(fn, cur))
        if args.set is not None:
            cur.execute("BEGIN;")
            if fp.set(fn, args.set, cur):
                cur.execute("COMMIT;")
            else:
                cur.execute("ROLLBACK;")
            print("fn", args.filename, "get", fp.get(fn, cur))
