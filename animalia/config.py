#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Constants that should come from configuration.
"""

from __future__ import unicode_literals

class Config(object):
    db_connection = 'mysql://animalia:grrargh@localhost/animalia'

    wit_access_token = 'JZKCMFUAZKZ5FQZT3JXEZVJM2XVNNPXI'
    wit_app_id = '56300313-4dfd-4da3-a74d-2ae701d1cfbb'
    
    parsed_data_confidence_threshold = 0.8
    parsed_data_relationship_entity_types = ['relationship', 'number']
    parsed_data_subject_entity_types = ['animal']
    
