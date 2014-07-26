#coding=utf8
__author__ = 'Sam Raker'

import json
from parsed import ParsedTweet, ParsedUser


def tweets_from_json(fname):
    """
    Reads a JSON file containing 1 tweet (as JSON) or serialized ParsedTweet per line and converts the contents
    into ParsedTweet objects.
    :param fname: path to the JSON file to read
    :type fname: string
    :return: list of ParsedTweet objects
    """
    parsed_tweets = []
    with open(fname) as f:
        for x in f.readlines():
            js = json.loads(x)
            if len(js) == 2:
                parsed_tweets.append(ParsedTweet(js[0],js[1]))
            else:
                parsed_tweets.append(ParsedTweet(js=js))
    return parsed_tweets


def users_from_json(fname):
    """
    Reads a JSON file containing 1 user (as JSON) or serialized ParsedUser per line and converts the contents
    into ParsedUser objects.
    :param fname: path to the JSON file to read
    :type fname: string
    :return: list of ParsedUser objects
    """
    with open(fname) as f:
        return [ParsedUser(json.loads(x)) for x in f.readlines()]


def tweet_gen_from_json(fname, tokenize=None, parse_user=True, unshorten=True):
    """
    Reads a JSON file containing 1 tweet (as JSON) or serialized ParsedTweet per line and returns
    a generator that converts the files contents into ParsedTweet objects.
    :param fname: path to the JSON file to read
    :type fname: string
    :return: generator function
    """
    def tweet_gen(fname):
        i = 0
        with open(fname) as f:
            unparsed = f.readlines()
        while i < len(unparsed):
            try:
                yield ParsedTweet(json.loads(unparsed[i]), tokenize, parse_user, unshorten)
                i += 1
            except ValueError:
                continue
    return tweet_gen(fname)


def user_gen_from_json(fname, unshorten=True):
    """
    Reads a JSON file containing 1 tweet (as JSON) or serialized ParsedUser per line and returns
    a generator that converts the files contents into ParsedUser objects.
    :param fname: path to the JSON file to read
    :type fname: string
    :return: generator function
    """
    def user_gen(fname):
        i = 0
        with open(fname) as f:
            unparsed = f.readlines()
        while i < len(unparsed):
            try:
                yield ParsedTweet(json.loads(unparsed[i]), unshorten)
                i += 1
            except ValueError:
                continue
    return user_gen(fname)
