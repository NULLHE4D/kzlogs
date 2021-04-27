#!/usr/bin/python

import argparse, gzip, re, datetime, os, json
from sys import stderr
from shutil import copyfileobj


class LogData():

    def __init__(self, custom):
        
        self.req_count = 0
        self.ip_addresses = []

        self.bad_requests = 0
        self._404_requests = 0
        self.server_errors = 0
        self.undefined_errors = 0

        self.rpr = {} # requests per route (method + path)
        self.custom = {i["title"]:[0,0] for i in custom}

    def inc_rpr(self, route, ignored_routes_regexes=[]):
        for regex in ignored_routes_regexes:
            if regex.match(route): return
        if route in self.rpr: self.rpr[route] += 1
        else: self.rpr[route] = 1

    def append_addr(self, addr):
        if not addr in self.ip_addresses: self.ip_addresses.append(addr)

    def append_custom(self, title, success):
        if success: self.custom[title][1] += 1
        else: self.custom[title][0] += 1


def single_date_regex_type(arg_value):
    pattern = re.compile("^[0-9]{8}$")
    if not pattern.match(arg_value):
        raise argparse.ArgumentTypeError
    return arg_value


def date_range_regex_type(arg_value):
    pattern = re.compile("^[0-9]{8}-[0-9]{8}$")
    if not pattern.match(arg_value):
        raise argparse.ArgumentTypeError

    dates = arg_value.split("-")
    if dates[0] > dates[1]:
        raise argparse.ArgumentTypeError
    
    return arg_value


def get_file_names(single_date, date_range, file_format="access.log-%s.gz"):
    arr = []

    if single_date:
        arr.append(file_format % single_date)

    elif date_range:
        dates = date_range.split("-")
        start_date = datetime.datetime.strptime(dates[0], "%Y%m%d")
        end_date = datetime.datetime.strptime(dates[1], "%Y%m%d")
        delta = end_date - start_date

        date_list = [end_date - datetime.timedelta(days=i) for i in range(delta.days + 1)]

        for i in date_list:
            d = "%d%02d%02d" % (i.year, i.month, i.day)
            arr.append(file_format % d) 

    return sorted(arr)


def gzip_uncompress(compressed):
    uncompressed = compressed[:-3]
    with gzip.open(compressed, 'rb') as f_in:
        with open(uncompressed, 'wb') as f_out:
            copyfileobj(f_in, f_out)
    return uncompressed


def delete_file(f):
    try: os.remove(f)
    except Exception as e: print("unable to remove file '%s': %s" % (f, e.__class__.__name__))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-s", "--single", type=single_date_regex_type, help="date of file log (YYYYMMDD)")
    group.add_argument("-r", "--range", type=date_range_regex_type, help="date range of file logs (DATE1-DATE2) (same format as with -s flag)")
    parser.add_argument("-c", "--config", default="kzlogs.json", help="path to JSON configuration file")
    parser.add_argument("-d", "--dir", required=True, help="log directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")
    args = parser.parse_args()

    single_date = args.single
    date_range = args.range
    config_file = args.config
    logdir = args.dir
    verbose = args.verbose

    log_files = get_file_names(single_date, date_range)

    config = json.load(open(config_file, "r"))
    ignored_routes_regexes = [re.compile(i) for i in config["ignored_routes"]]
    for i in range(len(config["custom"])): config["custom"][i]["regex"] = re.compile(config["custom"][i]["route"])
    log_data = LogData(config["custom"])

    for i in log_files:
        fgz = os.path.join(logdir, i)
        f = gzip_uncompress(fgz)

        with open(f, "r") as log_file:
            for line in log_file:
                log = json.loads(line)

                method = log[config["method_key"]]
                path = log[config["path_key"]]
                route = "%s %s" % (method.upper(), path)
                ip_address = log[config["ip_address_key"]]

                log_data.req_count += 1
                log_data.append_addr(ip_address)
                log_data.inc_rpr(route, ignored_routes_regexes)

                status_code = int(log[config["status_code_key"]])
                if status_code == 400: log_data.bad_requests += 1
                elif status_code == 404: log_data._404_requests += 1
                elif status_code >= 500: log_data.server_errors += 1
                elif status_code >= 400: log_data.undefined_errors += 1

                for i in range(len(config["custom"])):
                    if config["custom"][i]["regex"].match(route):
                        log_data.append_custom(config["custom"][i]["title"], (status_code == config["custom"][i]["success_status"]))
                        break

        delete_file(f)

    # output
    print("request count: %d" % log_data.req_count)
    print("IP addresses: %d (%s)" % (len(log_data.ip_addresses), ", ".join(log_data.ip_addresses)))
    print("")
    print("bad requests (400): %d" % log_data.bad_requests)
    print("not found (404): %d" % log_data._404_requests)
    print("server errors (5XX): %d" % log_data.server_errors)
    print("undefined errors (4XX): %d" % log_data.undefined_errors)
    print("")

    for i in log_data.custom:
        print("%s: successes -> %d, failures -> %d" % (i, log_data.custom[i][1], log_data.custom[i][0]))
        print("")

    print("requests per route:")
    for route in log_data.rpr: print("  - %s -> %d" % (route, log_data.rpr[route]))
