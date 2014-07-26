#coding=utf8
__author__ = 'Sam Raker'

from functools import partial
from itertools import ifilter, imap, islice
from json import loads
import re
from time import sleep

import requests
from requests_oauthlib import OAuth1

from parsed import ParsedTweet
from auth import _AUTH

if not _AUTH:
    print "authorization error! Please check your settings or set your authorization manually."


class Twitterizer(object):
    """
    Base class for Search and Scrape. Implements OAuth authorization, a generator that
    turns twitter JSON responses into ParsedTweet objects (see parsed_tweet.ParsedTweet
    for more information), and .filter_tweets.
    The last of these relies on a number of tests (see below) that ensure only tweets
    meeting specific requirements are allowed through.
    The class is designed to be flexible and extensible, with any number of tests being
    allowed. User-defined tests must meet the following criteria:
        1) They take a tweet object as their first (non-'self') argument. This is a
        dictionary as returned via twitter's implementation of the Twitter API.
        See http://mike.verdone.ca/twitter/ for more information.
        2) They return a boolean
        3) They include variable keyword parameters (**kwargs)
        NB: tests to be used with Scrape should probably be wrapped in try/except
        in case a tweet lacks a certain key (most commonly 'text' in case of deletions,
        etc.)
    """
    def __init__(self, _auth=None):
        """
        :param _auth: Twitter OAuth authorization. See documentation under tools.auth for
        more information.
        :type _auth: function
        """
        self.__auth__ = _auth or _AUTH or OAuth1("", "", "", "")
        self.tweets = {}
        self.saved_search_meta = {}
        self.to_censor = ["nigga", "nigger", "shit", "damn", "fuck", "cock", "twat", "slut", "pussy"]
        self.unames_pat = re.compile(r'@[\w\d]+')

    def unifilter(self, s):
        return all([self.unicheck(c) for c in s.encode("utf8")])

    def unicheck(self, c):
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

    def curse_out(self, s):
        """
        Filters out tweets with bad words (as listed in .to_censor) in them.
        :param s: the text to censor
        :return: boolean
        """
        for x in self.to_censor:
            if x in s.lower():
                return False  # fails the test
        return True

    def _exist_test(self, tweet):
        """
        Checks if a tweet is None
        :param tweet: the tweet to filter
        :return: boolean
        """
        if tweet:
            return True
        else:
            return False

    def _filter_test(self, tweet):
        """
        Checks if a tweet passes tools.filter._unifilter (q.v.)
        :param tweet: the tweet to filter
        :type tweet: dictionary
        """
        try:
            if self.unifilter(tweet['text']):
                return True
            else:
                return False
        except KeyError:
            return False

    def _censor_test(self, tweet):
        """
        Checks whether a tweet's text passes .curse_out (q.v)
        :param tweet: the tweet to check
        :type tweet: dictionary
        """
        try:
            if self.curse_out(tweet['text']):
                return True
            else:
                return False
        except KeyError:
            return False

    def _hash_test(self, tweet):
        """
        Checks whether the tweet has hashtags
        :param tweet: the tweet to check
        :type tweet: dictionary
        :return: boolean

        """
        try:
            if tweet['entities']['hashtags']:
                return True
            else:
                return False
        except KeyError:
            return False

    def _text_test(self, tweet):
        """
        Checks whether the tweet has text
        :param tweet: the tweet to check
        :type tweet: dictionary
        """
        if 'text' in tweet.keys():
            return True
        else:
            return False

    def _url_test(self, tweet):
        """
        Checks whether there are urls in the tweet
        :param tweet: the tweet to check
        :type tweet: dictionary
        """
        try:
            if len(tweet['entities']['urls']) > 0:
                return True
            else:
                return False
        except KeyError:
            return False

    def _unames_test(self, tweet, q):
        """
        Checks whether the query exists outside usernames.
        :param tweet: the tweet to check
        :type tweet: unparsed tweet object
        :param q: the search query
        :type q: string
        :return: boolean
        """
        tweet_text = tweet['text']
        text = re.sub(self.unames_pat, '', tweet_text)
        if q in text:
            return True
        else:
            return False

    def filter_tweet(self, tweet, suite=True, tests=None):
        """
        Filters a tweet using the underscored helper methods above and separates the tweet into (text,metadata) tuples
        :param tweet: the tweet to filter
        :type tweet: dict
        :param suite: whether to include the standard test suite (_censor_test, _filter_test, _hash_test, _text_test)
        :type suite: bool
        :param tests: any additional tests to use
        :type tests: list of test functions (see note on test functions above) or None
        :param test_kwargs: keyword arguments to pass to the tests
        """
        if tweet:
            tests = tests or []
            if suite:
                tests += [self._censor_test, self._filter_test, self._hash_test, self._text_test, ]
            if all([test(tweet) for test in tests]):
                return True
        return False

    def parse_generator(self, tweets):
        """
        Yields ParsedTweet objects from a list of unparsed tweets.
        :param tweets: a list of unparsed tweets
        :type tweets: a list of unparsed tweet objects
        :return: iterator of ParsedTweet object(s) (see parsed_tweet.ParsedTweet for more information)
        """
        return imap(ParsedTweet, tweets)


