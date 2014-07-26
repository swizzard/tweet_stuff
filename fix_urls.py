#coding=utf8
__author__ = 'Sam Raker'

from contextlib import closing
import json
import os
import re
import socket

import requests
from requests import exceptions

from tools import eld, SafeRedis

ROUTER_IP = '24.186.113.22'
REDIS_HOST = '24.186.113.22'
REDIS_PORT = '6666'
REDIS_DB = 1

DOMAIN_PAT = re.compile(r'https?://([\w\d\.\-]+\.\w{2,3})')
ERR_PAT = re.compile(r'host=\'([\w\d\.]+)\'')

if os.path.exists(os.path.expanduser("~/PycharmProjects/tweet_stuff")):
    home_dir = os.path.expanduser("~/PycharmProjects/tweet_stuff")
elif os.path.exists(os.path.expanduser("~/tweet_stuff")):
    home_dir = os.path.expanduser("~/tweet_stuff")
IN_DIR = os.path.join(home_dir, "extracted2")
OUT_DIR = os.path.join(home_dir, "fixed")



CONN = SafeRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


def resolve_redirects(url):
    print "Resolving {}".format(url)
    cached = CONN.get(url)
    if cached:
        return cached
    session = requests.session()
    try:
        with closing(session.head(url, timeout=300)) as req:
            r = req
    except (exceptions.RequestException, socket.error) as e:
        try:
            requests.head('http://{}'.format(ROUTER_IP)).close()
            CONN.set(url, url)
            return url  # original url is invalid
        except (exceptions.RequestException, socket.error):
            raise e
    if not r.headers.get('location'):  # not a redirect
        CONN.set(url, url)
        return url
    tmp_url = url
    try:
        redir = r
        for redir in session.resolve_redirects(r, r.request, timeout=300):
            if redir.status_code == 200 and not (('domainnotfound' in redir.url) or ('http' not in redir.url)):
                return redir.url  # return a valid end
            else:
                tmp_url = redir.url
        else:
            CONN.set(url, tmp_url)
            return tmp_url  # if no url in the redirect chain meets our criteria, just return the last url in
                            # the chain
    except requests.exceptions.TooManyRedirects:
        CONN.set(url, tmp_url)
        return tmp_url
    except (exceptions.RequestException, socket.error) as e:
        # requests can't distinguish failing to connect to an invalid site from having no connectivity whatsoever.
        # We'll try to ping the router; if that works, then it's the url's fault and we'll move on. If it doesn't,
        # we're not connected and there's no point trying to go on
            try:
                requests.head('http://{}'.format(ROUTER_IP)).close()
                # shout-out to Martijn Peters for suggesting this as a better solution on StackOverflow
                # (https://stackoverflow.com/questions/24619150/python-requests-full-url-from-error-message/24619242#24619242)
                end_url = redir.headers.get('location', tmp_url)
                CONN.set(url, end_url)
                return end_url
            except (exceptions.RequestException, socket.error):
                raise e


def fix_url(url):
    expanded_url = resolve_redirects(url)
    m = re.match(DOMAIN_PAT, expanded_url)
    domain = None
    if m:
        domain = m.group(1)
    return expanded_url, domain


def fix_urls(entry):
    js = json.loads(entry)
    urls = js[1][0].get('urls')
    if not urls:  # no urls => nothing to do
        return entry.rstrip()
    domains = []
    expanded_urls = []
    for url in urls:
        expanded_url, domain = fix_url(url)
        expanded_urls.append(expanded_url)
        domains.append(domain)
    js[1][0]['urls'] = expanded_urls
    js[1][0]['domains'] = domains
    return json.dumps(js)


def fix_js(js_file):
    i = 0
    with open(js_file) as f:
        l = f.readlines()
    with open(os.path.join(OUT_DIR, os.path.split(js_file)[-1]), 'a') as f:
        while True:
            try:
                f.write(fix_urls(l.pop()) + "\n")
                i += 1
                print "fixed line {}".format(i)
            except IndexError:
                break
    print "fixed {}".format(js_file)


def fix_all(directory):
    exclude = [os.path.join(directory, fil) for fil in os.listdir(OUT_DIR)]

    def fil_is_valid(fil):
        return fil not in exclude and bool(re.match(r'[\w]+\.json', os.path.split(fil)[-1]))

    fils = filter(fil_is_valid, eld(directory))
    num_fils = len(fils)
    for idx, fil in enumerate(fils):
        print "fixing {} ({} of {})".format(fil, idx, num_fils)
        fix_js(fil)

if __name__ == '__main__':
    fix_all(IN_DIR)
