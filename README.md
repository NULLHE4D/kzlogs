# kzlogs

A half-baked python script for getting a summary of [ndjson](http://ndjson.org/) formatted HTTP traffic logs. The summary includes the request count, IP addresses, HTTP error count (categorized-ish), number of requests per route (method + path), and other custom stuff.

## Usage

**kzlogs** requires that you provide a valid JSON configuration file (see [kzlogs.json](kzlogs.json)).

### Command line options

```console
foo@bar:~$: python3 kzlogs.py -h
usage: kzlogs.py [-h] [-s SINGLE | -r RANGE] [-c CONFIG] -d DIR [-v]

optional arguments:
  -h, --help            show this help message and exit
  -s SINGLE, --single SINGLE
                        date of file log (YYYYMMDD)
  -r RANGE, --range RANGE
                        date range of file logs (DATE1-DATE2) (same format as with -s flag)
  -c CONFIG, --config CONFIG
                        path to JSON configuration file
  -d DIR, --dir DIR     log directory
  -v, --verbose         increase output verbosity
```

## Log files format

The log files which **kzlogs** can process must be compressed with [gzip](https://www.gzip.org/) with a name formatted as *access.log-YYYYMMDD.gz* (e.g., *access.log-20210427.gz*) but this can be easily modified in code.

An example of a single entry in these logs is as follows:

```json

{"remoteAddr":"::ffff:127.0.0.1","time":"2021-04-22T14:44:51.996Z","method":"GET","url":"/login","httpVersion":"1.0","user-agent":"Mozilla/5.0 (X11; L
inux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36","reqBody":{},"status":"200", "more keys": "more values"}
```
