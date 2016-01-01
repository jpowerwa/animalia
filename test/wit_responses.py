#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Hard-coded response data captured from wit.ai text_query API.
"""

from __future__ import unicode_literals


animal_leg_fact_data = {
    "_text": "the otter has four legs",
    "msg_id": "ee6bc003-161c-4693-8886-17ce81c944c0",
    "outcomes": [{
            "_text": "the otter has four legs",
            "confidence": 0.994,
            "entities": {
                "animal": [{"type": "value", "value": "otter"}],
                "body_part": [{"type": "value", "value": "legs"}],
                "number": [{"type": "value", "value": 4}],
                "relationship": [{"type": "value", "value": "has"}]
                },
            "intent": "animal_leg_fact"
            }]
    }

animal_species_fact_data = {
    '_text': 'the otter is a mammal',
    'outcomes': [{
            '_text': 'the otter is a mammal',
            'confidence': 0.9,
            'entities': {
                'animal': [{'type': 'value', 'value': 'otter'}],
                'species': [{'type': 'value', 'value': 'mammal'}],
                'relationship': [{'type': 'value', 'value': 'is a'}]
                },
            'intent': 'animal_species_fact'
            }]
    }
