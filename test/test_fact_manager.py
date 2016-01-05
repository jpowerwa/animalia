#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit tests for fact_manager.py
"""

from __future__ import unicode_literals

import copy
import datetime
import json
import logging
import unittest
import uuid

from mock import ANY, Mock, patch

from animalia.fact_manager import (logger,
                                   FactManager, 
                                   IncomingFactError,
                                   FactParseError, 
                                   InvalidFactDataError,
                                   ConflictingFactError,
                                   DuplicateFactError)
import animalia.fact_model as fact_model
import wit_responses

# Set log level for unit tests
logger.setLevel(logging.WARN)


class FactManagerTests(unittest.TestCase):
    """Verify behavior of simple FactManager methods.
    """

    @patch.object(fact_model.db.session, 'commit')
    @patch.object(FactManager, '_save_parsed_fact')
    @patch.object(FactManager, '_query_wit')
    @patch.object(fact_model.IncomingFact, 'select_by_text')
    @patch.object(FactManager, '_normalize_sentence')
    def test_fact_from_sentence(self, normalize_sentence, select_fact, query_wit, save_fact, 
                                commit_txn):
        """Verify calls made by fact_from_sentence.
        """
        # Set up mocks and test data
        mock_sentence = Mock(name='sentence')
        normalize_sentence.return_value = mock_normalized_sentence = Mock(name='norm_sentence')
        select_fact.return_value = None
        test_data = copy.deepcopy(wit_responses.animal_species_fact_data)
        query_wit.return_value = json.dumps(test_data)
        save_fact.return_value = saved_fact = Mock(name='saved_fact')

        # Make call
        fact = FactManager.fact_from_sentence(mock_sentence)

        # Verify result
        self.assertEqual(saved_fact, fact)
        
        # Verify mocks
        normalize_sentence.assert_called_once_with(mock_sentence)
        select_fact.assert_called_once_with(mock_normalized_sentence)
        query_wit.assert_called_once_with(mock_normalized_sentence)
        save_fact.assert_called_once_with(parsed_data=test_data)
        self.assertEqual(1, commit_txn.call_count)
        
    @patch.object(fact_model.db.session, 'commit')
    @patch.object(FactManager, '_save_parsed_fact')
    @patch.object(FactManager, '_query_wit')
    @patch.object(fact_model.IncomingFact, 'select_by_text')
    @patch.object(FactManager, '_normalize_sentence')
    def test_fact_from_sentence__existing_sentence(self, normalize_sentence, select_fact, 
                                                   query_wit, save_fact, commit_txn):
        """Verify calls made by fact_from_sentence when sentence matches existing fact.
        """
        # Set up mocks and test data
        mock_sentence = Mock(name='sentence')
        normalize_sentence.return_value = mock_normalized_sentence = Mock(name='norm_sentence')
        select_fact.return_value = mock_fact = Mock(name='incoming_fact')
        test_data = copy.deepcopy(wit_responses.animal_species_fact_data)

        # Make call
        fact = FactManager.fact_from_sentence(mock_sentence)

        # Verify result
        self.assertEqual(mock_fact, fact)
        
        # Verify mocks
        normalize_sentence.assert_called_once_with(mock_sentence)
        select_fact.assert_called_once_with(mock_normalized_sentence)
        self.assertEqual(0, query_wit.call_count)
        self.assertEqual(0, save_fact.call_count)
        self.assertEqual(0, commit_txn.call_count)

    @patch.object(FactManager, '_normalize_sentence')
    def test_fact_from_sentence__no_sentence(self, normalize_sentence):
        """Verify FactParseError if no sentence is provided.
        """
        for empty in (None, ''):
            normalize_sentence.return_value = empty
            self.assertRaisesRegexp(FactParseError,
                                    'Invalid fact sentence provided',
                                    FactManager.fact_from_sentence, 
                                    'the otter lives in the river')

    def test_fact_from_sentence__no_normalized_sentence(self):
        """Verify FactParseError if sentence normalizes to empty string.
        """
        self.assertRaisesRegexp(FactParseError,
                                'Invalid fact sentence provided',
                                FactManager.fact_from_sentence, 
                                '')

    def test_normalize_sentence(self):
        """Verify functionality of _normalize_sentence.
        """
        sentence = 'The otter, lives in the river!'
        self.assertEqual('the otter lives in the river', FactManager._normalize_sentence(sentence))

    def test_filter_entity_values(self):
        """Verify behavior of filter_entity_values.
        """
        # Set up mocks and test data
        value_entities = [{'type': 'value', 'value': 'foo'}, {'type': 'value', 'value': 'bar'}]
        suggested_entities = [{'type': 'value', 'value': 'maybe foo', 'suggested': True}, 
                              {'type': 'value', 'value': 'maybe bar', 'suggested': True}]
        other_entities = [{'type': 'whatever'}, {'type': 'whoever'}]
        test_data = [suggested_entities[0], 
                     value_entities[0], 
                     other_entities[0],
                     value_entities[1],
                     other_entities[1],
                     suggested_entities[1]]
        
        # Make call
        v, s = FactManager._filter_entity_values(test_data)
        
        # Verify results
        self.assertEqual([e['value'] for e in value_entities], v)
        self.assertEqual([e['value'] for e in suggested_entities], s)
        
    def test_filter_entity_values__empty_data(self):
        """Verify behavior of filter_entity_values when empty data is supplied.
        """
        for empty in (None, []):
            self.assertEqual(([], []), FactManager._filter_entity_values(empty))
        

@patch.object(FactManager, '_merge_to_db_session')
@patch.object(FactManager, '_relationship_from_entity_data')
@patch.object(FactManager, '_verify_parsed_fact_data')
class SaveParsedFactTests(unittest.TestCase):
    """Verify behavior of FactManager._save_parsed_fact.
    """

    def _get_wit_response_data(self, key):
        """Return JSON that is captured wit.ai response data with specified name.
        """
        return copy.deepcopy(getattr(wit_responses, key))

    def test_save_parsed_fact(self, verify_data, create_relationship, merge_to_session):
        """Verify calls made by _save_parsed_fact.
        """
        # Set up mocks and test data
        test_data = copy.deepcopy(wit_responses.animal_species_fact_data)
        verify_data.return_value = test_data['outcomes'][0]
        create_relationship.return_value = mock_relationship = Mock(name='relationship')
        mock_saved_relationship = Mock(name='saved_relationship')
        mock_saved_fact = Mock(name='saved_fact')
        merge_to_session.side_effect = [mock_saved_relationship, mock_saved_fact]

        # Make call
        saved_fact = FactManager._save_parsed_fact(parsed_data=test_data)
        
        # Verify result
        self.assertEqual(mock_saved_fact, saved_fact)

        # Verify mocks
        self.assertEqual(1, verify_data.call_count)
        call_args = verify_data.call_args
        self.assertEqual(test_data, call_args[0][0])
        self.assertTrue(hasattr(call_args[0][1], '__call__'))

        self.assertEqual(1, create_relationship.call_count)
        call_args = create_relationship.call_args
        self.assertEqual(test_data['outcomes'][0]['entities'], call_args[0][0])
        self.assertTrue(hasattr(call_args[0][1], '__call__'))
        new_fact_id = call_args[1]['new_fact_id']
        self.assertTrue(isinstance(new_fact_id, uuid.UUID))
        
        call_args_list = merge_to_session.call_args_list
        self.assertEqual(2, len(call_args_list))
        self.assertEqual(mock_relationship, call_args_list[0][0][0])
        incoming_fact_arg = call_args_list[1][0][0]
        self.assertEqual(new_fact_id, incoming_fact_arg.fact_id)
        self.assertEqual('the otter is a mammal', incoming_fact_arg.fact_text)
        self.assertEqual(json.dumps(test_data), incoming_fact_arg.parsed_fact)

    @patch.object(fact_model.IncomingFact, 'select_by_id')
    def test_save_parsed_fact__duplicate_fact(self, select_fact, verify_data, create_relationship,
                                              merge_to_session):
        """Verify calls made by _save_parsed_fact when relationship is duplicate.
        """
        # Set up mocks and test data
        test_data = copy.deepcopy(wit_responses.animal_species_fact_data)
        dup_fact_id = uuid.uuid4()
        verify_data.return_value = test_data['outcomes'][0]
        select_fact.return_value = mock_fact = Mock(name='fact')
        create_relationship.side_effect = DuplicateFactError('uh oh',
                                                             duplicate_fact_id=dup_fact_id)

        # Make call
        with patch.object(logger, 'warn') as log_warn:
            saved_fact = FactManager._save_parsed_fact(parsed_data=test_data)
        
        # Verify return value
        self.assertEqual(mock_fact, saved_fact)
        
        # Verify mocks
        log_warn.assert_called_once_with('uh oh')
        select_fact.assert_called_once_with(dup_fact_id)


@patch.object(FactManager, '_ensure_relationship')
@patch.object(FactManager, '_filter_entity_values')
@patch.object(FactManager, '_concepts_from_entity_data')
class RelationshipFromEntityDataTests(unittest.TestCase):
    """Verify behavior of FactManager._relationship_from_entity_data.
    """

    def _get_entity_data(self, key):
        """Return JSON for 'entities' element of captured wit.ai response data with specified name.
        """
        response_data = getattr(wit_responses, key)
        return copy.deepcopy(response_data['outcomes'][0]['entities'])

    def test_relationship_from_entity_data(self, create_concepts, filter_entities, 
                                           ensure_relationship):
        """Verify calls made by _relationship_from_entity_data.
        """
        # Set up mocks and test data
        test_data = self._get_entity_data('animal_species_fact_data')
        mock_raise_fn = Mock(name='raise_fn')
        mock_fact_id = Mock(name='fact_id')
        mock_subj_concept = Mock(name='subj_concept')
        mock_obj_concept = Mock(name='obj_concept')
        create_concepts.return_value = (mock_subj_concept, mock_obj_concept)
        filter_entities.return_value = (['whatever'], [])
        ensure_relationship.return_value = mock_relationship = Mock(name='relationship')

        # Make call
        relationship = FactManager._relationship_from_entity_data(
            test_data, mock_raise_fn, new_fact_id=mock_fact_id)
        
        # Verify result
        self.assertEqual(mock_relationship, relationship)

        # Verify mocks
        create_concepts.assert_called_once_with(test_data, mock_raise_fn, new_fact_id=mock_fact_id)
        filter_entities.assert_called_once_with([{'type': 'value', 'value': 'is a'}])
        ensure_relationship.assert_called_once_with(mock_subj_concept, 
                                                    mock_obj_concept, 
                                                    relationship_name='whatever', 
                                                    relationship_number=None, 
                                                    new_fact_id=mock_fact_id,
                                                    error_on_duplicate=True)

    def test_with_count(self, create_concepts, filter_entities, ensure_relationship):
        """Verify calls made by _relationship_from_entity_data for relationship with number entity.
        """
        # Set up mocks and test data
        test_data = self._get_entity_data('animal_leg_fact_data')
        mock_fact_id = Mock(name='fact_id')
        mock_subj_concept = Mock(name='subj_concept')
        mock_obj_concept = Mock(name='obj_concept')
        create_concepts.return_value = (mock_subj_concept, mock_obj_concept)
        filter_entities.side_effect = [(['whatever'], []), ([14], [])]
        ensure_relationship.return_value = mock_relationship = Mock(name='relationship')

        # Make call
        relationship = FactManager._relationship_from_entity_data(
            test_data, Mock(name='raise_fn'), new_fact_id=mock_fact_id)
        
        # Verify result
        self.assertEqual(mock_relationship, relationship)

        # Verify mocks
        call_args_list = filter_entities.call_args_list
        self.assertEqual(2, len(call_args_list))
        self.assertEqual([{'type': 'value', 'value': 'has'}], call_args_list[0][0][0])
        self.assertEqual([{'type': 'value', 'value': 4}], call_args_list[1][0][0])

        ensure_relationship.assert_called_once_with(mock_subj_concept, 
                                                    mock_obj_concept, 
                                                    relationship_name='whatever', 
                                                    relationship_number=14,
                                                    new_fact_id=mock_fact_id,
                                                    error_on_duplicate=True)

    def test_with_suggested_relationship(self, create_concepts, filter_entities,
                                         ensure_relationship):
        """Verify calls made by _relationship_from_entity_data with suggested relationship entity.
        """
        # Set up mocks and test data
        test_data = self._get_entity_data('animal_species_fact_with_suggestion_data')
        mock_fact_id = Mock(name='fact_id')
        mock_subj_concept = Mock(name='subj_concept', concept_name='otter')
        mock_obj_concept = Mock(name='obj_concept', concept_name='mammal')
        create_concepts.return_value = (mock_subj_concept, mock_obj_concept)
        filter_entities.return_value = (['whatever'], ['just an idea'])
        ensure_relationship.return_value = mock_relationship = Mock(name='relationship')

        # Make call
        with patch.object(logger, 'warn') as log_warn:
            FactManager._relationship_from_entity_data(
                test_data, Mock(name='raise_fn'), new_fact_id=mock_fact_id)
        msg = "Skipping suggested relationship '{0}' for subject '{1}' and object '{2}'".format(
            'just an idea', 'otter', 'mammal')
        log_warn.assert_called_once_with(msg)

        # Verify mocks
        filter_entities.assert_called_once_with(
            [{'suggested': True, 'type': 'value', 'value': 'a'}, {'type': 'value', 'value': 'is'}])
        ensure_relationship.assert_called_once_with(mock_subj_concept, 
                                                    mock_obj_concept, 
                                                    relationship_name='whatever',
                                                    relationship_number=None, 
                                                    new_fact_id=mock_fact_id,
                                                    error_on_duplicate=True)

    def test_error__multiple_relationships(self, create_concepts, filter_entities,
                                           ensure_relationship):
        """Verify error if multiple relationship entities are present in parsed data.
        """
        test_data = self._get_entity_data('animal_species_fact_data')
        mock_raise_fn = Mock(name='raise_fn', side_effect=ValueError)
        mock_subj_concept = Mock(name='subj_concept', concept_name='otter')
        mock_obj_concept = Mock(name='obj_concept', concept_name='mammal')
        create_concepts.return_value = (mock_subj_concept, mock_obj_concept)
        filter_entities.return_value = (['whatever', 'whoever'], [])

        # Make call
        self.assertRaises(ValueError,
                          FactManager._relationship_from_entity_data,
                          test_data, 
                          mock_raise_fn, 
                          new_fact_id=Mock()) 

        # Verify mocks
        mock_raise_fn.assert_called_once_with(
            "Expected 1 relationship entity for subject 'otter' and object 'mammal'; found 2")

    def test_error__zero_relationships(self, create_concepts, filter_entities, ensure_relationship):
        """Verify error if zero relationship entities are present in parsed data.
        
        Note that if data has no relationship entity, verification step will fail, but since
        the code handles it, might as well test it.
        """
        test_data = self._get_entity_data('animal_species_fact_data')
        mock_raise_fn = Mock(name='raise_fn', side_effect=ValueError)
        mock_subj_concept = Mock(name='subj_concept', concept_name='otter')
        mock_obj_concept = Mock(name='obj_concept', concept_name='mammal')
        create_concepts.return_value = (mock_subj_concept, mock_obj_concept)
        filter_entities.return_value = ([], [])

        # Make call
        self.assertRaises(ValueError,
                          FactManager._relationship_from_entity_data,
                          test_data, 
                          mock_raise_fn, 
                          new_fact_id=Mock()) 

        # Verify mocks
        mock_raise_fn.assert_called_once_with(
            "Expected 1 relationship entity for subject 'otter' and object 'mammal'; found 0")



@patch.object(FactManager, '_ensure_concept_with_type')
class ConceptsFromEntityDataTests(unittest.TestCase):
    """Verify behavior of FactManager._concept_from_entity_data
    """

    def setUp(self):
        """Allow tests to alter FactManager.SUBJECT_ENTITY_TYPES without impacting other tests.
        """
        self.orig_subject_types = FactManager.SUBJECT_ENTITY_TYPES

    def tearDown(self):
        FactManager.SUBJECT_ENTITY_TYPES = self.orig_subject_types

    def _get_entity_data(self, key):
        """Return JSON for 'entities' element of captured wit.ai response data with specified name.
        """
        response_data = getattr(wit_responses, key)
        return copy.deepcopy(response_data['outcomes'][0]['entities'])

    def test_concepts_from_entity_data(self, ensure_typed_concept):
        """Verify calls made by _concepts_from_entity_data.
        """
        # Set up mocks and test data
        test_data = self._get_entity_data('animal_species_fact_data')
        mock_raise_fn = Mock(name='raise_fn')
        mock_fact_id = Mock(name='fact_id')
        mock_concepts = [Mock(name='concept_1', concept_name='concept_1'),
                         Mock(name='concept_2', concept_name='concept_2')]
        ensure_typed_concept.side_effect = mock_concepts

        # Make call
        subj_concept, obj_concept = FactManager._concepts_from_entity_data(
            test_data, mock_raise_fn, new_fact_id=mock_fact_id)
        
        # Verify result
        self.assertEqual(set([subj_concept, obj_concept]), set(mock_concepts))

        # Verify mocks
        call_args_list = ensure_typed_concept.call_args_list
        self.assertEqual(2, len(call_args_list))
        self.assertEqual(set(['otter', 'mammal']), 
                         set([call_args[0][0][0]['value'] for call_args in call_args_list]))
        self.assertEqual(set(['animal', 'species']), 
                         set([call_args[0][1] for call_args in call_args_list]))
        for call_args in call_args_list:
            self.assertEqual(mock_fact_id, call_args[1]['new_fact_id'])

    def test_error__invalid_concept_data(self, ensure_typed_concept):
        """Verify error if ensure_concept_with_type does not return Concept.
        """
        # Set up mocks and test data
        test_data = self._get_entity_data('animal_species_fact_data')
        mock_raise_fn = Mock(name='raise_fn', side_effect=ValueError)
        ensure_typed_concept.return_value = None

        # Make call
        self.assertRaises(ValueError,
                          FactManager._concepts_from_entity_data,
                          test_data, 
                          mock_raise_fn, 
                          new_fact_id=Mock())

        self.assertEqual(1, mock_raise_fn.call_count)
        error_msg_arg = mock_raise_fn.call_args[0][0]
        self.assertTrue(error_msg_arg.startswith("Invalid data for concept_type"))
        self.assertTrue(("concept_type 'species'" in error_msg_arg 
                         or "concept_type 'animal'" in error_msg_arg))

    def test_error__multiple_subject_concepts(self, ensure_typed_concept):
        """Verify error if multiple subject concepts are found.
        """
        # Set up mocks and test data
        test_data = self._get_entity_data('animal_species_fact_data')
        FactManager.SUBJECT_ENTITY_TYPES = ('animal', 'vegetable')
        test_data['vegetable'] = [{'type': 'value', 'value': 'potato'}]
        mock_raise_fn = Mock(name='raise_fn', side_effect=ValueError)
        ensure_typed_concept.return_value = Mock(name='concept', concept_name='bunny')

        # Make call
        self.assertRaises(ValueError,
                          FactManager._concepts_from_entity_data,
                          test_data, 
                          mock_raise_fn, 
                          new_fact_id=Mock())
        mock_raise_fn.assert_called_once_with("Found multiple subject concepts: bunny, bunny")

    def test_error__no_subject_concept(self, ensure_typed_concept):
        """Verify error if no subject concept is found.
        """
        # Set up mocks and test data
        test_data = self._get_entity_data('animal_species_fact_data')
        del test_data['animal']
        mock_raise_fn = Mock(name='raise_fn', side_effect=ValueError)
        ensure_typed_concept.return_value = Mock(name='concept', concept_name='bunny')

        # Make call
        self.assertRaises(ValueError,
                          FactManager._concepts_from_entity_data,
                          test_data, 
                          mock_raise_fn, 
                          new_fact_id=Mock())
        mock_raise_fn.assert_called_once_with("No subject concept found")

    def test_error__multiple_object_concepts(self, ensure_typed_concept):
        """Verify error if multiple subject concepts are found.
        """
        # Set up mocks and test data
        test_data = self._get_entity_data('animal_species_fact_data')
        test_data['vegetable'] = [{'type': 'value', 'value': 'potato'}]
        mock_raise_fn = Mock(name='raise_fn', side_effect=ValueError)
        ensure_typed_concept.return_value = Mock(name='concept', concept_name='bunny')

        # Make call
        self.assertRaises(ValueError,
                          FactManager._concepts_from_entity_data,
                          test_data, 
                          mock_raise_fn, 
                          new_fact_id=Mock())
        mock_raise_fn.assert_called_once_with("Found multiple object concepts: bunny, bunny")
        
    def test_error__no_object_concept(self, ensure_typed_concept):
        """Verify error if no object concept is found.
        """
        # Set up mocks and test data
        test_data = self._get_entity_data('animal_species_fact_data')
        del test_data['species']
        mock_raise_fn = Mock(name='raise_fn', side_effect=ValueError)
        ensure_typed_concept.return_value = Mock(name='concept', concept_name='bunny')

        # Make call
        self.assertRaises(ValueError,
                          FactManager._concepts_from_entity_data,
                          test_data, 
                          mock_raise_fn, 
                          new_fact_id=Mock())
        mock_raise_fn.assert_called_once_with("No object concept found")


@patch.object(FactManager, '_ensure_relationship')
@patch.object(FactManager, '_ensure_concept')
@patch.object(FactManager, '_filter_entity_values')
class EnsureConceptWithTypeTests(unittest.TestCase):
    """Verify behavior of _ensure_concept_with_type method.
    """
    def test_ensure_concept_with_type(self, filter_entities, ensure_concept, ensure_relationship):
        """Verify calls made by _ensure_concept_with_type.
        """
        # Set up mocks and test data
        mock_concept_data = Mock(name='concept_data')
        test_concept_type = 'shoe'
        filter_entities.return_value = (['high heel'], [])
        mock_subj_concept = Mock(name='subj_concept', concept_name='high heel')
        mock_obj_concept = Mock(name='obj_concept', concept_name='shoe')
        ensure_concept.side_effect = [mock_subj_concept, mock_obj_concept]
        mock_rel = Mock(name='relationship', subject=mock_subj_concept)
        ensure_relationship.return_value = mock_rel
                                                           
        new_fact_id = Mock(name='new_fact_id')

        # Make call
        typed_concept = FactManager._ensure_concept_with_type(
            mock_concept_data, test_concept_type, new_fact_id)

        # Verify result
        self.assertEqual(mock_subj_concept, typed_concept)

        # Verify mocks
        filter_entities.assert_called_once_with(mock_concept_data)
        
        call_args_list = ensure_concept.call_args_list
        self.assertEqual(2, len(call_args_list))
        self.assertEqual('high heel', call_args_list[0][0][0])
        self.assertEqual('shoe', call_args_list[1][0][0])
        
        ensure_relationship.assert_called_once_with(mock_subj_concept, 
                                                    mock_obj_concept,
                                                    relationship_name='is',
                                                    new_fact_id=new_fact_id,
                                                    error_on_duplicate=False)

    def test_ensure_concept_with_type__suggestion(self, filter_entities, ensure_concept, 
                                                   ensure_relationship):
        """Verify calls made by _ensure_concept_with_type with subject suggestions
        """
        # Set up mocks and test data
        mock_concept_data = Mock(name='concept_data')
        test_concept_type = 'shoe'
        filter_entities.return_value = (['high heel'], ['other'])
        mock_subj_concept = Mock(name='subj_concept', concept_name='high heel')
        ensure_concept.side_effect = [mock_subj_concept, Mock(name='obj_concept')]
        mock_rel = Mock(name='relationship', subject=mock_subj_concept)
        ensure_relationship.return_value = mock_rel
                                                           
        # Make call
        with patch.object(logger, 'warn') as log_warn:
            typed_concept = FactManager._ensure_concept_with_type(
                mock_concept_data, test_concept_type, Mock(name='fact_id'))

        # Verify result
        self.assertEqual(mock_subj_concept, typed_concept)

        # Verify mocks
        log_warn.assert_called_once_with(
            "Skipping suggested subject 'other' for concept_type 'shoe'")

    def test_ensure_concept_with_type__multiple_subjects(self, filter_entities, ensure_concept, 
                                                         ensure_relationship):
        """Verify calls made by _ensure_concept_with_type with multiple subjects.
        """
        # Set up mocks and test data
        mock_concept_data = Mock(name='concept_data')
        test_concept_type = 'shoe'
        filter_entities.return_value = (['high heel', 'other'], [])
        mock_subj_concept = Mock(name='subj_concept', concept_name='high heel')
        ensure_concept.side_effect = [mock_subj_concept, Mock(name='obj_concept')]
        mock_rel = Mock(name='relationship', subject=mock_subj_concept)
        ensure_relationship.return_value = mock_rel
                                                           
        # Make call
        with patch.object(logger, 'warn') as log_warn:
            typed_concept = FactManager._ensure_concept_with_type(
                mock_concept_data, test_concept_type, Mock(name='fact_id'))

        # Verify result
        self.assertEqual(mock_subj_concept, typed_concept)

        # Verify mocks
        log_warn.assert_called_once_with(
            "Multiple subjects for concept_type 'shoe': {0}; ignoring all but 'high heel'".format(
                ['high heel', 'other']))


@patch.object(fact_model.Relationship, 'select_by_foreign_keys')
@patch.object(fact_model.RelationshipType, 'select_by_name')
class EnsureRelationshipTests(unittest.TestCase):
    """Verify behavior of _ensure_relationship.
    """
    def setUp(self):
        super(EnsureRelationshipTests, self).setUp()
        self.subj_concept = Mock(name='subj_concept', concept_id=uuid.uuid4())
        self.obj_concept = Mock(name='obj_concept', concept_id=uuid.uuid4())

    def test_ensure_relationship(self, select_type_by_name, select_relationship):
        """Verify calls made by _ensure_relationship for new relationship and relationship_name.
        """
        # Set up mocks and test data
        select_type_by_name.return_value = None
        select_relationship.return_value = None
        relationship_name = 'aunt'
        new_fact_id = uuid.uuid4()

        # Make call
        relationship = FactManager._ensure_relationship(self.subj_concept, 
                                                        self.obj_concept,
                                                        relationship_name=relationship_name,
                                                        new_fact_id=new_fact_id)

        # Verify result
        self.assertEqual(self.subj_concept, relationship.subject)
        self.assertEqual(self.obj_concept, relationship.object)
        self.assertEqual(relationship_name, relationship.relationship_names[0])
        self.assertIsNone(relationship.count)
        self.assertEqual(new_fact_id, relationship.fact_id)

    def test_ensure_relationship__existing_type(self, select_type_by_name, select_relationship):
        """Verify calls made by _ensure_relationship for existing relationship_type.
        """
        # Set up mocks and test data
        r_name = 'aunt'
        select_type_by_name.return_value = mock_rel_type = Mock(name='relationship_type',
                                                                relationship_type_name=r_name,
                                                                relationship_type_id=uuid.uuid4())
        select_relationship.return_value = None
        new_fact_id = uuid.uuid4()

        # Make call
        relationship = FactManager._ensure_relationship(self.subj_concept, 
                                                        self.obj_concept,
                                                        relationship_name=r_name,
                                                        new_fact_id=new_fact_id)

        # Verify result
        self.assertEqual(self.subj_concept, relationship.subject)
        self.assertEqual(self.obj_concept, relationship.object)
        self.assertEqual(mock_rel_type, relationship.relationship_types[0])
        self.assertIsNone(relationship.count)
        self.assertEqual(new_fact_id, relationship.fact_id)

        # Verify mocks
        select_type_by_name.assert_called_once_with(r_name)
        select_relationship.assert_called_once_with(self.subj_concept.concept_id,
                                                    self.obj_concept.concept_id,
                                                    mock_rel_type.relationship_type_id)

    def test_ensure_relationship__duplicate(self, select_type_by_name, select_relationship):
        """Verify calls made by _ensure_relationship for existing relationship.
        """
        # Set up mocks and test data
        r_name = 'aunt'
        select_type_by_name.return_value = mock_rel_type = Mock(name='relationship_type',
                                                                relationship_type_name=r_name)
        select_relationship.return_value = mock_rel = Mock(name='relationship')

        # Make call
        relationship = FactManager._ensure_relationship(self.subj_concept, 
                                                        self.obj_concept,
                                                        relationship_name=r_name,
                                                        new_fact_id=uuid.uuid4())
        # Verify result
        self.assertEqual(relationship, mock_rel)

    def test_ensure_relationship__duplicate_raise(self, select_type_by_name, select_relationship):
        """Verify raise for duplicate relationship with error_on_duplicate=True.
        """
        # Set up mocks and test data
        r_name = 'aunt'
        select_type_by_name.return_value = mock_rel_type = Mock(name='relationship_type',
                                                                relationship_type_name=r_name)
        select_relationship.return_value = mock_rel = Mock(name='relationship',
                                                           fact_id=uuid.uuid4())

        # Make call
        self.assertRaisesRegexp(
            DuplicateFactError,
            'Found existing fact {0} with subject={1}, object={2}, relationship={3}'.format(
                mock_rel.fact_id, self.subj_concept.concept_name, self.obj_concept.concept_name,
                r_name),
            FactManager._ensure_relationship,
            self.subj_concept, 
            self.obj_concept,
            relationship_name=r_name,
            new_fact_id=uuid.uuid4(),
            error_on_duplicate=True)

    def test_ensure_relationship__duplicate__no_count_specified(self, select_type_by_name, 
                                                                select_relationship):
        """Verify duplicate if relationship has count but no relationship_number is specified.
        """
        # Set up mocks and test data
        r_name = 'aunt'
        select_type_by_name.return_value = mock_rel_type = Mock(name='relationship_type',
                                                                relationship_type_name=r_name)
        select_relationship.return_value = mock_rel = Mock(name='relationship',
                                                           fact_id=uuid.uuid4(),
                                                           count=3)

        # Make call
        self.assertRaisesRegexp(
            DuplicateFactError,
            'Found existing fact {0} with subject={1}, object={2}, relationship={3}'.format(
                mock_rel.fact_id, self.subj_concept.concept_name, self.obj_concept.concept_name,
                r_name),
            FactManager._ensure_relationship,
            self.subj_concept, 
            self.obj_concept,
            relationship_name=r_name,
            new_fact_id=uuid.uuid4(),
            error_on_duplicate=True)

    def test_ensure_relationship__duplicate__matching_count(self, select_type_by_name, 
                                                            select_relationship):
        """Verify duplicate if relationship has count.
        """
        # Set up mocks and test data
        r_name = 'aunt'
        select_type_by_name.return_value = mock_rel_type = Mock(name='relationship_type',
                                                                relationship_type_name=r_name)
        select_relationship.return_value = mock_rel = Mock(name='relationship',
                                                           fact_id=uuid.uuid4(),
                                                           count=3)

        # Make call
        self.assertRaisesRegexp(
            DuplicateFactError,
            'Found existing fact {0} with subject={1}, object={2}, relationship={3}'.format(
                mock_rel.fact_id, self.subj_concept.concept_name, self.obj_concept.concept_name,
                r_name),
            FactManager._ensure_relationship,
            self.subj_concept, 
            self.obj_concept,
            relationship_name=r_name,
            relationship_number=3,
            new_fact_id=uuid.uuid4(),
            error_on_duplicate=True)

    def test_ensure_relationship__conflict(self, select_type_by_name, select_relationship):
        """Verify error on conflict with existing relationship count.
        """
        # Set up mocks and test data
        r_name = 'aunt'
        orig_count = 3
        new_count = 4
        select_type_by_name.return_value = mock_rel_type = Mock(name='relationship_type',
                                                                relationship_type_name=r_name)
        select_relationship.return_value = mock_rel = Mock(name='relationship', count=orig_count)

        # Make call
        self.assertRaisesRegexp(
            ConflictingFactError,
            ('Found conflicting fact {0} with subject={1}, object={2}, relationship={3}; '
             'persisted count conflicts with specified count: 3 vs 4').format(
                mock_rel.fact_id, self.subj_concept.concept_name, self.obj_concept.concept_name,
                r_name),
            FactManager._ensure_relationship,
            self.subj_concept, 
            self.obj_concept,
            relationship_name=r_name,
            relationship_number=new_count,
            new_fact_id=uuid.uuid4(),
            error_on_duplicate=True)

    def test_ensure_relationship__needs_update(self, select_type_by_name, select_relationship):
        """Verify relationship.count is set on existing relationship if relationship_number is sent.
        """
        # Set up mocks and test data
        r_name = 'aunt'
        select_type_by_name.return_value = mock_rel_type = Mock(name='relationship_type',
                                                                relationship_type_name=r_name)
        select_relationship.return_value = mock_rel = Mock(name='relationship',
                                                           count=None)
        self.assertIsNone(mock_rel.count)

        # Make call
        relationship = FactManager._ensure_relationship(self.subj_concept, 
                                                        self.obj_concept,
                                                        relationship_name=r_name,
                                                        relationship_number=2,
                                                        new_fact_id=uuid.uuid4())
        # Verify result
        self.assertEqual(mock_rel, relationship)
        self.assertEqual(2, mock_rel.count)


@patch.object(FactManager, '_delete_from_db_session')
@patch.object(fact_model.Relationship, 'select_by_fact_id')
@patch.object(fact_model.IncomingFact, 'select_by_id')
class DeleteFactTests(unittest.TestCase):
    """Verify behavior of delete_fact_by_id method.
    """
    def test_delete_fact_by_id(self, select_fact, select_relationships, delete_from_session):
        """Verify calls made by delete_fact_by_id.
        """
        # Set up mocks and test data
        fact_id = uuid.uuid4()
        select_fact.return_value = mock_fact = Mock(name='fact')
        mock_relationships = [Mock(name='relationship_1'), Mock(name='relationship_2')]
        select_relationships.return_value = mock_relationships
        
        # Make call
        deleted_fact_id = FactManager.delete_fact_by_id(fact_id)

        # Verify result
        self.assertEqual(fact_id, deleted_fact_id)

        # Verify mocks
        select_fact.assert_called_once_with(fact_id)
        select_relationships.assert_called_once_with(fact_id)

        call_args_list = delete_from_session.call_args_list
        self.assertEqual(len(mock_relationships) + 1, len(call_args_list))
        for i, call_args in enumerate(call_args_list):
            if i < len(mock_relationships):
                self.assertEqual(mock_relationships[i], call_args[0][0])
        self.assertEqual(mock_fact, call_args_list[-1][0][0])

    def test_delete_fact_by_id__no_fact_found(self, select_fact, select_relationships,
                                              delete_from_session):
        """Verify calls made by delete_fact_by_id when no fact is found.
        """
        # Set up mocks and test data
        fact_id = uuid.uuid4()
        select_fact.return_value = None
        
        # Make call
        deleted_fact_id = FactManager.delete_fact_by_id(fact_id)

        # Verify result
        self.assertIsNone(deleted_fact_id)

        # Verify mocks
        select_fact.assert_called_once_with(fact_id)
        self.assertEqual(0, select_relationships.call_count)
        self.assertEqual(0, delete_from_session.call_count)


class VerifyParsedFactDataTests(unittest.TestCase):
    """Verify logic of _verify_parsed_data method.
    """
    def setUp(self):
        self.parsed_data = copy.deepcopy(wit_responses.animal_species_fact_data)
#        self.mock_raise_fn = Mock(name='raise_fn', side_effect=lambda m: InvalidFactDataError(m))

    @staticmethod
    def raise_fn(message):
        raise InvalidFactDataError(message)

    def test_verify_fact_data(self):
        """Verify that valid data passes.
        """
        for attr in ('animal_leg_fact_data',
                     'animal_species_fact_data'):
            test_data = copy.deepcopy(getattr(wit_responses, attr))
            verified_data = FactManager._verify_parsed_fact_data(test_data, self.raise_fn)
            self.assertEqual(test_data['outcomes'][0], verified_data)

    def test_no_text_attr(self):
        """Verify that parsed data without _text attribute fails.
        """
        del self.parsed_data['_text']
        self.assertRaisesRegexp(InvalidFactDataError,
                                'No _text attribute',
                                FactManager._verify_parsed_fact_data,
                                self.parsed_data,
                                self.raise_fn)

    def test_multiple_outcomes(self):
        """Verify that parsed data with extra 'outcome' attributes fails.
        """
        self.parsed_data['outcomes'].append({})
        self.assertRaisesRegexp(InvalidFactDataError,
                                'Expected 1 outcome, found 2',
                                FactManager._verify_parsed_fact_data,
                                self.parsed_data,
                                self.raise_fn)

    def test_zero_outcomes(self):
        """Verify that parsed data with no 'outcome' attributes fails.
        """
        del self.parsed_data['outcomes']
        self.assertRaisesRegexp(InvalidFactDataError,
                                'Expected 1 outcome, found 0',
                                FactManager._verify_parsed_fact_data,
                                self.parsed_data,
                                self.raise_fn)

    def test_non_fact_intent(self):
        """Verify that parsed data with non-fact intent fails.
        """
        self.parsed_data['outcomes'][0]['intent'] = 'pumpkin_pie'
        self.assertRaisesRegexp(InvalidFactDataError,
                                "Non-fact outcome intent 'pumpkin_pie'",
                                FactManager._verify_parsed_fact_data,
                                self.parsed_data,
                                self.raise_fn)

    def test_low_confidence(self):
        """Verify that outcome with confidence below threshold does not pass.
        """
        self.parsed_data['outcomes'][0]['confidence'] = FactManager.CONFIDENCE_THRESHOLD - 0.1
        self.assertRaisesRegexp(InvalidFactDataError,
                                'Outcome confidence falls below threshold: 0.7 < 0.8',
                                FactManager._verify_parsed_fact_data,
                                self.parsed_data,
                                self.raise_fn)

    def test_too_few_entities(self):
        """Verify that outcome with fewer than 3 entities fails.
        """
        self.parsed_data['outcomes'][0]['entities'] = {'foo': [], 'bar': []}
        self.assertRaisesRegexp(InvalidFactDataError,
                                'Expected at least 3 entities, found 2',
                                FactManager._verify_parsed_fact_data,
                                self.parsed_data,
                                self.raise_fn)

    def test_multiple_relationship_entities(self):
        """Verify that outcome with multiple relationship entities fails.
        """
        self.parsed_data['outcomes'][0]['entities']['relationship'].append({})
        self.assertRaisesRegexp(InvalidFactDataError,
                                'Expected 1 relationship entity, found 2',
                                FactManager._verify_parsed_fact_data,
                                self.parsed_data,
                                self.raise_fn)

    def test_zero_relationship_entities(self):
        """Verify that outcome with zeror elationship entities fails.
        """
        self.parsed_data['outcomes'][0]['entities']['third_entity'] = []
        del self.parsed_data['outcomes'][0]['entities']['relationship']
        self.assertRaisesRegexp(InvalidFactDataError,
                                'Expected 1 relationship entity, found 0',
                                FactManager._verify_parsed_fact_data,
                                self.parsed_data,
                                self.raise_fn)

    def test_multiple_subject_entities(self):
        """Verify that outcome with multiple subject entities fails.
        """
        orig_subject_types = FactManager.SUBJECT_ENTITY_TYPES
        FactManager.SUBJECT_ENTITY_TYPES = ['animal', 'species']

        try:
            FactManager._verify_parsed_fact_data(self.parsed_data, self.raise_fn)
            self.fail("Did not expect to get here")
        except InvalidFactDataError as ex:
            msg = str(ex)
            self.assertTrue(msg.startswith('Expected 1 subject entity, found 2'))
            self.assertTrue('animal' in msg)
            self.assertTrue('species' in msg)
        finally:
            FactManager.SUBJECT_ENTITY_TYPES = orig_subject_types

    def test_zero_subject_entities(self):
        """Verify that outcome with zero subject entities fails.
        """
        orig_subject_types = FactManager.SUBJECT_ENTITY_TYPES
        FactManager.SUBJECT_ENTITY_TYPES = []

        try:
            FactManager._verify_parsed_fact_data(self.parsed_data, self.raise_fn)
            self.fail("Did not expect to get here")
        except InvalidFactDataError as ex:
            self.assertEqual('Expected 1 subject entity, found 0: []', str(ex))
        finally:
            FactManager.SUBJECT_ENTITY_TYPES = orig_subject_types



