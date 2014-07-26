#coding=utf8
__author__ = 'Sam Raker'

import gzip
import json

from tools import eld


def get_hashtags():
    master_vectors = eld('master_vectors')
    tag_lists = []
    for vector_list in master_vectors:
        with gzip.open(vector_list) as f:
            js = json.load(f)
            hashtags = js.get('hashtags')
            if len(hashtags) > 2:
                tag_lists.append(set(hashtags))
    return tag_lists


def get_coocurrences(tag_lists):
    tag_sets = []
    for tag_set in tag_lists:
        for other_set in tag_lists:
            if tag_set.issubset(other_set):
                tag_set.update(other_set)
        tag_sets.append(tag_set)
    tag_sets = [tag_set for tag_set in tag_sets if tag_set not in tag_sets]
    return tag_sets


def get_baseline():
    return get_coocurrences(get_hashtags())


if __name__ == '__main__':
    print get_baseline()
