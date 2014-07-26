#coding=utf-8
__author__ = 'Sam Raker'

import json
import re
from pprint import pformat

import requests

from auth import _AUTH
from feature_extraction.freq_splitter import split_text


class Parsed(object):
    """
    Base class for ParsedTweet and ParsedUser classes.
    """

    def __init__(self, js, unshorten=True):
        """
        :param js: JSON dict as returned by Twitter API
        :type js: dict
        """
        self.metadata = self.__get_meta_keys__(js)
        self.meta_keys = self.metadata.keys()
        self.urls = []
        urls = self.get_meta('entities_urls')
        if urls:
            for url in urls:
                expanded = url.get('expanded_url')
                if expanded:
                    self.urls.append(expanded)
                else:
                    tco = url.get('url')
                    if tco:
                        self.urls.append(tco)
        if unshorten:
            self.unshortened_urls = self.get_unshortened_urls()
            self.url_domains = self.get_url_domains()
        else:
            self.unshortened_urls = []
            self.url_domains = []
        self.id = self.get_meta("id_str")

    def __eq__(self, other):
        if self.id == other.id:
            return True
        else:
            return False

    def __ne__(self, other):
        if self.id == other.id:
            return False
        else:
            return True

    def __repr__(self):
        return pformat(self.metadata, indent=2, depth=4, width=40)

    def __get_meta_keys__(self, js):
        """
        The metadata dictionary returned by the Twitter API is heavily nested. This function
        flattens that dictionary and makes it easier to retrieve various parts of the metadata
        (see also .get_meta, below.)
        :param js: the twitter metadata.
        :type js: dictionary.
        :return: dictionary.
        """
        d = {}
        for k in js.keys():
            if k == "user": # keep user data in one place to pass to ParsedUser
                d[k] = js[k]
            elif isinstance(js[k], dict):
                for k2 in js[k].keys():
                    d["{0}_{1}".format(k, k2)] = js[k][k2]
                d.update(self.__get_meta_keys__(js[k]))
            else:
                d[k] = js[k]
        return d

    def get_meta(self, value=None, verbose=False):
        """
        This function can be used to retrieve any of the various parts of the twitter
        metadata.
        :param value: the metadata value to be retrieved.
        :type value: string.
        :param verbose: if True, print an alert when the metadata retrieval fails.
        :type verbose: boolean.
        :return: string, list, or dictionary, depending on the metadata in question.
        """
        if self.get('meta_keys', None):
            if value:
                try:
                    return self.metadata[value]
                except KeyError:
                    if verbose:
                        print "No value found for {}".format(value)
                    return None
            else:
                return self.meta_keys
        else:
            return None

    def get(self, value, default=None):
        """
        An implementation of the standard dictionary.get() method.
        :param value: the value to be gotten.
        :type value: string.
        :param default: the default value, to be returned if the getting fails.
        :return: string, list, or dictionary, depending on the metadata, or None.
        """
        if hasattr(self, value):
            return self.__getattribute__(value)
        else:
            if hasattr(self, 'meta_key'):
                if hasattr(self.meta_keys, 'get'):
                    return self.meta_keys.get(value, default)
            else:
                return default

    def get_unshortened_urls(self):
        """
        Uses requests to get the full URLs from a shortened (bit.ly, t.co, etc.) versions
        :return: list of strings
        """
        unshortened = []
        for url in self.urls:
            try:
                r = requests.get(url)
                unshortened.append(r.url)
            except Exception as e:
                print e
                unshortened.append(url)
        return unshortened

    def get_url_domains(self):
        """
        Extracts the domains from URLs
        :return: list of strings
        """
        domains = []
        p = re.compile(r'https?://([\w\d\.\-]+\.\w{2,3})')
        for url in self.unshortened_urls:
            m = re.match(p, url)
            if m:
                domains.append(m.group(1))
            else:
                domains.append(None)
        return domains

    def to_json(self, verbose=True):
        """
        Serializes the object to JSON.
        NB: The way I've implemented it, each Parsed object is serialized to a separate line of JSON.
        This allows one file to be appended with new Parsed JSON representations, but also means that
        one needs to decode said file line-by-line.
        :param verbose: whether to print a notice that the object is being serialized.
        :type verbose: boolean.
        :return: string representation of the JSON serialization of the object.
        """
        if verbose:
            print "serializing {}".format(self.__repr__())
        return json.dumps(self.metadata)


