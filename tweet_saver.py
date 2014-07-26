##coding=utf8
__author__ = 'Sam Raker'

from json import dumps
from time import sleep

from twitterizer import Scrape

s = Scrape()


def tweet_saver(outfile, current, total):
    counter = current
    tweets = s.get_tweets(limit=None, as_gen=False)
    while counter < total:
        try:
            with open(outfile, "a") as f:
                f.write(dumps(tweets.next())+"\n")
                counter += 1
                if counter % 10 == 0:
                    print counter
        except ValueError:
            print counter
            tweets = s.get_tweets(limit=None, as_gen=False)
            continue
        except StopIteration:
            print counter
            sleep(60)
            tweets = s.get_tweets(limit=None, as_gen=False)
            continue
        except AttributeError:
            print counter
            sleep(60)
            tweets = s.get_tweets(limit=None, as_gen=False)
            continue
        except KeyboardInterrupt:
            break
    else:
        print "{0} tweets saved to {1}".format(current, outfile)
