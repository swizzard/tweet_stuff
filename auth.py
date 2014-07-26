#coding=utf-8
__author__ = 'Sam Raker'

import os

import requests
from requests_oauthlib import OAuth1

_AUTH = None


def set_AUTH(token, token_secret, consumer_key, consumer_secret):
    """
    Creates and validates a twitter OAuth object from the credentials provided.
    :param token: your token
    :type token: string
    :param token_secret: your token secret
    :type token_secret: string
    :param consumer_key: your consumer key
    :type consumer_key: string
    :param consumer_secret: your consumer secret
    :type consumer_secret: string
    :returns: None
    See https://dev.twitter.com/ for more information.
    """
    _auth = OAuth1(consumer_key, consumer_secret, token, token_secret)
    r = requests.head("https://api.twitter.com/1.1/statuses/home_timeline.json", auth=_auth)
    r.raise_for_status()
    r.close()
    global _AUTH
    _AUTH = _auth

def auth_from_env():
    """
    Attempts to retrieve authorization credentials from environment variables, and,
    if found, calls set_auth.T
    """
    TOKEN = os.environ.get("TWITTER_TOKEN", -1)
    if TOKEN == -1:
        print """TWITTER_TOKEN environment variable not found.
        Please supply it manually, or set it via the command line"""
    TOKEN_SECRET = os.environ.get("TWITTER_TOKEN_SECRET", -1)
    if TOKEN_SECRET == -1:
        print """TWITTER_TOKEN_SECRET environment variable not found.
        Please supply it manually, or set it via the command line"""
    CONSUMER_KEY = os.environ.get("TWITTER_CONSUMER_KEY", -1)
    if CONSUMER_KEY == -1:
        print """TWITTER_CONSUMER_KEY environment variable not found.
        Please supply it manually, or set it via the command line."""
    CONSUMER_SECRET = os.environ.get("TWITTER_CONSUMER_SECRET", -1)
    if CONSUMER_SECRET == -1:
        print """TWITTER_CONSUMER_SECRET environment variable not found.
        Please supply it manually, or set it via the command line."""
    if TOKEN != -1 and TOKEN_SECRET != -1 and CONSUMER_KEY != -1 and CONSUMER_SECRET != -1:
        set_AUTH(TOKEN, TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET)


auth_from_env()