class ParsedTweet(Parsed):
    """
    A class that turns some salient parts of the twitter metadata into attributes,
    and also tokenizes and munges the text of the tweet.
    The various parts of the metadata that I have implemented get methods for are those relevant
    to my research. Feel free to add to/replace these methods for your own purposes!
    NB: Twitter metadata is frequently in unicode. You have been warned.
    NB: See .to_json, below, for information on serialization.
    """

    def __init__(self, js, tokenize=None, parse_user=True, unshorten=True):
        """
        :param js: the JSON representation of the tweet, as returned by the Twitter API
        :type js: dict
        :param tokenize: a tokenization function, e.g. one that takes a string and returns a list of tokens.
        The default is a simple whitespace-based tokenizer (see .__split__, below.)
        :type tokenize: function
        :param parse_user: whether to turn the user data included in the tweet JSON into a ParsedUser
        instance (see parsed.ParsedUser for more information)
        :type parse_user: bool
        """
        super(ParsedTweet, self).__init__(js, unshorten)
        self.tokenize = tokenize or self.__split__
        self.text = self.metadata.get('text', '')
        self.text = self.text.encode('utf8', 'replace').decode('ascii', 'replace')
        self.tokenized_text = self.tokenize(self.text)
        self.munge_p = re.compile(r'(@|http://(www\.)?)[\w\d\.\-\?/]+')
        self.munged_text = re.sub(self.munge_p, '\g<1>xxxxxxxx', self.text)
        self.hashtags = None
        try:
            hts = self.get_meta("entities_hashtags")
            if hts:
                self.hashtags = [ht['text'] for ht in hts]
        except KeyError:
            self.hashtags = None
        self.hashtags = self.hashtags or re.findall(r'#[\w_\d]+', self.text)
        self.split_hashes = self._split_hashes()
        if parse_user:
            self.user = ParsedUser(self.get_meta("user"))
        else:
            self.user = self.get_meta("user_id_str")
        self.created_at = self.get_meta("created_at")
        self.mentions = self._mentions() + self._ats()
        self.words = [word for word in self.tokenized_text if not re.match(r'(@|#|http)\S+', word) and any([char.isalnum() for char in word])]
        self.coordinates = self._coordinates()

    def __str__(self):
        return "<ParsedTweet: {0}: {1}>".format(self.user.screen_name, self.text)

    def __split__(self, s):
        """
        The default tokenization function. Splits a string by whitespace.
        :param s: the string to be tokenized.
        :type s: string.
        :return: list of strings.
        """
        return re.split(r'\s+', s)

    def _split_hashes(self):
        """
        Splits hashtags via feature_extraction.freq_splitter.split_text (q.v.)
        :return: list of strings
        """
        split = []
        for hashtag in self.hashtags:
            split.append(split_text(hashtag)[1])
        return split

    def _ats(self):
        """
        Pulls user mentions from the text.
        NB: it seems that in certain circumstances (e.g., "manual" retweets), Twitter fails to pick up
        on the presence of usernames in the tweet text. This method addresses that.
        :return: list of strings
        """
        ats = []
        at_iter = re.finditer(r'@([\w\d]+)', self.text)
        for at in at_iter:
            ats.append(at.group(1))
        return ats

    def _mentions(self):
        """
        Retrieves user mentions from the tweet's metadata.
        :return: list of strings
        """
        mentions = self.get_meta("entities_user_mentions")
        mention_sns = []
        for mention in mentions:
            mention_sns.append(mention["screen_name"])
        return mention_sns

    def _coordinates(self):
        """
        Gets the geolocation coordinates from the metadata.
        NB: not all tweets have such data.
        NB: the geolocation data provided by Twitter is, IMHO, a bit of a mess. There are
        sometimes multiple lists of coordinates--I'm not sure what they all represent.
        In these cases, I've made the (arbitrary) choice to use the first set.
        :return: list of strings (longitude, latitude)
        """
        if self.get_meta('coordinates'):
            coordinates = self.get_meta('coordinates')
            while isinstance(coordinates[0], list):
                coordinates = coordinates[0]
            else:
                return coordinates


class ParsedUser(Parsed):
    """
    User equivalent of ParsedTweet class, above. Like ParsedTweet, turns some salient parts of the
    user data returned by Twitter's REST API into attributes, and leaves the rest available in
    .metadata. Additional functionality includes retrieving the user's most recent tweets and
    an attempt to get the user's UTC offset and timezone.
    """

    def __init__(self, js, unshorten=True):
        """
        :param js: JSON representation of the user, as returned by Twitter's API
        :type js: dict
        :param unshorten: whether to unshorten the URLs contained in the user's profile
        :type unshorten: bool
        """
        super(ParsedUser, self).__init__(js, unshorten)
        self.created_at = self.get_meta("created_at")
        self.description = self.get_meta("description")
        self.followers_count = self.get_meta("followers_count")
        self.following_count = self.get_meta("friends_count")
        self.lang = self.get_meta("lang")
        self.location = self.get_meta("location")
        self.name = self.get_meta("name")
        self.screen_name = self.get_meta("screen_name")
        self.statuses_count = self.get_meta("statuses_count")
        self.tz = self.get_meta("time_zone")
        self.utc_offset = self._utc_offset()
        self.utc_tz = self._utc_tz()
        self.verified = self.get_meta("verified")
        self.timeline = self._timeline()

    def __str__(self):
        return "<ParsedUser: {0}>".format(self.screen_name)

    def _utc_offset(self):
        """
        If the User supplies utc_offset, return it. Otherwise, try and guess the offset
        from the created_at attribute.
        :return: int
        """
        offset = self.get_meta("utc_offset")
        if offset:
            return int(offset)
        else:
            m = re.search(r'\d{2}:\d{2}:\d{2} ((\+|-)\d{4}) \d{4}', self.created_at)
            if m:
                offset = int(m.group(1))
        return offset

    def _utc_tz(self):
        """
        Converts self.utc_offset into a numerical timezone (+/- X hours from GMT)
        :return: int or None
        """
        if self.utc_offset:
            return self.utc_offset / 3600
        else:
            return None

    def _timeline(self):
        """
        Retrieve the user's most recent tweets.
        NB: This method will retrieve AT MOST the user's 200 most recent tweets (as per the
            count parameter in the Twitter.statuses.user_timeline call.) See the information
            on the 'count' parameter at https://dev.twitter.com/docs/api/1.1/get/statuses/user_timeline
            for more information. See also https://dev.twitter.com/docs/working-with-timelines
            if you'd like to refactor this method to retrieve more tweets.
        :return: list of ParsedTweet objects or empty list
        """
        try:
            payload = {"user_id": self.id, "count": 200, "trim_user": True, "exclude_replies": True,
                       "include_rts": False}
            req = requests.get(url="https://api.twitter.com/1.1/statuses/user_timeline.json", auth=_AUTH, params=payload)
            req.raise_for_status()
            timeline = req.json()
            return [ParsedTweet(t, parse_user=False) for t in timeline]
        except requests.HTTPError as e:
            print e
            return []
