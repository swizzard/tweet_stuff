# coding=utf8
__author__ = 'Sam Raker'

from json import loads
from os import environ
import re

import MySQLdb

from tools import SafeRedis, eld


class Inserter(object):
    """
    Class to handle insertion of twitter data into the database.
    NB: tweet ids and user ids are 18- and 9-digit integers, respectively. These values are represented as strings in the
    data, and treated as such in the code, but are translated into bigints by MySQLdb.
    """

    def __init__(self, use_testdb=False, show_sql=True):
        """
        Initialize the Inserter.
        :param test: whether to use the test db/Redis settings
        :type test: bool
        """
        if use_testdb:
            db_settings = {'host': 'localhost',
                           'db': 'tweets_test',
                           'user': 'samuelraker',
                           'passwd': environ.get('TWEETS_TESTDB_PASSWORD')}
            redis_settings = {'host': 'localhost',
                              'db': '0'}
        else:
            db_settings = {'host': 'localhost',
                           'db': 'twitter',
                           'user': 'samuelraker',
                           'passwd': environ.get('TWEETS_DB_PASSWORD')}
            redis_settings = {'host': 'localhost',
                              'db': '2'}
        self.show_sql = show_sql
        self.DB = MySQLdb.connect(**db_settings)
        self.cursor = self.DB.cursor()
        self.cache = SafeRedis(**redis_settings)
        for table in ('cluster', 'hashtag', 'tag_word', 'url', 'word'):
            key = 'pk_{table}'.format(table=table)
            if self.cache.get(key) is None:
                self.cache.set(key, 0)
        self.escape_word = self.DB.escape

    def get_or_set_pk(self, table, val, get_only=False):
        """
        Try to retrieve the primary key of a datum from the Redis cache. If none is found, increment the cached pk
        counter for the table in question and use that.
        :param table: the db table the entry is going to be added to
        :type table: str (one of 'cluster', 'hashtag', 'hashtag_to_cluster', 'tag_word', 'tag_word_to_hashtag', 'url',
            'url_to_tweet', 'user_to_tweet', 'word', 'word_to_tweet')
        :param val: the value in question
        :type val: str, probably
        :param get_only: disable creation of new pks, raising an error if the value doesn't already have a pk in the cache
        :type get_only: bool
        :return: int
        """
        key = '{table}_{val}'.format(table=table, val=val[:355])
        cached_pk = self.cache.get(key)
        if cached_pk is not None:
            return int(cached_pk)  # redis-py returns strings by default
        else:
            if get_only:
                raise ValueError("No primary key found for value {val} for table {table}".format(val=val, table=table))
            new_pk = self.cache.incr('pk_{table}'.format(table=table))  # .incr increments the value by 1 and returns the result as an int
            self.cache.set(key, new_pk)
            return new_pk

    def insert_tweet_data(self, tid, hour, day, is_weekday):
        """
        Insert all tweet-related data. NB: this only inserts data for the 'tweet' column, NOT all the data about a
        tweet.
        :param id: the id of the tweet
        :type id: str
        :param hour: the hour of the day the tweet was tweeted
        :type hour: int (0-23)
        :param day: the day of the week the tweet was tweeted
        :type day: int (0-7)
        :param is_weekday: whether the tweet was tweeted on a weekday
        :type is_weekday: int (0 or 1)
        :return: None
        """
        if hour == "-1":
            hour = "NULL"
        if day == "-1":
            day = "NULL"
        if is_weekday == "-1":
            is_weekday = "NULL"
        try:
            tweet_insert_command = """
                    INSERT INTO `tweet` (tweet_id, hour, day, is_weekday)
                    VALUES({id},{hour},{day},{is_w})
                    ON DUPLICATE KEY UPDATE tweet_id={id}, hour={hour}, day={day}, is_weekday={is_w}
                """.format(id=tid, hour=hour, day=day, is_w=is_weekday)
            if self.show_sql:
                print tweet_insert_command
            self.cursor.execute(tweet_insert_command)
        except MySQLdb.IntegrityError:
            print "Tweet with id {tid} already exists".format(tid=tid)

    def insert_mention(self, tweet_id, user_id):
        """
        Insert mentions. Per this schema, a mention is the same as a user tweeting a tweet, except 'is_mention' is set
        to 1 (i.e., True).
        :param tweet_id: the id of the tweet
        :type tweet_id: str
        :param user_id: the id of the user mentioned in the tweet
        :type user_id: str
        :return: None
        """
        add_user_command = """
            INSERT IGNORE INTO `twitter_user` (user_id) VALUES({user_id})
            """.format(user_id=user_id)
        if self.show_sql:
            print add_user_command
        self.cursor.execute(add_user_command)
        
        add_tweet_command = """
            INSERT IGNORE INTO `tweet` (tweet_id) VALUES({tweet_id})
            """.format(tweet_id=tweet_id)
        if self.show_sql:
            print add_tweet_command
        self.cursor.execute(add_tweet_command)
        
        mention_insert_command = """
                INSERT INTO `user_to_tweet` (tweet_id, user_id, is_mention)
                VALUES({tid},{uid},{is_m});""".format(tid=tweet_id, uid=user_id, is_m=1)
        if self.show_sql:
            print mention_insert_command
        self.cursor.execute(mention_insert_command)
        

    def insert_hashtag(self, hashtag_str, tweet_id):
        """
        Insert hashtag-related data.
        :param hashtag_str: the text of the hashtag
        :type hashtag_str: str
        :param tweet_id: the id of the tweet the hashtag came from
        :type tweet_id: str
        :return: int (primary key of hashtag)
        """
        hashtag_pk = self.get_or_set_pk('hashtag', hashtag_str)
        add_tweet_command = """
            INSERT IGNORE INTO `tweet` (tweet_id) VALUES({tweet_id})
            """.format(tweet_id=tweet_id)
        if self.show_sql:
            print add_tweet_command
        self.cursor.execute(add_tweet_command)
        
        try:
            hashtag_insert_command = """
                    INSERT INTO `hashtag` (id, str)
                    VALUES({id}, '{h_str}');""".format(id=hashtag_pk, h_str=self.escape_word(hashtag_str))
            if self.show_sql:
                print hashtag_insert_command
            self.cursor.execute(hashtag_insert_command)
            
        except MySQLdb.IntegrityError:
            if self.show_sql:
                print "Hashtag {ht} already in DB...skipping...".format(ht=self.escape_word(hashtag_str))
        hashtag_to_tweet_insert_command = """
              INSERT INTO `hashtag_to_tweet` (hashtag_id, tweet_id) VALUES({hid}, {tid})
            """.format(hid=hashtag_pk, tid=tweet_id)
        if self.show_sql:
            print hashtag_to_tweet_insert_command
        self.cursor.execute(hashtag_to_tweet_insert_command)
        
        return hashtag_pk

    def insert_tag_word(self, tag_word, hashtag_id):
        """
        Insert data about a word contained in a hashtag.
        :param tag_word: the word
        :type tag_word: str
        :param hashtag_id: primary key of the hashtag the word came from
        :type hashtag_id: int
        :return: None
        """
        tag_word_pk = self.get_or_set_pk('tag_word', tag_word)
        add_hashtag_command = """
            INSERT IGNORE INTO `hashtag` (id) VALUES({hashtag_id})
            """.format(hashtag_id=hashtag_id)
        if self.show_sql:
            print add_hashtag_command
        self.cursor.execute(add_hashtag_command)
        
        try:
            tag_word_insert_command = """
                    INSERT INTO `tag_word` (id, str)
                    VALUES({id}, '{tw_str}');""".format(id=tag_word_pk, tw_str=tag_word)
            if self.show_sql:
                print tag_word_insert_command
            self.cursor.execute(tag_word_insert_command)
            
        except MySQLdb.IntegrityError:
            if self.show_sql:
                print """Tag word {tw} already in DB...skipping...""".format(tw=tag_word)
        tag_word_to_hashtag_insert_command = """
                INSERT INTO `tag_word_to_hashtag` (tag_word_id, hashtag_id)
                VALUES({wid}, {hid});""".format(wid=tag_word_pk, hid=hashtag_id)
        if self.show_sql:
            print tag_word_to_hashtag_insert_command
        self.cursor.execute(tag_word_to_hashtag_insert_command)
        

    def insert_twitter_user(self, user_id, follow_ratio, followers, following, offset):
        """
        Insert data about a twitter user.
        :param user_id: the user's id
        :type user_id: str
        :param follow_ratio: the ratio of users the user follows / users the user is followed by
        :type follow_ratio: float
        :param followers: the number of users following this user
        :type followers: int
        :param following: the number of users this user follows
        :type following: int
        :param offset: the user's offset from UTC
        :type offset: int or NULL
        :param tweet_id: the id of the tweet the user tweeted
        :type tweet_id: str
        :return: None
        """
        try:
            offset = int(offset)
        except TypeError:
            offset = "NULL"
        try:
            user_insert_command = """
                    INSERT INTO `twitter_user` (user_id, follow_ratio, followers, following, offset)
                    VALUES({id}, {ratio}, {ers}, {ing}, {off})
                    ON DUPLICATE KEY UPDATE user_id={id}, follow_ratio={ratio}, followers={ers}, following={ing},
                    offset={off};
                """.format(id=user_id, ratio=follow_ratio if (isinstance(followers, int) and followers >= 0) else "NULL",
                           ers=followers if (isinstance(followers, int) and followers >= 0) else "NULL",
                           ing=following if (isinstance(following, int) and following >= 0) else "NULL", off=offset)
            if self.show_sql:
                print user_insert_command
            self.cursor.execute(user_insert_command)
            
        except MySQLdb.IntegrityError:
            if self.show_sql:
                print "User with id {uid} already exists in DB...skipping...".format(uid=user_id)

    def insert_url(self, url, domain, tweet_id=None, user_id=None, user_url=False):
        """
        Insert data about a URL. URLs are found in one of two places: the body of the tweet itself, or in the profile of
        the user who tweeted the tweet. This method dispatches the appropriate method in either situation.
        :param url: the url
        :type url: str
        :param domain: the url's domain
        :type domain: str
        :param tweet_id: the id of the tweet the url appears in
        :type tweet_id: str or None
        :param user_id: the id of the user in whose profile the url occurs
        :type user_id: str or None
        :param user_url: whether the url occurs in a user's profile
        :type user_url: bool
        :return: None
        """
        url_pk = self.get_or_set_pk('url', url)
        if "'" in url:
            url_tpl = '"{url_str}"'
        else:
            url_tpl = "'{url_str}'"
        if tweet_id is not None:
            add_tweet_command = """
                INSERT IGNORE INTO `tweet` (tweet_id) VALUES({tweet_id})""".format(tweet_id=tweet_id)
            if self.show_sql:
                print add_tweet_command
            self.cursor.execute(add_tweet_command)
            
        if user_id is not None and user_url:
            add_user_command = """
                INSERT IGNORE INTO `twitter_user` (user_id) VALUE({user_id})""".format(user_id=user_id)
            if self.show_sql:
                print add_user_command
            self.cursor.execute(add_user_command)
            
        try:
            url_insert_command = """
                    INSERT INTO `url` (id, str, domain)
                    VALUES({url_id},{url_tpl},'{domain}');""".format(url_id=url_pk,
                                                                       url_tpl=url_tpl.format(url_str=self.escape_word(url)),
                                                                       domain=self.escape_word(domain))
            if self.show_sql:
                print url_insert_command
            self.cursor.execute(url_insert_command)
            
        except MySQLdb.IntegrityError:
            if self.show_sql:
                print """URL {url} already exists in DB...skipping...""".format(url=self.escape_word(url))
        if user_url:
            self.insert_user_url(user_id, url_pk)
        else:
            self.insert_tweet_url(tweet_id, url_pk)

    def insert_user_url(self, user_id, url_pk):
        """
        Insert user id and url pk into user_to_url table. Don't call this directly.
        :param user_id: the id of the user in whose profile the url occurs
        :type user_id: str
        :param url_pk: the primary key of the url
        :type url_pk: int
        :return: None
        """
        if not user_id:
            raise ValueError('Must specify user_id')
        else:

            user_url_insert_command = """
                INSERT INTO `user_to_url` (user_id, url_id)
                VALUES({user_id},{url_id});""".format(user_id=user_id, url_id=url_pk)
            if self.show_sql:
                print user_url_insert_command
            self.cursor.execute(user_url_insert_command)
            

    def insert_tweet_url(self, tweet_id, url_pk):
        """
        Insert tweet id and url pk into url_to_tweet table. Don't call this directly.
        :param tweet_id:
        :param url_pk:
        :return: None
        """
        if not tweet_id:
            raise ValueError('Must specify tweet_id')
        else:
            tweet_url_insert_command = """
                INSERT INTO `url_to_tweet` (tweet_id, url_id)
                VALUES({tweet_id},{url_id});""".format(tweet_id=tweet_id, url_id=url_pk)
            if self.show_sql:
                print tweet_url_insert_command
            self.cursor.execute(tweet_url_insert_command)
            

    def insert_word(self, word_str, tweet_id):
        """
        Insert data about a word.
        :param word_str: the word
        :type word_str: str
        :param tweet_id: the id of the tweet the word was found in
        :type tweet_id: str
        :return: None
        """
        word_pk = self.get_or_set_pk('word', word_str)
        word_str = word_str.replace("'", "[Q]").replace('"', "[QQ]")
        if "\\" in word_str:
            word_str = word_str.replace("\\", "\\\\")
        add_tweet_command = """
            INSERT IGNORE INTO `tweet` (tweet_id) VALUES({tweet_id})""".format(tweet_id=tweet_id)
        if self.show_sql:
            print add_tweet_command
        self.cursor.execute(add_tweet_command)
        try:
            word_insert_command = """
                    INSERT INTO `word` (id, str)
                    VALUES({w_pk}, '{w_str}');""".format(w_pk=word_pk, w_str=word_str)
            if self.show_sql:
                print word_insert_command
            self.cursor.execute(word_insert_command)
        except MySQLdb.IntegrityError:
            if self.show_sql:
                print "Word {word} already exists in DB...skipping...".format(word=word_str)
        except MySQLdb.ProgrammingError:
            return None
        word_to_tweet_insert_command = """
                INSERT INTO `word_to_tweet` (word_id, tweet_id) VALUES({wid}, {tid})
                        """.format(wid=word_pk, tid=tweet_id)
        if self.show_sql:
            print word_to_tweet_insert_command
        self.cursor.execute(word_to_tweet_insert_command)
        

    def process_json(self, js):
        """
        Process a JSON representation of a tweet and insert all the relevant information into the database. Also inserts
        user_to_tweet data.
        :param js: JSON representation of a tweet
        :type js: list
        :return: None
        """
        tweet_id = js[0]
        user_id = js[1][0]['user']
        self.process_tweet(tweet_id, js[1][0])
        self.process_user(user_id, js[1][1])
        user_to_tweet_insert_command = """
                INSERT INTO `user_to_tweet` (user_id, tweet_id, is_mention)
                VALUES({uid}, {tid}, {is_m});""".format(uid=user_id, tid=tweet_id, is_m=0)
        if self.show_sql:
            print user_to_tweet_insert_command
        self.cursor.execute(user_to_tweet_insert_command)
        

    def process_tweet(self, tweet_id, tweet_data):
        """
        Process the tweet data.
        :param tweet_id: the tweet's id
        :type tweet_id: str
        :param tweet_data: the data extracted from the tweet
        :type tweet_data: dict
        :return: None
        """
        self.insert_tweet_data(tweet_id, tweet_data['hour'], tweet_data['day'], tweet_data['is_weekday'])
        hashtags = tweet_data.get('hashtags')
        split_hashtags = tweet_data.get('split_hashtags')
        for idx, hashtag in enumerate(hashtags):  # hashtags & split_hashtags
            hashtag_id = self.insert_hashtag(hashtag, tweet_id)
            split_hashtag = split_hashtags[idx]
            for tag_word in split_hashtag:
                self.insert_tag_word(tag_word, hashtag_id)
        urls = tweet_data['urls']
        if urls:  # not all tweet have urls
            domains = tweet_data['domains']
            for idx, url in enumerate(urls):  # urls & domains
                self.insert_url(url, domains[idx], tweet_id=tweet_id)
        for word in tweet_data['words']:  # words
            self.insert_word(word, tweet_id)

    def process_user(self, user_id, user_data):
        """
        Process the user data.
        :param user_id: the user's id
        :type user_id: str
        :param user_data: the data extracted from the user profile
        :return: None
        """
        followers = user_data['followers'] if user_data['followers'] != '-1' else "NULL"
        following = user_data['following'] if user_data['following'] != '-1' else "NULL"
        ratio = user_data['follow_ratio'] if followers != 'NULL' else 'NULL'
        self.insert_twitter_user(user_id, ratio, followers, following, user_data.get('offset', 'NULL'))
        user_urls = user_data['urls']
        if user_urls:  # not all user profiles have urls
            user_domains = user_data['domains']
            for idx, user_url in enumerate(user_urls):  # urls & domains
                self.insert_url(user_url, user_domains[idx], user_id=user_id, user_url=True)


