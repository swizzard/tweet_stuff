#coding=utf8
__author__ = 'Sam Raker'

import gzip
import json
from os import path

from tools import eld

VECTORS = ['domains', 'hashtags', 'mentions', 'split_hashtags', 'urls', 'words']
VALUES = ['day_mean', 'day_median', 'day_std_dev', 'follow_ratio_mean', 'follow_ratio_median', 'follow_ratio_std_dev',
          'followers_mean', 'followers_median', 'followers_std_dev', 'following_mean', 'following_median',
          'following_std_dev', 'is_weekday_mean', 'is_weekday_median', 'is_weekday_std_dev', 'offset_median',
          'offset_rms', 'offset_std_dev']


def set_to_weka(infile):
    tpl = """"""
    prefix = path.split(infile)[1].split('_')[0]
    with open(infile) as f:
        for line in f:
            if line.endswith('\n'):
                line = line[:-1]
            tpl += "@ATTRIBUTE '{prefix}_{token}' NUMERIC\n".format(prefix=prefix, token=line)
    return tpl


def nonvector_to_weka():
    tpl = """"""
    for value in VALUES:
        tpl += '@ATTRIBUTE value_{val} NUMERIC\n'.format(val=value)
    return tpl


def gen_weka_header(outfile='arff_header.txt', dry_run=False):
    tpl = """% 1. Title: Hashtag Clustering Dataset
%
% 2. Sources:
%   Creator: Sam Raker
%   Tweets collected from the public stream between 2012 and 2014
%
@RELATION hashtag_cluster

        """
    for set_name in VECTORS:
        tpl += set_to_weka(path.join('sets', '{set_name}_set.txt'.format(set_name=set_name)))
    out_tpl = '{tpl}{vals}\n\n@DATA\n'.format(tpl=tpl, vals=nonvector_to_weka())
    if dry_run:
        print out_tpl
    else:
        with open(outfile, 'w') as f:
            f.write(out_tpl)


def process_set(vect_list, ref_set):
    s = ''
    for x in xrange(len(ref_set)):
        if x in vect_list:
            s += '1,'
        else:
            s += '0,'
    return s

def process_master_vector(master_vector_file):
    s = ''
    with gzip.open(master_vector_file) as f:
        d = json.load(f)
    for vect in VECTORS:
        with open(path.join('sets', '{vect}_set.txt'.format(vect=vect))) as f:
            ref_list = f.readlines()
        l = d.get(vect, [])
        s += process_set(l, ref_list)
    return s

def process_master_value(master_value_file):
    s = ''
    with gzip.open(master_value_file) as f:
        d = json.load(f)
    for value in VALUES:
        s += '{val},'.format(val=d.get(value, '?'))
    return s.replace('-1', '?')


def process_entry(master_vector_file):
    value_file = path.join('master_values', path.split(master_vector_file)[1])
    if not path.exists(value_file):
        return None
    s = process_master_vector(master_vector_file) + process_master_value(value_file)
    if s.endswith(','):
        s = s[:-1]
    return s + '\n'

def process_all(outfile='arff_data.txt', dry_run=False):
    fils = eld('master_vectors')
    s = ''
    for fil in fils:
        entry = process_entry(fil)
        if not entry:
            print """WARNING: No corresponding value file found for {fil}""".format(fil=fil)
        else:
            s += process_entry(fil)
    if dry_run:
        print s
    else:
        with open(outfile, 'w') as f:
            f.write(s)


def combine_header_data(dry_run=False, arff_file='tag_clusters.arff', header_file='arff_header.txt',
                        data_file='arff_data.txt'):
    if dry_run:
        with open(header_file) as header:
            print header
        with open(data_file) as data:
            print data
    else:
        with open(arff_file, 'w') as f:
            with open(header_file) as header:
                f.write(header)
            with open(data_file) as data:
                f.write(data)
