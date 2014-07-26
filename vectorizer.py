#coding=utf8
__author__ = 'Sam Raker'

from functools import partial
import gzip
from itertools import chain
from json import dump, dumps, loads
import operator
from os import mkdir
from os.path import exists, join, split
import re

import numpy

from tools import eld


def file_to_tuple(infile):
    """
    Reads a file containing one item per line and returns the contents as a tuple
    :param infile: the file to read
    :type infile: string (filename)
    :return: tuple of strings
    """
    with open(infile) as f:
        return tuple((line.rstrip() for line in f))


def get_tuple_dict(infiles):
    """
    Takes a list of infiles, parses their titles, and converts them into dictionaries
    of tuples via file_to_tuple
    :param infiles: files to convert to tuples
    :type infiles: list of strings (filenames)
    :return: {val:tuple...} dict, {val:tuple...} dict
    """
    p = re.compile(r'(\w+?)_set\.txt')
    tuple_dict = {}
    for fil in infiles:
        tup_title = re.match(p, split(fil)[-1]).group(1)
        tuple_dict[tup_title] = file_to_tuple(fil)
    return tuple_dict


def to_vector(lst, tup):
    """
    Takes a list and tuple and returns a list [0, 1, 0...], where a 1 represents
    the presence of an item from the tuple in the list, and 0 the absence of that item
    :param lst: the list to vectorize
    :type lst: list
    :param tup: the tuple to use as the vector map
    :type tup: tuple
    :param val: the value being vectorized
    :type val: string
    :return: list of ints (1s or 0s)
    """
    # initialize an empty vector, with an extra slot for OOV items
    # vector_list = numpy.zeros(shape=(1,(len(tup) + 1)))
    vector_list = set()
    oov_idx = len(tup)+1
    for item in lst:
        try:
            vector_list.add(int(tup.index(item)))
        except (ValueError, IndexError):
            vector_list.add(oov_idx)
    return list(vector_list)


def extracted_to_vector(extracted, tup, val):
    """
    Takes a JSON object as output by extract_info (q.v.), and vectorizes one of its values
    with tup as a reference
    :param extracted: the JSON object to parse
    :type extracted: list
    :param tup: the reference tuple, as output by file_to_tuple
    :type tup: tuple of ints (1s or 0s)
    :param val: the value to vectorize
    :type val: string
    :return: tuple of ints (1s or 0s)
    """
    lst = extracted[1][0][val]
    if lst and isinstance(lst[0], list):
        lst = list(chain.from_iterable(lst))
    return to_vector(lst, tup)


def write_wrapper(item, outfile):
    """
    Serializes item to JSON and appends it to outfile
    :param item: the item to serialize
    :type item: anything JSON-serializable
    :param outfile: the file to append the serialized object to
    :type outfile: string (filename)
    :return: None (writes to outfile)
    """
    if not exists(outfile):
        with gzip.open(outfile, mode="wb") as fil:
            fil.write(dumps(item) + "\n")
    else:
        with gzip.open(outfile, mode="ab") as fil:
            fil.write(dumps(item) + "\n")


def group_by_tags(js_file, tuple_dict, outdir=None):
    """
    Reads the contents of a JSON file line by line, vectorizes certain values
    from the JSON file, and serializes the result
    :param js_file: the JSON file to read
    :type js_file: string (filename)
    :param tuple_dict: dictionary of value tuples, as created
    by get_tuple_dicts (q.v.)
    :type tuple_dict: {string:(string, string...)}
    :param outdir: the directory to write the hashtag-specific files to
    :type outdir: string (path to directory)
    :return: None (serializes to outdir/hashtag.json for each hashtag)
    """
    print "group_by_tags ({0})".format(js_file)
    vals = ["domains", "hashtags", "mentions", "split_hashtags", "urls", "words"]
    with open(js_file) as f:
        i = 0
        for line in f:
            i += 1
            print i
            js = loads(line)
            vectors = [extracted_to_vector(js, tuple_dict[vals[x]], vals[x]) for x in xrange(len(vals))]
            for hashtag in js[1][0]["hashtags"]:
                outfile = join(outdir, "{0}.json.gz".format(hashtag.lower()))
                with gzip.open(outfile, "ab") as fil:
                    fil.write(dumps(vectors)+"\n")


def group_non_vectors(js_file, outdir):
    """
    Reads the contents of a JSON file line by line, pulls out certain values,
    and serializes the result.
    :param js_file: the JSON file to read
    :type js_file: string (filename)
    :param outdir: the directory to write the hashtag-specific files to
    :type outdir: string (path to directory)
    :return: None (serializes to outdir/hashtag.json for each hashtag)
    """
    print "group_non_vectors ({0})".format(js_file)
    vals = ["day", "is_weekday"]
    user_vals = ["follow_ratio", "following", "followers", "offset"]
    with open(js_file) as f:
        i = 0
        for line in f:
            i += 1
            print i
            js = loads(line)
            d = {val: js[1][0].get(val) for val in vals}
            d.update({val: js[1][1].get(val) for val in user_vals})
            for hashtag in js[1][0]["hashtags"]:
                outfile = join(outdir, "{0}.json.gz".format(hashtag.lower()))
                write_wrapper(d, outfile)


