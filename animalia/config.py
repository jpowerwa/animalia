#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Constants that should come from configuration.
"""

from __future__ import unicode_literals

class Config(object):
    db_connection = 'mysql://animalia:grrargh@localhost/animalia'

    wit_access_token = 'JZKCMFUAZKZ5FQZT3JXEZVJM2XVNNPXI'
    wit_app_id = '56300313-4dfd-4da3-a74d-2ae701d1cfbb'

    # Minimum threshold for wit response to be considered accurate
    parsed_data_confidence_threshold = 0.5

    # Keywords for entity that is subject of sentence
    wit_subject_entity_types = ['animal']
    # Keywords for entity that is sometimes object and sometimes subject of sentence
    wit_alt_subject_entity_types = ['species']
    
