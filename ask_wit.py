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
import urllib

import requests

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
    url = 'https://api.wit.ai/message?v=20141022&q={0}'.format(
        urllib.quote_plus(query))
    headers = {'Accept': 'application/json',
               'Authorization': 'Bearer {0}'.format(Config.wit_access_token)}
    response = requests.get(url, headers=headers)
    print('Response status: {0}'.format(response.status_code))
    response_data = response.json()
    print('Response data: {0}'.format(response_data))


if __name__ == "__main__":
    args = parse_args()
    query_wit(args.query)
    sys.exit(0)

