#coding=utf8
__author__ = 'Sam Raker'

from functools import partial
from itertools import chain, imap
from json import dumps, loads
import re
from urllib2 import HTTPError, URLError

import requests
from dateutil.parser import parse
from nltk.tokenize import wordpunct_tokenize

from feature_extraction.freq_splitter import split_text
from tools import eld


class Extractor(object):
    """
    A class to extract relevant information from JSON representations of tweets.
    """
    def __init__(self, fnames=None, folder=None):
        """
        :param fnames: list of JSON files to process
        :type fnames: list of strings (file names)
        :param folder: path to a folder containing JSON files to process
        :type folder: string
        """
        self.fnames = []
        if fnames:
            self.fnames += fnames
        if folder:
            self.fnames += eld(folder)
        self.domain_pat = re.compile(r'https?://([\w\d\.\-]+\.\w{2,3})')
        self.clean_pat = re.compile(r'(@|#|http)\S+')
        self.parsed = []
        self.tweets = []

    def parse_created(self, time):
        """
        Parses a string representation of a time.
        :param time: the time to parse
        :type time: string
        :return: (int, int) tuple
        """
        try:
            date = parse(time)
            hour = date.hour
            if date.minute > 30:
                hour += 1
            day_of_week = date.weekday()
            return day_of_week, hour
        except Exception as e:
            print e
            return -1, -1

    def extract_tweet(self, tweet, splitter=None):
        """
        Extracts relevant tweet-related information from a tweet.
        :param tweet: the tweet to process
        :type tweet: dict
        :param splitter: tokenizing function. Defaults to nltk.tokenize.wordpunct_tokenize (q.v.)
        :return: (string, dict) tuple
        """
        d = {"hashtags": [], "split_hashtags": [], "urls": [], "domains": [], "day": -1, "hour": -1, "is_weekday": -1,
             "words": [], "mentions": [], "user": ""}
        splitter = splitter or wordpunct_tokenize
        cleaned_text = re.sub(self.clean_pat, "", tweet.get("text", ""))
        self.tweets.append(tweet)
        d["words"] = splitter(cleaned_text)
        entities = tweet.get("entities", {})
        d["hashtags"] = [hashtag.get("text", "") for hashtag in entities.get("hashtags", [])]
        d["user"] = tweet.get("user", {}).get("id_str", "")
        d["mentions"] = [user.get("id_str", "") for user in entities.get("user_mentions", [])]
        d["split_hashtags"] = [split_text(hashtag)[1] for hashtag in d["hashtags"]]
        urls = entities.get("urls")
        for url in urls:
            try:
                r = requests.get(url)
                d["urls"].append(r.url)
            except (requests.RequestException, HTTPError, URLError, TypeError):
                d["urls"].append(url.get("expanded_url", url.get("display_url", url.get("url", ""))))
        for url in d["urls"]:
            m = re.match(self.domain_pat, url)
            if m:
                d["domains"].append(m.group(1))
            else:
                d["domains"].append(None)
        d["day"], d["hour"] = self.parse_created(tweet.get("created_at"))
        if d["day"] != -1:
            if d["day"] > 4:
                d["is_weekday"] = 1
            else:
                d["is_weekday"] = 0
        return tweet.get("id_str"), d

    def extract_user(self, tweet):
        """
        Extracts relevant user-related information from a tweet.
        :param tweet: the tweet to process
        :type tweet: dict
        :return: dict
        """
        d = {"following": 0, "followers": 0, "follow_ratio": 0.0, "urls": [], "domains": [], "offset": 0}
        user = tweet.get("user", {})
        d["following"] = user.get("friends_count", 1)
        if d["following"] == 0:
            d["following"] = 1
        d["followers"] = user.get("followers_count", 0)
        d["follow_ratio"] = float(d["followers"]) / d["following"]
        urls = user.get("entities", {}).get("urls", [])
        for url in urls:
            try:
                r = requests.get(url)
                d["urls"].append(r.url)
            except (requests.RequestException, HTTPError, URLError):
                d["urls"].append(url.get("expanded_url", url.get("display_url", url.get("url", ""))))
        for url in d["urls"]:
            m = re.match(self.domain_pat, url)
            if m:
                d["domains"].append(m.group(1))
            else:
                d["domains"].append(None)
        d["offset"] = user.get("utc_offset", -1)
        return d

    def extract(self, tweet, splitter):
        """
        Calls both .extract_tweet and .extract_user on a tweet
        :param tweet: the tweet to process
        :type tweet: dict
        :param splitter: tokenization function. See .extract_tweet for more information
        :return: (string, (dict, dict)) tuple
        """
        t = self.extract_tweet(tweet, splitter)
        u = self.extract_user(tweet)
        return t[0], (t[1], u)

    def open_wrapper(self, fil):
        """
        Opens a file and returns its lines as a list
        :param fil: the file to open
        :return: list of strings
        """

        with open(fil) as f:
            return f

    def parse(self, splitter=None):
        """
        Parses the files represented by the file names in .fnames
        :param splitter: tokenization function. See .extract_tweet for more information
        :return: None (appends to .parsed)
        """
        parse_partial = partial(self.extract, splitter=splitter)
        for parsed in imap(parse_partial, imap(loads, chain.from_iterable(imap(self.open_wrapper, self.fnames)))):
            self.parsed.append(parsed)

    def write_parse(self, dest, splitter=None):
        """
        Parses the files represented by the file names in .fnames and writes them to dest
        :param dest: the file to write the extracted information to
        :type dest: string (filename)
        :param splitter: tokenization function. See .extract_tweet for more information
        :return: None (writes JSON strings to a file)
        """
        extract_partial = partial(self.extract, splitter=splitter)
        it = imap(extract_partial, imap(loads, chain.from_iterable(imap(open, self.fnames))))
        tweet_counter = 0
        file_counter = 1
        if dest[-5:] == ".json":
            dest_template = dest[:-5]
        else:
            dest_template = dest
        while True:
            try:
                to_write = it.next()
                tweet_counter += 1
                if tweet_counter % 5000 == 0:
                    file_counter += 1
                with open("{0}_{1}.json".format(dest_template, file_counter), "a") as f:
                    f.write(dumps(to_write) + "\n")
            except StopIteration:
                break
        print "{0} results written to {1} files".format(tweet_counter, file_counter)
