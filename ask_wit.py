#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Submit query to wit.ai for interpretation and present response.

Examples:
  How many animals have tails?
  Which animals eat berries?
  Which animals do not eat berries?
  How many animals do not eat berries?
  Which animals eat mammals?
  Does a bear have scales?
  Does a bear have fur?
  Do mammals live in the ocean?
  What do coyotes eat?
  Where does a salmon live?

"""

from __future__ import unicode_literals

import argparse
import logging
import sys

import wit

# local 
from animalia.config import Config


def parse_args():
    parser = argparse.ArgumentParser(
        description='Query wit animalia app',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('query', help='query to submit to wit animalia app')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output')
    return parser.parse_args()

def query_wit(query):
    response = wit.text_query(query, Config.wit_access_token)
    print('Response: {}'.format(response))


if __name__ == "__main__":
    args = parse_args()

    wit.init()
    try:
        query_wit(args.query)
    finally:
        wit.close()
    sys.exit(0)

