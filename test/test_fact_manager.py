#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit tests for fact_manager.py
"""

from __future__ import unicode_literals

import copy
import json
import logging
import unittest
import uuid

from mock import Mock, call, patch

import animalia.exc as exc
import animalia.fact_model as fact_model
from animalia.fact_manager import logger, FactManager
from animalia.parsed_sentence import ParsedSentence
import wit_responses

# Set log level for unit tests
logger.setLevel(logging.WARN)


class FactManagerTests(unittest.TestCase):
    """Verify behavior of simple FactManager methods.
    """

    @patch.object(fact_model.db.session, 'commit')
    @patch.object(FactManager, '_save_parsed_fact')
    @patch.object(ParsedSentence, 'from_wit_response')
    @patch.object(FactManager, '_query_wit')
    @patch.object(fact_model.IncomingFact, 'select_by_text')
    @patch.object(FactManager, '_normalize_sentence')
    def test_fact_from_sentence(self, normalize_sentence, select_fact, query_wit, parse_response,
                                save_fact, commit_txn):
        """Verify calls made by fact_from_sentence.
        """
        # Set up mocks and test data
        mock_sentence = Mock(name='sentence')
        normalize_sentence.return_value = mock_normalized_sentence = Mock(name='norm_sentence')
        select_fact.return_value = None
        test_data = copy.deepcopy(wit_responses.animal_species_fact_data)
        query_wit.return_value = test_data
        mock_parsed_sentence = Mock(name='parsed_sentence',
                                    is_fact=Mock(return_value=True),
                                    relationship_negation=False)
        parse_response.return_value = mock_parsed_sentence
        save_fact.return_value = saved_fact = Mock(name='saved_fact')

        # Make call
        fact = FactManager.fact_from_sentence(mock_sentence)

        # Verify result
        self.assertEqual(saved_fact, fact)
        
        # Verify mocks
        normalize_sentence.assert_called_once_with(mock_sentence)
        select_fact.assert_called_once_with(mock_normalized_sentence)
        query_wit.assert_called_once_with(mock_normalized_sentence)
        parse_response.assert_called_once_with(test_data)
        save_fact.assert_called_once_with(mock_parsed_sentence)
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

    @patch.object(ParsedSentence, 'validate_fact')
    @patch.object(ParsedSentence, 'from_wit_response')
    @patch.object(FactManager, '_query_wit')
    @patch.object(fact_model.IncomingFact, 'select_by_text')
    @patch.object(FactManager, '_normalize_sentence')
    def test_fact_from_sentence__validation_failed(self, normalize_sentence, select_fact, 
                                                   query_wit, from_response, validate_fact):
        """Verify raise if fact fails validation.
        """
        # Set up mocks and test data
        mock_sentence = Mock(name='sentence')
        normalize_sentence.return_value = mock_normalized_sentence = Mock(name='norm_sentence')
        select_fact.return_value = None
        test_data = copy.deepcopy(wit_responses.animal_species_fact_data)
        query_wit.return_value = json.dumps(test_data)
        mock_parsed_sentence = Mock(name='parsed_sentence', 
                                    intent='horse farm',
                                    is_fact=Mock(return_value=False),
                                    relationship_negation=False)
        from_response.return_value = ParsedSentence()
        validate_fact.side_effect = ValueError("Bad fact")

        self.assertRaisesRegexp(exc.InvalidFactDataError,
                                "Invalid fact: Bad fact; wit_response=",
                                FactManager.fact_from_sentence,
                                mock_sentence)
           
    @patch.object(FactManager, '_normalize_sentence')
    def test_fact_from_sentence__no_sentence(self, normalize_sentence):
        """Verify SentenceParseError if no sentence is provided.
        """
        for empty in (None, ''):
            normalize_sentence.return_value = empty
            self.assertRaisesRegexp(exc.SentenceParseError,
                                    'Empty fact sentence provided',
                                    FactManager.fact_from_sentence, 
                                    'the otter lives in the river')

    def test_fact_from_sentence__no_normalized_sentence(self):
        """Verify SentenceParseError if sentence normalizes to empty string.
        """
        self.assertRaisesRegexp(exc.SentenceParseError,
                                'Empty fact sentence provided',
                                FactManager.fact_from_sentence, 
                                '')

    def test_normalize_sentence(self):
        """Verify functionality of _normalize_sentence.
        """
        sentence = 'The otter, lives in the river!'
        self.assertEqual('the otter lives in the river', FactManager._normalize_sentence(sentence))

    @patch.object(fact_model.db.session, 'commit')
    @patch.object(FactManager, '_merge_to_db_session')
    @patch.object(FactManager, '_ensure_relationship')
    @patch.object(FactManager, '_ensure_concept')
    def test_add_concept(self, ensure_concept, ensure_relationship, merge, commit):
        """Verify calls made by add_concept.
        """
        # Set up mocks and test data
        mock_concept_1 = Mock(name='concept_1')
        mock_concept_2 = Mock(name='concept_2')
        mock_rel = Mock(name='relationship')
        ensure_concept.side_effect = [mock_concept_1, mock_concept_2]
        ensure_relationship.return_value = mock_rel
        concept_name = 'otters'
        concept_type = 'animals'

        # Make call
        FactManager.add_concept(concept_name, concept_type)

        # Verify mocks
        expected_calls = [call(concept_name), call(concept_type)]
        self.assertEqual(expected_calls, ensure_concept.call_args_list)

        ensure_relationship.assert_called_once_with(
            mock_concept_1, mock_concept_2, relationship_type_name='is', error_on_duplicate=False)
        merge.assert_called_once_with(mock_rel)
        self.assertEqual(1, commit.call_count)

    @patch.object(fact_model.db.session, 'commit')
    @patch.object(FactManager, '_merge_to_db_session')
    @patch.object(FactManager, '_ensure_relationship')
    @patch.object(FactManager, '_ensure_concept')
    def test_add_concept__normalize(self, ensure_concept, ensure_relationship, merge, commit):
        """Verify calls made by add_concept for singular, uppercase concept_name and concept_type.
        """
        # Set up mocks and test data
        ensure_concept.side_effect = [Mock(), Mock()]
        ensure_relationship.return_value = Mock()
        concept_name = 'OTTER'
        concept_type = 'ANIMAL'

        # Make call
        FactManager.add_concept(concept_name, concept_type)

        # Verify mocks
        expected_calls = [call('otters'), call('animals')]
        self.assertEqual(expected_calls, ensure_concept.call_args_list)


@patch.object(FactManager, '_merge_to_db_session')
@patch.object(FactManager, '_ensure_relationship')
@patch.object(FactManager, '_ensure_concept_with_type')
class SaveParsedFactTests(unittest.TestCase):
    """Verify behavior of FactManager._save_parsed_fact.
    """

    def test_save_parsed_fact(self, ensure_concept, ensure_relationship, merge_to_session):
        """Verify calls made by _save_parsed_fact.
        """
        # Set up mocks and test data
        parsed_sentence = ParsedSentence(subject_name='otter',
                                         subject_type='animal',
                                         object_name='mammal',
                                         object_type='species',
                                         relationship_type_name='is a')
        mock_subject_concept = Mock(name='subject_concept')
        mock_object_concept = Mock(name='object_concept')
        ensure_concept.side_effect = [mock_subject_concept, mock_object_concept]
        ensure_relationship.return_value = mock_relationship = Mock(name='relationship')
        mock_saved_relationship = Mock(name='saved_relationship')
        mock_saved_fact = Mock(name='saved_fact')
        merge_to_session.side_effect = [mock_saved_relationship, mock_saved_fact]

        # Make call
        saved_fact = FactManager._save_parsed_fact(parsed_sentence)
        
        # Verify result
        self.assertEqual(mock_saved_fact, saved_fact)

        # Verify mocks
        self.assertEqual(2, ensure_concept.call_count)
        call_args_list = ensure_concept.call_args_list
        self.assertEqual(('otter', 'animal'), call_args_list[0][0])
        self.assertTrue(isinstance(call_args_list[0][1]['new_fact_id'], uuid.UUID))
        self.assertEqual(('mammal', 'species'), call_args_list[1][0])
        self.assertTrue(isinstance(call_args_list[1][1]['new_fact_id'], uuid.UUID))
        new_fact_id = call_args_list[1][1]['new_fact_id']

        ensure_relationship.assert_called_once_with(mock_subject_concept,
                                                    mock_object_concept,
                                                    relationship_type_name='is a',
                                                    relationship_number=None,
                                                    new_fact_id=new_fact_id,
                                                    error_on_duplicate=True)

    @patch.object(fact_model.IncomingFact, 'select_by_id')
    def test_save_parsed_fact__duplicate_fact(self, select_fact, ensure_concept, 
                                              ensure_relationship, merge_to_session):
        """Verify calls made by _save_parsed_fact when relationship is duplicate.
        """
        # Set up mocks and test data
        parsed_sentence = ParsedSentence(subject_name='otter',
                                         subject_type='animal',
                                         object_name='mammal',
                                         object_type='species',
                                         relationship_type_name='is a')
        dup_fact_id = uuid.uuid4()
        select_fact.return_value = mock_fact = Mock(name='fact')
        ensure_concept.side_effect = [Mock(name='subject_concept'), Mock(name='object_concept')]
        ensure_relationship.side_effect = exc.DuplicateFactError('uh oh',
                                                                 duplicate_fact_id=dup_fact_id)

        # Make call
        with patch.object(logger, 'warn') as log_warn:
            saved_fact = FactManager._save_parsed_fact(parsed_sentence)
        
        # Verify return value
        self.assertEqual(mock_fact, saved_fact)
        
        # Verify mocks
        log_warn.assert_called_once_with('uh oh')
        select_fact.assert_called_once_with(dup_fact_id)


class EnsureConceptWithTypeTests(unittest.TestCase):
    """Verify behavior of _ensure_concept_with_type method.
    """
    @patch.object(FactManager, '_ensure_relationship')
    @patch.object(FactManager, '_ensure_concept')
    def test_ensure_concept_with_type(self, ensure_concept, ensure_relationship):
        """Verify calls made by _ensure_concept_with_type.
        """
        # Set up mocks and test data
        concept_name = 'high heel'
        concept_type = 'shoes'
        mock_subj_concept = Mock(name='subj_concept', 
                                 concept_name=concept_name, 
                                 concept_types=[])
        mock_subj_type_concept = Mock(name='obj_concept', 
                                      concept_name=concept_type, 
                                      concept_types=['accessory'])
        ensure_concept.side_effect = [mock_subj_concept, mock_subj_type_concept]
        ensure_relationship.return_value = mock_rel = Mock(name='relationship',
                                                           subject=mock_subj_concept)
        mock_fact_id = Mock(name='new_fact_id')

        # Make call
        typed_concept = FactManager._ensure_concept_with_type(
            concept_name, concept_type, new_fact_id=mock_fact_id)

        # Verify result
        self.assertEqual(mock_subj_concept, typed_concept)

        # Verify mocks
        call_args_list = ensure_concept.call_args_list
        self.assertEqual(2, len(call_args_list))
        self.assertEqual(concept_name, call_args_list[0][0][0])
        self.assertEqual(concept_type, call_args_list[1][0][0])
        
        ensure_relationship.assert_called_once_with(mock_subj_concept, 
                                                    mock_subj_type_concept,
                                                    relationship_type_name='is',
                                                    new_fact_id=mock_fact_id,
                                                    error_on_duplicate=False)

    @patch.object(FactManager, '_ensure_relationship')
    @patch.object(FactManager, '_ensure_concept')
    def test_ensure_concept_with_type__loop(self, ensure_concept, ensure_relationship):
        """Verify calls made by _ensure_concept_with_type when loop is detected.
        """
        # Set up mocks and test data
        concept_name = 'high heel'
        concept_type = 'shoes'
        conflicting_fact_id = uuid.uuid4()
        mock_subj_concept = Mock(name='subj_concept', 
                                 concept_name=concept_name, 
                                 concept_types=[])
        mock_concept_type_rels = [Mock(name='foo_relationship',
                                       fact_id=uuid.uuid4(),
                                       object=Mock(concept_name='foo')),
                                  Mock(name='concept_type_relationship',
                                       fact_id=conflicting_fact_id,
                                       object=Mock(concept_name=concept_name))]
        mock_subj_type_concept = Mock(name='obj_concept', 
                                      concept_name=concept_type, 
                                      concept_types=['foo', concept_name],
                                      concept_type_relationships=mock_concept_type_rels)
        ensure_concept.side_effect = [mock_subj_concept, mock_subj_type_concept]

        # Make call
        try:
            FactManager._ensure_concept_with_type(concept_name, concept_type)
            self.fail("Did not expect to get here")
        except exc.ConflictingFactError as ex:
            expected_msg = ("Cannot add relationship 'high heel is shoes'; "
                            "existing relationship 'shoes is high heel'")
            self.assertEqual(expected_msg, ex.message)
            self.assertEqual(conflicting_fact_id, ex.conflicting_fact_id)

        self.assertEqual(0, ensure_relationship.call_count)


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
        """Verify calls made for new relationship and relationship_type_name.
        """
        # Set up mocks and test data
        select_type_by_name.return_value = None
        select_relationship.return_value = None
        relationship_type_name = 'aunt'
        new_fact_id = uuid.uuid4()

        # Make call
        relationship = FactManager._ensure_relationship(
            self.subj_concept, 
            self.obj_concept,
            relationship_type_name=relationship_type_name,
            new_fact_id=new_fact_id)

        # Verify result
        self.assertEqual(self.subj_concept, relationship.subject)
        self.assertEqual(self.obj_concept, relationship.object)
        self.assertEqual(relationship_type_name, relationship.relationship_type_names[0])
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
                                                        relationship_type_name=r_name,
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
                                                        relationship_type_name=r_name,
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
            exc.DuplicateFactError,
            'Found existing fact {0} with subject={1}, object={2}, relationship={3}'.format(
                mock_rel.fact_id, self.subj_concept.concept_name, self.obj_concept.concept_name,
                r_name),
            FactManager._ensure_relationship,
            self.subj_concept, 
            self.obj_concept,
            relationship_type_name=r_name,
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
            exc.DuplicateFactError,
            'Found existing fact {0} with subject={1}, object={2}, relationship={3}'.format(
                mock_rel.fact_id, self.subj_concept.concept_name, self.obj_concept.concept_name,
                r_name),
            FactManager._ensure_relationship,
            self.subj_concept, 
            self.obj_concept,
            relationship_type_name=r_name,
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
            exc.DuplicateFactError,
            'Found existing fact {0} with subject={1}, object={2}, relationship={3}'.format(
                mock_rel.fact_id, self.subj_concept.concept_name, self.obj_concept.concept_name,
                r_name),
            FactManager._ensure_relationship,
            self.subj_concept, 
            self.obj_concept,
            relationship_type_name=r_name,
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
            exc.ConflictingFactError,
            ('Found conflicting fact {0} with subject={1}, object={2}, relationship={3}; '
             'persisted count conflicts with specified count: 3 vs 4').format(
                mock_rel.fact_id, self.subj_concept.concept_name, self.obj_concept.concept_name,
                r_name),
            FactManager._ensure_relationship,
            self.subj_concept, 
            self.obj_concept,
            relationship_type_name=r_name,
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
                                                        relationship_type_name=r_name,
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

