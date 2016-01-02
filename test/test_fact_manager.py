#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit tests for fact_manager.py
"""

from __future__ import unicode_literals

import copy
import datetime
import json
import unittest
import uuid

from mock import ANY, Mock, patch

import animalia.fact_manager as fact_manager
from animalia.fact_manager import FactManager
import animalia.fact_model as fact_model
import wit_responses


@patch.object(FactManager, '_merge_to_db_session')
@patch.object(FactManager, '_ensure_relationship')
@patch.object(FactManager, '_filter_entity_values')
@patch.object(FactManager, '_reorder_concepts_by_subject')
@patch.object(FactManager, '_ensure_concept_with_type')
@patch.object(FactManager, '_verify_parsed_fact_data')
class SaveParsedFactTests(unittest.TestCase):
    """Verify behavior of FactManager._save_parsed_fact.

    This needs a lot of mocks, but that is okay since it is a workhorse of a method.
    """

    def _get_wit_response_data(self, key):
        """Return JSON that is captured wit.ai response data with specified name.
        """
        return copy.deepcopy(getattr(wit_responses, key))


    def test_save_parsed_fact(self, verify_data, ensure_typed_concept, reorder_concepts,
                              filter_entities, ensure_relationship, merge_to_session):
        """Verify calls made by _save_parsed_fact for a relationship with subject and object.
        """
        # Set up mocks and test data
        test_data = self._get_wit_response_data('animal_species_fact_data')

        test_subject_concept = fact_model.Concept(concept_name='otter')
        test_object_concept = fact_model.Concept(concept_name='mammal')
        ensure_typed_concept.side_effect = [test_subject_concept, test_object_concept]
        reorder_concepts.return_value = [test_subject_concept, test_object_concept]
        filter_entities.return_value = (['is a'], [])
        mock_relationship = Mock(name='relationship')
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
            test_subject_concept, test_object_concept, relationship_name='is a', 
            relationship_number=None, new_fact_id=ANY)
        new_fact_id = ensure_relationship.call_args[1]['new_fact_id']
        
        call_args_list = merge_to_session.call_args_list
        self.assertEqual(2, len(call_args_list))
        self.assertEqual(mock_relationship, call_args_list[0][0][0])
        incoming_fact_arg = call_args_list[1][0][0]
        self.assertEqual(new_fact_id, incoming_fact_arg.fact_id)
        self.assertEqual('the otter is a mammal', incoming_fact_arg.fact_text)
        self.assertEqual(json.dumps(test_data), incoming_fact_arg.parsed_fact)

    def test_relationship_with_count(self, verify_data, ensure_typed_concept, reorder_concepts,
                                     filter_entities, ensure_relationship, merge_to_session):
        """Verify calls made by _save_parsed_fact for a relationship with number entity.
        """
        # Set up mocks and test data
        test_data = self._get_wit_response_data('animal_leg_fact_data')

        test_subject_concept = fact_model.Concept(concept_name='otter')
        test_object_concept = fact_model.Concept(concept_name='legs')
        ensure_typed_concept.side_effect = [test_subject_concept, test_object_concept]
        reorder_concepts.return_value = [test_subject_concept, test_object_concept]
        filter_entities.side_effect = [(['has'], []), ([4], [])]
        mock_relationship = Mock(name='relationship')
        ensure_relationship.return_value = mock_relationship
        mock_saved_relationship = Mock(name='saved_relationship')
        mock_saved_fact = Mock(name='saved_fact')
        merge_to_session.side_effect = [mock_saved_relationship, mock_saved_fact]

        # Make call
        saved_fact = FactManager._save_parsed_fact(parsed_data=test_data)
        
        # Verify result
        self.assertEqual(mock_saved_fact, saved_fact)

        # Verify mocks
        self.assertEqual(1, verify_data.call_count)

        call_args_list = ensure_typed_concept.call_args_list
        self.assertEqual(2, len(call_args_list))
        self.assertEqual(set(['otter', 'legs']), 
                         set([call_args[0][0][0]['value'] for call_args in call_args_list]))
        self.assertEqual(set(['animal', 'body_part']), 
                         set([call_args[0][1] for call_args in call_args_list]))

        reorder_concepts.assert_called_once_with([test_subject_concept, test_object_concept])

        call_args_list = filter_entities.call_args_list
        self.assertEqual(2, len(call_args_list))
        self.assertEqual([{'type': 'value', 'value': 'has'}], call_args_list[0][0][0])
        self.assertEqual([{'type': 'value', 'value': 4}], call_args_list[1][0][0])

        ensure_relationship.assert_called_once_with(
            test_subject_concept, test_object_concept, relationship_name='has', 
            relationship_number=4, new_fact_id=ANY)
        new_fact_id = ensure_relationship.call_args[1]['new_fact_id']

        self.assertEqual(2, merge_to_session.call_count)
        incoming_fact_arg = merge_to_session.call_args_list[1][0][0]
        self.assertEqual(new_fact_id, incoming_fact_arg.fact_id)
        self.assertEqual('the otter has four legs', incoming_fact_arg.fact_text)
        self.assertEqual(json.dumps(test_data), incoming_fact_arg.parsed_fact)

    def test_with_suggested_relationship(self, verify_data, ensure_typed_concept, reorder_concepts,
                                         filter_entities, ensure_relationship, merge_to_session):
        """Verify calls made by _save_parsed_fact for a relationship with suggested entity.
        """
        # Set up mocks and test data
        test_data = self._get_wit_response_data('animal_species_fact_with_suggestion_data')

        test_subject_concept = fact_model.Concept(concept_name='otter')
        test_object_concept = fact_model.Concept(concept_name='mammal')
        reorder_concepts.return_value = [test_subject_concept, test_object_concept]
        filter_entities.return_value = (['is'], ['a'])

        # Make call
        with patch.object(fact_manager.logger, 'warn') as log_warn:
            FactManager._save_parsed_fact(parsed_data=test_data)
        expected_warning = ("Skipping suggested relationship '{0}' "
                            "for subject '{1}' and object '{2}'").format('a', 'otter', 'mammal')
        log_warn.assert_called_once_with(expected_warning)

        # Verify mocks
        filter_entities.assert_called_once_with(
            [{'suggested': True, 'type': 'value', 'value': 'a'}, {'type': 'value', 'value': 'is'}])
        ensure_relationship.assert_called_once_with(
            test_subject_concept, test_object_concept, relationship_name='is',
            relationship_number=None, new_fact_id=ANY)

    def test_parse_error__failed_concept(self, verify_data, ensure_typed_concept, reorder_concepts,
                                         filter_entities, ensure_relationship, merge_to_session):
        """Verify ParseError if Concept cannot be created.
        """
        # Set up mocks and test data
        test_data = self._get_wit_response_data('animal_species_fact_data')
        ensure_typed_concept.return_value = None

        # Make call
        self.assertRaisesRegexp(FactManager.ParseError,            
                                "Invalid parsed fact data: Invalid data for concept_type 'species'",
                                FactManager._save_parsed_fact,
                                parsed_data=test_data)

    def test_parse_error__too_many_concepts(self, verify_data, ensure_typed_concept, 
                                            reorder_concepts, filter_entities, ensure_relationship,
                                            merge_to_session):
        """Verify ParseError if more than two concept entities are present in parsed data.
        """
        # Set up mocks and test data
        test_data = self._get_wit_response_data('animal_species_fact_data')
        test_data['outcomes'][0]['entities']['new_entity'] = [{'type': 'value', 'value': 'foo'}]
        ensure_typed_concept.return_value = Mock(name='concept', concept_name='mock_concept')

        # Make call
        self.assertRaisesRegexp(FactManager.ParseError,
                                "Invalid parsed fact data: Expected 2 concept entities, found 3: ",
                                FactManager._save_parsed_fact,
                                parsed_data=test_data)

    def test_parse_error__reorder_concept_failure(self, verify_data, ensure_typed_concept, 
                                                  reorder_concepts, filter_entities, 
                                                  ensure_relationship, merge_to_session):
        """Verify ParseError if _reorder_concepts_by_subject raises ValueError.
        """
        # Set up mocks and test data
        test_data = self._get_wit_response_data('animal_species_fact_data')
        mock_concepts = [Mock(name='concept_1'), Mock(name='concept_2')]
        ensure_typed_concept.side_effect = mock_concepts
        reorder_concepts.side_effect = ValueError("Bad dog. No biscuit.")

        # Make call
        self.assertRaisesRegexp(FactManager.ParseError,
                                "Invalid parsed fact data: Bad dog. No biscuit.",
                                FactManager._save_parsed_fact,
                                parsed_data=test_data)

        # Verify mocks
        reorder_concepts.assert_called_once_with(mock_concepts)

    def test_parse_error__multiple_relationships(self, verify_data, ensure_typed_concept, 
                                                 reorder_concepts, filter_entities, 
                                                 ensure_relationship, merge_to_session):
        """Verify ParseError if multiple relationship entities are present in parsed data.
        """
        # Set up mocks and test data
        test_data = self._get_wit_response_data('animal_species_fact_data')
        test_concepts = [fact_model.Concept(concept_name='otter'), 
                         fact_model.Concept(concept_name='mammal')]
        ensure_typed_concept.side_effect = test_concepts
        reorder_concepts.return_value = test_concepts
        filter_entities.return_value = (['is a', 'foo'], [])

        # Make call
        expected_msg = ("Invalid parsed fact data: Expected 1 relationship entity for "
                        "subject 'otter' and object 'mammal'; found 2")
        self.assertRaisesRegexp(FactManager.ParseError,
                                expected_msg,
                                FactManager._save_parsed_fact,
                                parsed_data=test_data)

    def test_parse_error__zero_relationships(self, verify_data, ensure_typed_concept, 
                                             reorder_concepts, filter_entities, 
                                             ensure_relationship, merge_to_session):
        """Verify ParseError if zero relationship entities are present in parsed data.
        
        Note that if data has no relationship entity, verification step will fail, but since
        the code handles it, might as well test it.
        """
        # Set up mocks and test data
        test_data = self._get_wit_response_data('animal_species_fact_data')
        test_concepts = [fact_model.Concept(concept_name='otter'), 
                         fact_model.Concept(concept_name='mammal')]
        ensure_typed_concept.side_effect = test_concepts
        reorder_concepts.return_value = test_concepts
        filter_entities.return_value = ([], [])

        # Make call
        expected_msg = ("Invalid parsed fact data: Expected 1 relationship entity for "
                        "subject 'otter' and object 'mammal'; found 0")
        self.assertRaisesRegexp(FactManager.ParseError,
                                expected_msg,
                                FactManager._save_parsed_fact,
                                parsed_data=test_data)

    def test_conflict_error(self, verify_data, ensure_typed_concept, reorder_concepts,
                            filter_entities, ensure_relationship, merge_to_session):
        """Verify ConflictError from _ensure_relationship bubbles up.
        """
        # Set up mocks and test data
        test_data = self._get_wit_response_data('animal_species_fact_data')
        mock_concepts = [Mock(name='concept_1'), Mock(name='concept_2')]
        reorder_concepts.return_value = mock_concepts 
        filter_entities.return_value = (['is'], [])
        ensure_relationship.side_effect = FactManager.ConflictError('boo hoo')

        # Make call
        self.assertRaisesRegexp(FactManager.ConflictError,
                                'boo hoo',
                                FactManager._save_parsed_fact,
                                parsed_data=test_data)
        # Verify mocks
        ensure_relationship.assert_called_once_with(
            mock_concepts[0], mock_concepts[1], relationship_name='is',
            relationship_number=None, new_fact_id=ANY)


