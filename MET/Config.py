#! /usr/bin/env python3
#
# Load a YAML configuration file for how to process a CSV file
# into a PostgreSQL database, and then possibly into a NetCDF and/or CSV file(s)
#
# June-2022, Pat Welch, pat@mousebrains.com

from argparse import ArgumentParser
import yaml
import json
import logging
import re
import datetime
import os.path
import sys

class Config:
    def __init__(self, args:ArgumentParser) -> None:
        fn = args.yaml
        key = args.key

        if not os.path.isfile(fn):
            raise FileNotFoundError(fn)
        with open(fn, "r") as fp: info = yaml.safe_load(fp)

        if key not in info:
            raise KeyError(f"key {key} does not exist in {fn}")

        item = info[key]

        for name in ["timeToWait", "regexp", "delimiter", "headers"]:
            if name not in item: raise KeyError(f"{name} does not exist in {key} in {fn}")

        self.fn = fn
        self.key = key
        self.ship = item["ship"]
        self.regexp = re.compile(item["regexp"])
        self.timeToWait = item["timeToWait"]
        self.headerSkipBefore = max(0,item["headerSkipBefore"]) if "headerSkipBefore" in item else 0
        self.headerSkipAfter = max(0,item["headerSkipAfter"]) if "headerSkipAfter" in item else 0
        self.delimiter = re.compile(item["delimiter"])

        self.dbInfo = self.dbParams(fn, key, info, "db.parameters")
        self.csv = self.decimateParameters(fn, key, info, "csv.parameters")
        self.netcdf = self.decimateParameters(fn, key, info, "netCDF.parameters")
        hdrKey = item["headers"]
        if hdrKey not in info:
            raise KeyError(f"{hdrKey} not in {fn} referenced from {key}")
        self.headers = info[hdrKey]

    def __repr__(self) -> str:
        info = {
                "fn": self.fn,
                "key": self.key,
                "ship": self.ship,
                "regexp": str(self.regexp),
                "timeToWait": str(self.timeToWait),
                "headerSkipBefore": str(self.headerSkipBefore),
                "headerSkipAfter": str(self.headerSkipAfter),
                "delimiter": str(self.delimiter),
                "dbInfo": self.dbInfo,
                "csv": self.csv,
                "netcdf": self.netcdf,
                }
        return json.dumps(info, indent=4, sort_keys=True)

    @staticmethod
    def addArgs(parser:ArgumentParser) -> None:
        parser.add_argument("--yaml", type=str, required=True, help="Name of YAML file to load")
        parser.add_argument("--key", type=str, required=True,
                help="ID string to load from the YAML file")

    def dbParams(self, fn:str, key:str, info:dict, dbName:str) -> dict:
        item = info[key]
        if dbName not in item: raise KeyError(f"{dbName} not in {key} in {fn}")
        name = item[dbName]
        if name not in info: raise KeyError(f"{name} not in {fn} referenced from {key}")
        dbInfo = info[name]
        if "table" not in dbInfo: raise KeyError(f"table not in {name} in {fn}")
        if "schema" not in dbInfo: raise KeyError(f"schema not in {name} in {fn}")
        tbl = dbInfo["table"]
        columns = []
        for (col, val) in dbInfo["schema"].items():
            columns.append(f"{col} {val}")
        if "supplemental" in dbInfo: columns.extend(dbInfo["supplemental"])
        sql = f"CREATE TABLE IF NOT EXISTS {tbl} (\n  "
        sql+= ",\n  ".join(columns)
        sql+= f"\n); -- {tbl}"

        insertPre = f"INSERT INTO {tbl} ("
        insertMid = ") VALUES("

        exValues = []
        if "insert" in dbInfo and "extra" in dbInfo["insert"]:
            exKeys = dbInfo["insert"]["extra"]
            for a in exKeys:
                if a not in item:
                    raise KeyError("{a} not in {key} in {fn} from extra om {dbName}")
                exValues.append(item[a])
            insertPre += ",".join(exKeys) + ","
            insertMid += ",".join(["%s"] * len(exKeys)) + ","
        insertPost = ")"
        if "insert" in dbInfo and "onConflict" in dbInfo["insert"]:
            insertPost+= " ON CONFLICT " + dbInfo["insert"]["onConflict"]
        insertPost += ";"

        return {"create": sql, 
                "insertPre": insertPre,
                "insertMid": insertMid,
                "insertPost": insertPost,
                "extra": exValues,
                "table": tbl}

    def decimateParameters(self, fn:str,  key:str, info:str, paramName:str) -> dict:
        item = info[key]
        if paramName not in item: return None
        a = item[paramName] # CSV definition
        if a not in info:
            raise KeyError(f"{a} not in {fn} referenced from {key}")
        return info[a]

    def mkTable(self, cur):
        # cur.execute("DROP TABLE IF EXISTS met;") # TPW
        cur.execute(self.dbInfo["create"])

    def mapColumns(self, columns:list[str]) -> None:
        colmap = []
        headers = self.headers
        for index in range(len(columns)):
            name = columns[index]
            logging.info("name %s in headers %s", name, name in headers)
            if name not in headers: continue
            item = headers[name]
            colmap.append((
                index, 
                item["name"],
                item["type"] if "type" in item else None,
                item["format"] if "format" in item else None,
                ))
        self.__colmap = colmap

    def latLon(self, val:str) -> float:
        # First look for deg*100+ fractional minutes + direction
        matches = re.match(r"^\s*(\d+)(\d{2}[.]\d*)([EWNSewns])\s*$", val)
        if matches:
            deg = int(matches[1]) + (float(matches[2]) / 60)
            if matches[3] in ["W", "w", "S", "s"]: deg = -deg
            return deg

        # Now look for [+-]? deg*100 + fractional minutes
        matches = re.match(r"^\s*([+-]?)(\d+)(\d{2}[.]\d*)\s*$", val)
        if matches: #+-deg*100 + minutes
            deg = int(matches[2]) + (float(matches[3]) / 60)
            if matches[1] == "-": deg = -deg
            return deg
        # Now look for [+-]decimal degrees
        matches = re.match(r"^\s*([+-]?\d+[.]\d*)\s*$", val)
        if matches:
            return float(matches[1])
        return None

    def insertRow(self, cur, row:tuple) -> bool:
        names = []
        values = self.dbInfo["extra"].copy()
        t = None
        for item in self.__colmap:
            val = row[item[0]].strip()
            if len(val) == 0: continue
            if item[2] is None:
                pass
            elif item[2] == "date":
                date = datetime.datetime.strptime(val, item[3]).date()
                if t is None:
                    t = date
                    val = None
                else:
                    val = datetime.datetime.combine(date, t, tzinfo=datetime.timezone.utc)
                    t = None
            elif item[2] == "time":
                time = datetime.datetime.strptime(val, item[3]).time()
                if t is None:
                    t = time
                    val = None
                else:
                    val = datetime.datetime.combine(t, time, tzinfo=datetime.timezone.utc)
                    t = None
            elif item[2] == "epoch":
                val = datetime.datetime.fromtimestamp(float(val), tz=datetime.timezone.utc)
            elif item[2] == "latLonDegMin":
                val = self.latLon(val)
            else:
                logging.error("Unrecognized type %s", item)
            if val is None: continue # Date/Time
            names.append(item[1])
            values.append(val)
        sql = self.dbInfo["insertPre"] + ",".join(names) + self.dbInfo["insertMid"]
        sql+= ",".join(["%s"] * len(names)) + self.dbInfo["insertPost"]
        try:
            cur.execute(sql, values)
            return True
        except:
            logging.error("sql %s", sql)
            logging.error("Values %s\n%s", len(values), values)
            logging.exception("Error inserting row, %s", row)
            return False

if __name__ == "__main__":
    parser = ArgumentParser()
    Config.addArgs(parser)
    args = parser.parse_args()

    config = Config(args)
    print("CONFIG:", config)
