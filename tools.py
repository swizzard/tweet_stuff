#coding=utf8
__author__ = 'Sam Raker'

from itertools import chain, imap, ifilter
from json import dumps, loads
from os import listdir
from os.path import join
from time import sleep

import redis


class SafeRedis(redis.StrictRedis):
    """
    Subclass of redis.StrictRedis to handle transient connection errors
    """
    def __init__(self, verbose=True, max_attempts=-1, sleep_time=120, host='localhost', port='6379', db=0, *args, **kwargs):
        """
        :param verbose: if True, print a notice about the error
        :type verbose: bool
        :param max_attempts: maximum number of times to retry connecting to the server. Set to negative for infinite
        retries, 0 to try only once (i.e., not retry.)
        :type max_attempts: int
        :param sleep_time: time to sleep between trying to connect to the server again after a failed operation
        :type sleep_time: int
        :param host: same as for redis.StrictRedis, but unpacked from *args for notification purposes
        :param port: ""
        :param db: ""
        :param args: same as for redis.StrictRedis
        :param kwargs: ""
        """
        self.host = host
        self.port = port
        self.db = db
        self.sleep_time = sleep_time
        self.verbose = verbose
        if not isinstance(max_attempts, int):
            raise ValueError("max_attempts must be an integer (-1 for infinite attempts)")
        self.max_attempts = 0
        self.attempts = 0
        if max_attempts < 0:
            self.recur_infinitely = True
        else:
            self.recur_infinitely = False
            self.max_attempts = max_attempts
        super(SafeRedis, self).__init__(host, port, db, *args, **kwargs)

    def set(self, name, value, *args, **kwargs):
        """
        Same as redis.StrictRedis().set, except will retry connection based on class's reconnection settings
        (see __init__ for more information)
        :param name: same as redis.StrictRedis().set
        :param value: ""
        :param args: ""
        :param kwargs: ""
        """
        try:
            return super(SafeRedis, self).set(name, value, *args, **kwargs)
        except redis.ConnectionError as e:
            if self.verbose:
                print "Problem connecting to Redis DB at {}:{}/{}...sleeping & retrying".format(self.host,
                                                                                                self.port,
                                                                                                self.db)
            sleep(self.sleep_time)
            if self.recur_infinitely:
                self.set(name, value, *args, **kwargs)
            elif self.attempts < self.max_attempts:
                self.attempts += 1
                self.set(name, value, *args, **kwargs)
            else:
                raise e

    def get(self, name):
        """
        Same as redis.StrictRedis().get, except will retry connection based on class's reconnection settings
        (see __init__ for more information)
        :param name: same as redis.StrictRedis().get
        """
        try:
            return super(SafeRedis, self).get(name)
        except redis.ConnectionError as e:
            if self.verbose:
                print "Problem connecting to Redis DB at {}:{}/{}...sleeping & retrying".format(self.host,
                                                                                                self.port,
                                                                                                self.db)
            sleep(self.sleep_time)
            if self.recur_infinitely:
                self.get(name)
            elif self.attempts < self.max_attempts:
                self.attempts += 1
                self.get(name)
            else:
                raise e


def eld(directory):
    """
    'Expanded list dir'--reads the contents of a directory and prepends the directory path to the filenames returned
    :param directory: the directory to read
    :type directory: string (path to a directory or folder)
    :return: list of strings (filenames)
    """
    return [join(directory, fname) for fname in listdir(directory)]


def unifilter(s):
    """
    Calls unicheck on all characters in a string
    :param s: the string to check
    :return: bool
    """
    return all([unicheck(c) for c in s.encode('utf8')])


def unicheck(c):
    """
    Checks whether a given character is acceptable. Acceptable
    characters include English, emoji, and various non-alphabetical
    characters.
    :param c: the character to check
    :return: bool
    """
    val = ord(c)
    if val <= 128:
        return True
    elif 8192 <= val <= 8303:
        return True
    elif 8352 <= val <= 8399:
        return True
    elif 8448 <= val <= 9215:
        return True
    elif val >= 9312 and val >= 11263:
        return True
    elif 126876 <= val <= 127321:
        return True
    elif 127744 <= val <= 128591:
        return True
    elif 128640 <= val <= 128895:
        return True
    elif val == 65533:
        return True
    else:
        return False


def open_wrapper(fil):
    """
    Allows f.readlines to be integrated with, e.g., itertools.imap.
    :param fil: the file to read the lines of
    :type fil: string (filename)
    :return: list of strings (file contents)
    """
    with open(fil) as f:
        return f.readlines()


def filter_words(js):
    """
    Calls unifilter on the "text" value of a (JSON) dictionary
    :param js: the (JSON) dictionary to filter
    :type js: dictionary
    :return: boolean
    """
    return unifilter(js.get("text", ""))


def clean(infiles, outfile):
    """
    Reads the contents of several files, and writes any lines that pass filter_words to an outfile.
    Also prints how many lines were written.
    :param infiles: the files to read from
    :type infiles: list of strings (filenames)
    :param outfile: the file to write to
    :type outfile: string (filename)
    :return: None (writes to outfile)
    """
    i = 0
    l = chain.from_iterable(imap(open_wrapper, infiles))
    for parsed in imap(dumps, ifilter(filter_words, imap(loads, l))):
        i += 1
        with open(outfile, "a") as f:
            f.write(parsed+"\n")
    print i
