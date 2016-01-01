#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit tests for fact_manager.py
"""

from __future__ import unicode_literals

import datetime
import json
import unittest
import uuid

from mock import ANY, Mock, patch

from animalia.fact_manager import FactManager
import animalia.fact_model as fact_model


@patch.object(FactManager, '_merge_to_db_session')
@patch.object(FactManager, '_ensure_relationship')
@patch.object(FactManager, '_filter_entity_values')
@patch.object(FactManager, '_reorder_concepts_by_subject')
@patch.object(FactManager, '_ensure_concept_with_type')
@patch.object(FactManager, '_verify_parsed_data')
class SaveParsedFactTests(unittest.TestCase):
    """Verify behavior of FactManager._save_parsed_fact.

    This needs a lot of mocks, but that is okay since it is a workhorse of a method.
    """

    def setUp(self):
        self._animal_species_fact_data = {
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

    def test_save_parsed_fact__relationship(self, verify_data, ensure_typed_concept, 
                                            reorder_concepts, filter_entities,
                                            ensure_relationship, merge_to_session):
        """Verify calls made by _save_parsed_fact for a relationship with subject and object.
        """
        # Set up mocks and test data
        test_data = self._animal_species_fact_data

        test_subject_concept = fact_model.Concept(concept_name='otter')
        test_object_concept = fact_model.Concept(concept_name='mammal')
        ensure_typed_concept.side_effect = [test_subject_concept, test_object_concept]
        reorder_concepts.return_value = [test_subject_concept, test_object_concept]
        filter_entities.return_value = (['is a'], [])
        mock_relationship = Mock(name='relationship', relationship_id=None)        
        ensure_relationship.return_value = mock_relationship
        mock_saved_relationship = Mock(name='saved_relationship')
        mock_saved_fact = Mock(name='saved_fact')
        merge_to_session.side_effect = [mock_saved_relationship, mock_saved_fact]

        # Make call
        saved_fact = FactManager._save_parsed_fact(parsed_data=test_data)
        
        # Verify result
        self.assertEqual(mock_saved_fact, saved_fact)

        # Verify mocks
        call_args = verify_data.call_args
        self.assertEqual(test_data, call_args[0][0])
        self.assertTrue(hasattr(call_args[0][1], '__call__'))

        call_args_list = ensure_typed_concept.call_args_list
        self.assertEqual(2, len(call_args_list))
        self.assertEqual(set(['otter', 'mammal']), 
                         set([call_args[0][0][0]['value'] for call_args in call_args_list]))
        self.assertEqual(set(['animal', 'species']), 
                         set([call_args[0][1] for call_args in call_args_list]))

        reorder_concepts.assert_called_once_with([test_subject_concept, test_object_concept])
        filter_entities.assert_called_once_with([{'type': 'value', 'value': 'is a'}])
        ensure_relationship.assert_called_once_with(
            test_subject_concept, test_object_concept, relationship_name='is a', new_fact_id=ANY)
        new_fact_id = ensure_relationship.call_args[1]['new_fact_id']
        
        call_args_list = merge_to_session.call_args_list
        self.assertEqual(2, len(call_args_list))
        self.assertEqual(mock_relationship, call_args_list[0][0][0])
        incoming_fact_arg = call_args_list[1][0][0]
        self.assertEqual(new_fact_id, incoming_fact_arg.fact_id)
        self.assertEqual('the otter is a mammal', incoming_fact_arg.fact_text)
        self.assertEqual(json.dumps(test_data), incoming_fact_arg.parsed_fact)
