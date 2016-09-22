#!/usr/bin/env python

import sys
import os
import re
import datetime

from collections import defaultdict

from optparse import OptionParser

# DEBUG = False
# DEBUG = True
# LOG = "strace.log"

# TOP_NUMBER_OPERATIONS = 10
# TOP_NUMBER_VOLUME = 3

OPEN_REGEX = re.compile(
    'open\("(?P<filepath>[^"]+)", [^\)]*\) = (?P<descriptor>[0-9]+)')
CLOSE_REGEX = re.compile(
    'close\((?P<descriptor>[0-9]+)\)[\s]+=')
WRITE_REGEX = re.compile(
    'write\((?P<descriptor>[0-9]+), ".+\) = (?P<amount>[0-9]+)')
READ_REGEX = re.compile(
    'read\((?P<descriptor>[0-9]+), ".+\) = (?P<amount>[0-9]+)')
# TIME_REGEX = re.compile("([0-9]{2}):([0-9]{2}):([0-9]{2})\.([0-9]+)")
# PID_REGEX = re.compile("^(?P<pid>[0-9]+)")
# DUP_REGEX = re.compile(
# "dup[23]?\((?P<old_descriptor>[0-9]+), [0-9]+\)[\s]+=(?P<descriptor>[0-9]+)")


# def parse_time(line):
#    time_data = TIME_REGEX.search(line)
#    return datetime.time(*map(int, time_data.groups()))


# def log(msg):
#    if not DEBUG:
#        return
#    print msg


def main(logfile):
    open_desc = {}
    files = {
        'unknown': {
            'writes': 0,
            'reads': 0
            }
        }

    with open(logfile) as fp:
        for line in fp:
            open_search = OPEN_REGEX.search(line)
            close_search = CLOSE_REGEX.search(line)
            write_search = WRITE_REGEX.search(line)
            read_search = READ_REGEX.search(line)

            if not (write_search or open_search or close_search or read_search):
                continue
            if open_search:
                file = open_search.group(1)
                inode = open_search.group(2)

                open_desc[inode] = file
                if file in files:
                    continue
                else:
                    files[file] = {'writes': 0, 'reads': 0}

            elif close_search:
                inode = close_search.group(1)
                if inode in open_desc:
                    del open_desc[inode]

            elif read_search:
                inode = read_search.group(1)
                amount = int(read_search.group(2))
                if inode in open_desc:
                    file = open_desc[inode]
                    files[file]['reads'] = files[file]['reads'] + amount
                else:
                    files['unknown']['reads'] = files['unknown']['reads'] + amount

            elif write_search:
                inode = write_search.group(1)
                amount = int(write_search.group(2))
                if inode in open_desc:
                    file = open_desc[inode]
                    files[file]['writes'] = files[file]['writes'] + amount
                else:
                    files['unknown']['writes'] = files['unknown']['writes'] + amount

    total_read = 0
    total_write = 0
    xlog_write = 0
    unknown = files['unknown']
    del files['unknown']

    for file in sorted(files):
        print "{0} reads: {1} MB, writes: {2} MB".format(
            file, files[file]['reads'] / 1048576.0,
            files[file]['writes'] / 1048576.0)

        total_read = total_read + files[file]['reads']
        total_write = total_write + files[file]['writes']
        if re.compile(r'pg_xlog').search(file) is not None:
            xlog_write = xlog_write + files[file]['writes']

    print 'unknown reads: {0} MB, writes {1} MB'.format(
        unknown['reads'] / 1048576.0, unknown['writes'] / 1048576.0)
    print 'total read: {0} MB'.format(total_read / 1048576.0)
    print 'xlog write: {0} MB'.format(xlog_write / 1048576.0)
    print 'total write: {0} MB'.format(total_write / 1048576.0)


if __name__ == '__main__':

    parser = OptionParser()

    (option, args) = parser.parse_args()

    if len(args) != 1:
        parser.error("incorrect number of arguments")
    main(args[0])
