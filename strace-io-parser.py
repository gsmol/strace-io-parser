#!/usr/bin/env python

import sys
import os
import re
import datetime

from optparse import OptionParser


OPEN_REGEX = re.compile(
    'open\("(?P<filepath>[^"]+)", [^\)]*\) = (?P<descriptor>[0-9]+)')
CLOSE_REGEX = re.compile(
    'close\((?P<descriptor>[0-9]+)\)[\s]+=')
WRITE_REGEX = re.compile(
    'write\((?P<descriptor>[0-9]+), ".+\) = (?P<amount>[0-9]+)')
READ_REGEX = re.compile(
    'read\((?P<descriptor>[0-9]+), ".+\) = (?P<amount>[0-9]+)')
PID_REGEX = re.compile(
    "^(?P<pid>[0-9]+)")


def main(logfile):
    open_desc = {}
#    open_desc = {
#        'pid1': {
#            'inode1': 'file',
#            'inode2': 'file2',
#        }
#        'pid2': {
#            'inode3': 'fil3',
#            'inode4': 'file4',
#        }
#    }
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
            read_search = READ_REGEX.search(line)
            write_search = WRITE_REGEX.search(line)
            pid_search = PID_REGEX.search(line)

            if not (open_search or close_search or read_search or write_search):
                continue
            if open_search:
                pid = pid_search.group(1)
                inode = open_search.group(2)
                file = open_search.group(1)

                if pid in open_desc:
                    open_desc[pid][inode] = file
                else:
                    open_desc[pid] = {inode: file}
                if file in files:
                    continue
                else:
                    files[file] = {'writes': 0, 'reads': 0}

            elif close_search:
                pid = pid_search.group(1)
                inode = close_search.group(1)
                if inode in open_desc[pid]:
                    del open_desc[pid][inode]

            elif read_search:
                pid = pid_search.group(1)
                inode = read_search.group(1)
                amount = int(read_search.group(2))
                if pid in open_desc:
                    if inode in open_desc[pid]:
                        file = open_desc[pid][inode]
                        files[file]['reads'] = files[file]['reads'] + amount
                    else:
                        files['unknown']['reads'] = files['unknown']['reads'] + amount

                else:
                    files['unknown']['reads'] = files['unknown']['reads'] + amount

            elif write_search:
                pid = pid_search.group(1)
                inode = write_search.group(1)
                amount = int(write_search.group(2))
                if pid in open_desc:
                    if inode in open_desc[pid]:
                        file = open_desc[pid][inode]
                        files[file]['writes'] = files[file]['writes'] + amount
                    else:
                        files['unknown']['writes'] = files['unknown']['writes'] + amount
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

    print 'unknown read: {0} MB'.format(unknown['reads'] / 1048576.0)
    print 'unknown write: {0} MB'.format(unknown['writes'] / 1048576.0)
    print 'total read: {0} MB'.format(total_read / 1048576.0)
    print 'xlog write: {0} MB'.format(xlog_write / 1048576.0)
    print 'total write: {0} MB'.format(total_write / 1048576.0)


if __name__ == '__main__':

    parser = OptionParser()

    (option, args) = parser.parse_args()

    if len(args) != 1:
        parser.error("incorrect number of arguments")
    main(args[0])
