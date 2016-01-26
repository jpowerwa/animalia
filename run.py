#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Run flask animalia app.
"""

from __future__ import unicode_literals

import argparse
import logging

from animalia import app

def parse_args():
    parser = argparse.ArgumentParser(
        description="Flask animalia app",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-p', '--port', default='8080', 
                        help='localhost port for application')
    parser.add_argument('-v', '--verbose', action='store_true', 
                        help='debugging capability and verbose output')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.verbose:
        app.logger.setLevel(logging.DEBUG)
    port = int(args.port)
    app.run(host='localhost', port=port, debug=args.verbose)
