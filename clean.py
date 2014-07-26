#coding=utf8
__author__ = 'Sam Raker'

from itertools import ifilter, imap
from json import dumps, loads


from write_words import unifilter


def open_wrapper(fil):
    with open(fil) as f:
        return f.readlines()


def filter_words(js):
    return unifilter(js.get("text", ""))


def clean():
    i = 0
    with open("tweets_01_14.json") as f:
        l = f.readlines()
    for parsed in imap(dumps, ifilter(filter_words, imap(loads, l))):
        i += 1
        with open("all_tweets.json", "a") as f:
            f.write(parsed+"\n")
    print i


if __name__ == "__main__":
    clean()