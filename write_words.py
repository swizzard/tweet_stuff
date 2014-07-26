#coding=utf8
__author__ = 'Sam Raker'

from itertools import chain, ifilter
from json import loads

from tools import eld, unifilter


def extractor(val, infile, outfile, user=False):
    """
    Extracts the given value from all the tweets in a file
    :param val: the value to extract
    :type val: string
    :param infile: file to extract from
    :type infile: string (file name)
    :param outfile: the file to write to
    :type outfile: string (file name)
    :return: None (writes to outfile)
    """
    outstr = ""
    outlist = []
    with open(infile) as f:
        for line in f:
            parsed = loads(line)
            if user:
                output = parsed[1][1].get(val)
            else:
                output = parsed[1][0].get(val)
            try:
                if isinstance(output[0], list):
                    output = chain.from_iterable(output)
            except IndexError:
                pass
            outlist += output
    outstr += "\n".join(ifilter(unifilter, outlist))
    with open(outfile, "a") as f:
        f.write(outstr)


def extract_folder(val, folder, outfile, user=False):
    """
    Calls extractor on every file in a folder
    :param val: the value to extract
    :type val: string
    :param folder: the path to the folder
    :type folder: string (path to folder)
    :param outfile: the file to write to
    :type outfile: string (file name)
    :return: None (writes to outfile)
    """
    for f in eld(folder):
        extractor(val, f, outfile, user)


def reconstructor(infiles, outfile):
    """
    Turns the contents of a number of files into a set and writes it to
    another file
    :param infiles: files to read from
    :type infiles: list of strings (file names)
    :param outfile: file to write to
    :type outfile: string (file name)
    :return: None (writes to outfile)
    """
    s = set()
    for infile in infiles:
        with open(infile) as f:
            s = s.union([x.rstrip() for x in f.readlines()])
    with open(outfile, "w") as f:
        f.write("\n".join(list(s)))
