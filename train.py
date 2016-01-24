#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Go through training data csv, inserting appropriate Concepts and Relationships into database.
"""

from __future__ import unicode_literals

import argparse
import csv
import logging

from animalia import fact_manager

ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter(fmt='%(name)s [%(levelname)s] %(message)s'))
logging.root.addHandler(ch)
logger = logging.getLogger('train')
logger.setLevel(logging.WARN)


def add_data_from_record(rec):
    """
    :type rec: dict
    :arg rec: dictionary of related data

    dict keys and val types:
      concept             : string
      type                : string
      lives          [OPT]: string that is colon-separated list
      has body part  [OPT]: string that is colon-separated list
      has fur        [OPT]: string that is 'TRUE' or 'FALSE'
      has scales     [OPT]: string that is 'TRUE' or 'FALSE'
      eats           [OPT]: string that is colon-separated list
      parent species [OPT]: string
      leg count      [OPT]: string that is int

    """

    def as_bool(v):
        return v == 'TRUE'

    def split_str(s):
        return [s.lower() for s in s.split(':')] if s else []

    concept = rec['concept']
    add_concept(concept, rec['type'])

    if rec.get('parent species'):
        add_sentence('the {0} is a {1}'.format(concept, rec['parent species']))
    for v in split_str(rec.get('lives')):
        add_sentence('the {0} lives in the {1}'.format(concept, v))
    for v in split_str(rec.get('has body part')):
        if v == 'leg':
            num_legs = rec.get('leg count')
            add_sentence('the {0} has {1} legs'.format(concept, num_legs if num_legs else ''))
        else:
            add_sentence('the {0} has a {1}'.format(concept, v))
    if as_bool(rec.get('has fur')):
        add_sentence('the {0} has fur'.format(concept))
    if as_bool(rec.get('has scales')):
        add_sentence('the {0} has scales'.format(concept))
    for v in split_str(rec.get('eats')):
        add_sentence('the {0} eats {1}'.format(concept, v))

def add_concept(concept_name, concept_type):
    try:
        fact_manager.FactManager.add_concept(concept_name, concept_type)
        logger.info("Added concept '{0}' with type '{1}'".format(concept_name, concept_type))
    except fact_manager.IncomingDataError as ex:
        logger.error("Failed to add concept '{0}' with type '{1}': {2}".format(
                concept_name, concept_type, ex))

def add_sentence(sentence):
    fact = None
    try:
        fact = fact_manager.FactManager.fact_from_sentence(sentence)
        logger.info("Added sentence '{0}' (fact_id={1})".format(sentence, fact.fact_id))
    except fact_manager.IncomingDataError as ex:
        logger.error("Failed to add sentence '{0}': {1}".format(sentence, ex))
    return fact

def parse_args():
    parser = argparse.ArgumentParser(
        description='Add facts from training data set',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('infile', help='csv file of training data')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output')
    
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    with open(args.infile, 'r') as f:
        reader = csv.DictReader(f)
        for rec in reader:
            try:
                add_data_from_record(rec)
            except ValueError as ex:
                logger.error("Failed to add data from record '{0}'".format(rec))

    logger.info("Done")