def process_fil(fil, inserter=None, test=True):
    """
    Processes a whole file, updating the db with the data it contains
    :param fil: the file to process
    :type fil: str (filename)
    :param inserter: Inserter instance to use for processing the file. If None, one will be created.
    :type inserter: Inserter instance or None
    :param test: whether to make the Inserter instance use the test db/cache settings
    :type test: bool
    :return: None
    """
    if not inserter:
        inserter = Inserter(test)
    with open(fil) as f:
        lines = f.readlines()
    for line in lines:
        try:
            js = loads(line)
            inserter.process_json(js)
        except ValueError:
            print 'Cannot decode JSON from {line}'.format(line=line)


def process_dir(directory, use_testdb=False, show_sql=True):
    """
    Process a whole directory.
    :param directory: the directory to process
    :type directory: str (path to a directory)
    :param test: whether to make the Inserter instance use the test db/cache settings
    :param test: bool
    :return: None
    """
    inserter = Inserter(use_testdb, show_sql)
    try:
        fils = eld(directory)
        for fil in fils:
            process_fil(fil, inserter)
            print "Processed {fil}".format(fil=fil)
    finally:
        inserter.DB.commit()


def reset_db(db='test', **db_settings):
    if db == 'test':
        db_settings = {'host': 'localhost', 'db': 'tweets_test', 'user': 'samuelraker',
                       'passwd': environ.get('TWEETS_TESTDB_PASSWORD')}
        redis_settings = {'host': 'localhost', 'db': '0'}
    elif db == 'mbp2':
        db_settings = {'host': 'localhost',
                       'db': 'twitter',
                       'user': 'samuelraker',
                       'passwd': environ.get('TWEETS_DB_PASSWORD')}
        redis_settings = {'host': 'localhost', 'db': 2}
    else:
        if not db_settings:
            raise ValueError("Must supply valid db name or settings")
    cache = SafeRedis(**redis_settings)
    cache.flushdb()
    print "Flushed Redis cache"
    db = MySQLdb.connect(**db_settings)
    cursor = db.cursor()
    print 'Wiping {db_name}'.format(db_name=db)
    try:
        for table in (
                'cluster', 'hashtag', 'hashtag_to_cluster', 'hashtag_to_tweet', 'tag_word', 'tag_word_to_hashtag', 'url',
                'url_to_tweet', 'user_to_tweet', 'user_to_url', 'word', 'word_to_tweet', 'twitter_user', 'tweet'):
            cursor.execute("""DELETE FROM `{table}`;""".format(table=table))
            print "Wiped {table}".format(table=table)
    finally:
        db.commit()