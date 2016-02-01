#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Animalia-specific constants that should come from configuration.
"""

from __future__ import unicode_literals

class Config(object):
    __doc__ = __doc__

    db_connection = 'mysql://animalia:grrargh@localhost/animalia'

    wit_access_token = 'JZKCMFUAZKZ5FQZT3JXEZVJM2XVNNPXI'
    wit_query_uri = 'https://api.wit.ai/message'
    wit_api_version = '20141022'

    # Recommended minimum threshold for wit response to be considered accurate
    parsed_data_confidence_threshold = 0.7

    # Keywords for entity that is subject of sentence
    wit_subject_entity_types = ['animal']
    # Keywords for entity that is sometimes object and sometimes subject of sentence
    wit_alt_subject_entity_types = ['species']
    