def vector_map(v1, v2):
    """
    Helper function for combine_vectors: replaces a missing vector with
    an all-0 vector of the same length as the other vector
    :param v1: the first vector to combine
    :type v1: list of 1s and/or 0s
    :param v2: the second vector to combine
    :type v2: list of 1s and /or 0s
    :return: list of 1s and/or 0s
    """
    if not v1:
        v1 = [0]*len(v2)
    elif not v2:
        v2 = [0]*len(v1)
    return map(operator.or_, v1, v2)


def get_val(line, val):
    """
    Converts a line of a file from JSON and returns val (or None if val isn't found).
    :param line: the line of the JSON file to read
    :type line: string (JSON)
    :param val: the specific value to extract
    :type val: string
    :return: float, int, or None
    """
    return loads(line)[val]


def vectorize(start, stop):
    """
    Master function
    :return: None
    """
    sets = eld("sets")
    extracted = eld("extracted2")[start:stop]
    td = get_tuple_dict(sets)
    outdir = "tag-vectors"
    if not exists(outdir):
        mkdir(outdir)
    for fil in extracted:
        try:
            group_by_tags(fil, td, outdir)
        except (TypeError, ValueError, OverflowError):
            continue


def non_vectorize(start, stop):
    """
    vectorize equivalent for non-vector values
    :return: None
    """
    extracted = eld("extracted2")[start:stop]
    outdir = "tag_values"
    if not exists(outdir):
        mkdir(outdir)
    for fil in extracted:
        try:
            group_non_vectors(fil, outdir)
        except (TypeError, ValueError, OverflowError):
            continue


def get_master_vectors(infile, outfile):
    """
    Reads all vector lists from infile, combine
    :param infile:
    :param outfile:
    :return:
    """
    vals = ["domains", "hashtags", "mentions", "split_hashtags", "urls", "words"]
    out_dict = {"domains": [], "hashtags": [], "mentions": [], "split_hashtags": [], "urls": [], "words": []}
    with gzip.open(infile) as f:
        while True:
            try:
                line = loads(f.next())
                for x in xrange(len(line)):
                        out_dict[vals[x]] += line[x]
            except (TypeError, ValueError) as e:
                print vals[x], line[x]
                raise e
            except StopIteration:
                break
    for key in out_dict:
        out_dict[key] = list(set(out_dict[key]))
    with gzip.open(outfile, "w") as f:
        f.write(dumps(out_dict))

def get_master_nonvectors(infile, outfile):
    """
    Equivalent of get_master_vectors for non-vector values.
    Calls the following values for the following values:
        day: arithmetic mean, median, standard deviation
        is_weekday: arithmetic mean, median, standard deviation
        follow_ratio: arithmetic mean, median, standard deviation
        following: arithmetic mean, median, standard deviation
        followers: arithmetic mean, median, standard deviation
        offset: root mean square, median, standard deviation
    :param infile: the file to process
    :type infile: string (filename)
    :param outfile: the file to write to
    :type outfile: string (filename)
    :return: None (writes to outfile)
    """
    vals = ["day", "is_weekday", "follow_ratio", "following", "followers", "offset"]
    results = {}
    for val in vals:
        with gzip.open(infile) as f:
            get_partial = partial(get_val, val=val)
            arr = numpy.array([get_partial(line) for line in f])
        try:
            results["{0}_std_dev".format(val)] = arr.std(0)
        except TypeError:
            results["{0}_std_dev".format(val)] = -1  # there was an error
        try:
            results["{0}_median".format(val)] = numpy.median(arr)
        except TypeError:
            results["{0}_median".format(val)] = -1
        if val != "offset":
            try:
                results["{0}_mean".format(val)] = arr.mean()
            except TypeError:
                results["{0}_mean".format(val)] = -1
        else:
            try:
                results["{0}_rms".format(val)] = numpy.sqrt(numpy.mean(arr ** 2))
            except TypeError:
                results["{0}_rms".format(val)] = -1
    with gzip.open(outfile, "wb") as f:
        dump(results, f)


def master_vectorize():
    """
    Equivalent of vectorize for get_master_vectors: calls get_master_vectorize on
    all files in tag_vectors
    :return: None (writes to master_vectors)
    """
    outdir = "master_vectors"
    if not exists(outdir):
        mkdir(outdir)
    clustered_vectors = eld("tag-vectors")
    for fil in clustered_vectors:
        get_master_vectors(fil, join(outdir, split(fil)[1]))


def master_nonvectorize():
    """
    Equivalent of master_vectorize for get_master_nonvectors: calls get_master_nonvectors
    for all files in tag_values
    :return: None (writes to master_values)
    """
    outdir = "master_values"
    if not exists(outdir):
        mkdir(outdir)
    clustered_values = eld("tag_values")
    for fil in clustered_values:
        get_master_nonvectors(fil, join(outdir, split(fil)[1]))