class Search(Twitterizer):
    """
    Child class of Twitterizer that interacts with the Search API
    For more information, see documentation for Twitterizer
    """
    def __init__(self, _auth=None):
        """
        :param _auth: your Twitter authorization. See also documentation under Twitterizer and
        auth.set_auth
        :type _auth: requests_oauthlib.OAuth1 object
        """
        super(Search, self).__init__(_auth)
        self.url = "https://api.twitter.com/1.1/search/tweets.json"

    def search(self, q, suite=True, tests=None, ignore_unames=True, minim=20, as_parsed=True,
               verbose=True):
        """
        Searches Twitter for a term. Uses cursoring (see
        https://dev.twitter.com/docs/working-with-timelines for more information.)
        :param q: the term to search for
        :type q: str
        :param suite: whether to include the "standard suite" of filter tests (see
        .filter_test for more information)
        :type suite: bool
        :param tests: tests to implement
        :type tests: list of functions
        :param ignore_unames: whether to implement ._unames_test (q.v.)
        :type ignore_unames: bool
        :param minim: the minimum number of tweets to return
        :type minim: int
        :param as_parsed: whether to return the retrieved tweets as a list of unparsed dictionaries (False),
        or a .parse_generator created therefrom.
        :type as_parsed: bool
        :param verbose: whether to print the number of results
        :type verbose: bool
        :return: list of dicts or .generator
        NB: kwargs passed to this function will be passed to both the filter tests and to
        the Twitter API call. See https://dev.twitter.com/docs/api/1.1/get/search/tweets
        for more information
        """
        tests = tests or []
        if ignore_unames:
            unames_test = partial(self._unames_test, q=q)
            tests.append(unames_test)

        filter_partial = partial(self.filter_tweet, suite=suite, tests=tests)

        def fil(raw_tweets):
            """
            Filters the tweets
            :param raw_tweets: the tweets to filter
            :type raw_tweets: list of JSON strings as returned by the Twitter API
            :return: (list of JSON strings, int, int) tuple
            """
            max_id = min([long(tweet["id_str"]) for tweet in raw_tweets]) - 1
            since_id = max([long(tweet["id_str"]) for tweet in raw_tweets])
            returned = list(ifilter(filter_partial, raw_tweets))
            return returned, max_id, since_id

        count = min([minim, 100])
        payload = {"q": q, "count": count}
        req = requests.get(self.url, auth=self.__auth__, params=payload)
        req.raise_for_status()
        search = req.json()
        tweets = search["statuses"]
        results, max_id, since_id = fil(tweets)
        while len(results) < minim and max_id > 0:
            sleep(120)
            payload.update({"max_id": max_id, "since_id": since_id})
            req = requests.get(url=self.url, auth=self.__auth__, params=payload)
            req.raise_for_status()
            search = req.json()
            tweets = search["statuses"]
            filtered = fil(tweets)
            results += filtered[0]
            max_id = filtered[1]
            since_id = filtered[2]
        if verbose:
            print "{0} results".format(len(results))
        if as_parsed:
            return self.parse_generator(results)
        else:
            return results


class Scrape(Twitterizer):
    """
    Child class of Twitterizer that interacts with the Streaming API. Note that unlike
    the Search class, this class lacks any storage functionality, and so the data scraped
    from the Streaming API must be used immediately. This class allows for multiple
    streams and multiple samples
    """
    def __init__(self, _auth=None):
        """
        :param _auth: your twitter authentication. See the documentation under Twitterizer and
        auth.set_auth
        :type _auth: requests_oauthlib.OAuth1 object
        """
        super(Scrape, self).__init__(_auth)

    def get_tweets(self, limit=20, suite=True, tests=None, as_gen=True):
        """
        Retrieve tweets from a sample.
        :param limit: the maximum number of tweets to return at once
        :type limit: integer
        :param suite: See documentation under Twitterizer, above
        :type suite: boolean
        :param tests: additional tests to pass to filter_tweet
        :type tests: list of test functions (see documentation for Twitterizer)
        :param as_gen: whether to return an iterator of unparsed tweets (False) or a
        Twitterizer.parse_generator created therefrom
        :type as_gen: boolean
        :return: list of unparsed tweets, or .parse_generator
        """
        filter_partial = partial(self.filter_tweet, suite=suite, tests=tests)
        req = requests.get(url="https://stream.twitter.com/1.1/statuses/sample.json", auth=self.__auth__, stream=True)
        try:
            req.raise_for_status()
            iter_ = req.iter_lines()
            tw = ifilter(filter_partial, imap(loads, iter_))
            if as_gen:
                return self.parse_generator(islice(tw, limit))
            else:
                return islice(tw, limit)
        except requests.exceptions.RequestException as e:
            print e
