#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit tests for FactQuery class.
"""

from __future__ import unicode_literals

import logging
import unittest
import uuid

from mock import call, Mock, patch

from animalia.fact_query import FactQuery
import animalia.fact_model as fact_model


class FactQueryTests(unittest.TestCase):
    """Verify behavior of FactQuery methods.
    """
    def test_init__default(self):
        """Verify init with no args.
        """
        fact_query = FactQuery()
        self.assertIsNone(fact_query.parsed_query)
    
    def test_init(self):
        """Verify init.
        """
        mock_query = Mock(name='parsed_query')
        fact_query = FactQuery(parsed_query=mock_query)
        self.assertEqual(mock_query, fact_query.parsed_query)

    @patch.object(FactQuery, '_find_answer_function')
    def test_find_answer(self, find_fn):
        """Verify calls made by find_answer.
        """
        # Set up mocks and test data
        find_fn.return_value = mock_fn = Mock(name='mock_fn',
                                              return_value='hi')
        mock_query = Mock(name='parsed_query')
        fact_query = FactQuery(parsed_query=mock_query)
        
        # Make call
        answer = fact_query.find_answer()

        # Verify result
        self.assertEqual('hi', answer)

        # Verify mocks
        self.assertEqual(1, find_fn.call_count)

    @patch.object(FactQuery, '_find_answer_function')
    def test_find_answer__no_answer_fn(self, find_fn):
        """Verify ValueError if no answer function exists.
        """
        # Set up mocks and test data
        find_fn.return_value = None
        mock_query = Mock(name='parsed_query')
        fact_query = FactQuery(parsed_query=mock_query)

        # Make call
        self.assertRaisesRegexp(ValueError,
                                'No answer function found',
                                fact_query.find_answer)

    def test_find_answer__no_query(self):
        """Verify ValueError if no query is set.
        """
        fact_query = FactQuery()
        self.assertRaisesRegexp(ValueError,
                                'No query to answer',
                                fact_query.find_answer)

    def test_find_answer_function(self):
        """Verify logic of find_answer_function for query intent.
        """
        mock_parsed_query = Mock(name='parsed_query',
                                 intent='animal_eat_query')
        fact_query = FactQuery(parsed_query=mock_parsed_query)
        fn = fact_query._find_answer_function()
        self.assertEqual(fn, fact_query._animal_eat_query)

    def test_find_answer_function__ci(self):
        """Verify logic of find_answer_function for query intent that is capitalized.
        """
        mock_parsed_query = Mock(name='parsed_query',
                                 intent='ANIMAL_EAT_QUERY')
        fact_query = FactQuery(parsed_query=mock_parsed_query)
        fn = fact_query._find_answer_function()
        self.assertEqual(fn, fact_query._animal_eat_query)

    def test_find_answer_function__question(self):
        """Verify logic of find_answer_function for question intent.
        """
        mock_parsed_query = Mock(name='parsed_query',
                                 intent='animal_eat_question')
        fact_query = FactQuery(parsed_query=mock_parsed_query)
        fn = fact_query._find_answer_function()
        self.assertEqual(fn, fact_query._animal_eat_query)

    def test_find_answer_function__does_not_exist(self):
        """Verify logic of find_answer_function for unrecognized intent.
        """
        mock_parsed_query = Mock(name='parsed_query',
                                 intent='foo_bar_query')
        fact_query = FactQuery(parsed_query=mock_parsed_query)
        fn = fact_query._find_answer_function()
        self.assertIsNone(fn)

    def test_find_answer_function__fact(self):
        """Verify logic of find_answer_function for fact intent.
        """
        mock_parsed_query = Mock(name='parsed_query',
                                 intent='animal_eat_fact')
        fact_query = FactQuery(parsed_query=mock_parsed_query)
        fn = fact_query._find_answer_function()
        self.assertEqual(fn, fact_query._animal_attribute_query)

    def test_get_synonymous_names(self):
        """Verify logic of get_synonymous_name with singular name.
        """
        names = FactQuery._get_synonymous_names('mammal')
        self.assertEqual(['mammal', 'mammals'], names)

    def test_get_synonymous_names__plural(self):
        """Verify logic of get_synonymous_names with plural name.
        """
        names = FactQuery._get_synonymous_names('mammals')
        self.assertEqual(['mammal', 'mammals'], names)

    @patch.object(FactQuery, '_select_matching_relationships')
    def test_concept_is_species(self, select_relationships):
        """Verify calls made by _concept_is_species.
        """
        select_relationships.return_value = mock_matches = Mock(name='matches')
        result = FactQuery._concept_is_species('bird')
        self.assertTrue(result)
        select_relationships.assert_called_once_with('is',
                                                     subject_name=['bird', 'birds'],
                                                     object_name='species',
                                                     stop_on_match=True)

    @patch.object(FactQuery, '_select_matching_relationships')
    def test_concept_is_species__fail(self, select_relationships):
        """Verify _concept_is_species when no matches are found
        """
        select_relationships.return_value = []
        result = FactQuery._concept_is_species('bird')
        self.assertFalse(result)

    @patch.object(FactQuery, '_select_matching_relationships')
    def test_select_by_concept_type(self, select_relationships):
        """Verify calls made by select_by_concept_type.
        """
        select_relationships.return_value = [Mock(subject='hello'), Mock(subject='kitty')]
        mock_concept_types = Mock(name='concept_types')

        result = FactQuery._select_by_concept_type(mock_concept_types)
        self.assertEqual(['hello', 'kitty'], result)
        select_relationships.assert_called_once_with('is', object_name=mock_concept_types)

    @patch.object(FactQuery, '_select_matching_relationships')
    def test_select_by_concept_type__no_matches(self, select_relationships):
        """Verify return value of select_by_concept_type when no results are found.
        """
        select_relationships.return_value = []

        result = FactQuery._select_by_concept_type(Mock(name='concept_types'))
        self.assertEqual([], result)


class SelectMatchingRelationshipTests(unittest.TestCase):

    @patch.object(fact_model.Relationship, 'select_by_values')
    def test_select_matching_relationships(self, select_by_values):
        """Verify calls made by _select_matching_relationships.
        """
        # Set up mocks and test data
        select_by_values.return_value = ['one', 'two']
        test_relationship_type_name = 'eats'
        test_subject_name = 'otter'
        test_object_name = 'mussels'
        test_rel_number = 99
        
        # Make call
        matches = FactQuery._select_matching_relationships(test_relationship_type_name,
                                                           subject_name=test_subject_name,
                                                           object_name=test_object_name,
                                                           relationship_number=test_rel_number)
        # Verify result
        self.assertEqual(['one', 'two'], matches)

        # Verify mocks
        select_by_values.assert_called_once_with(relationship_type_name=test_relationship_type_name,
                                                 subject_name=test_subject_name,
                                                 object_name=test_object_name,
                                                 relationship_number=test_rel_number)

    @patch.object(fact_model.Relationship, 'select_by_values')
    def test_select_matching_relationships__multiple_subs__one_obj(self, select_by_values):
        """Verify calls made by _select_matching_relationships for multiple subjects.
        """
        # Set up mocks and test data
        select_by_values.side_effect = [['one', 'two'], ['three']]
        test_relationship_type_name = 'eats'
        test_subject_names = ['otter', 'otters']
        test_object_name = 'mussels'
        
        # Make call
        matches = FactQuery._select_matching_relationships(test_relationship_type_name,
                                                           subject_name=test_subject_names,
                                                           object_name=test_object_name)
        # Verify result
        self.assertEqual(['one', 'two', 'three'], matches)

        # Verify mocks
        call_args_list = select_by_values.call_args_list
        self.assertEqual(2, len(call_args_list))
        for i, call_args in enumerate(call_args_list):
            expected_call = call(relationship_type_name='eats',
                                 relationship_number=None,
                                 subject_name=test_subject_names[i],
                                 object_name=test_object_name)
            self.assertEqual(expected_call, call_args)

    @patch.object(fact_model.Relationship, 'select_by_values')
    def test_select_matching_relationships__multiple_subs__no_obj(self, select_by_values):
        """Verify calls made by _select_matching_relationships for multiple subjects and no object.
        """
        # Set up mocks and test data
        select_by_values.side_effect = [['one', 'two'], ['three']]
        test_relationship_type_name = 'eats'
        test_subject_names = ['otter', 'otters']
        
        # Make call
        matches = FactQuery._select_matching_relationships(test_relationship_type_name,
                                                           subject_name=test_subject_names)
        # Verify result
        self.assertEqual(['one', 'two', 'three'], matches)

        # Verify mocks
        call_args_list = select_by_values.call_args_list
        self.assertEqual(2, len(call_args_list))
        for i, call_args in enumerate(call_args_list):
            expected_call = call(relationship_type_name='eats',
                                 relationship_number=None,
                                 subject_name=test_subject_names[i],
                                 object_name=None)
            self.assertEqual(expected_call, call_args)

    @patch.object(fact_model.Relationship, 'select_by_values')
    def test_select_matching_relationships__multiple_objs__one_sub(self, select_by_values):
        """Verify calls made by _select_matching_relationships for multiple objects.
        """
        # Set up mocks and test data
        select_by_values.side_effect = [['one', 'two'], ['three']]
        test_relationship_type_name = 'eats'
        test_subject_name = 'otter'
        test_object_names = ['mussel', 'mussels']
        
        # Make call
        matches = FactQuery._select_matching_relationships(test_relationship_type_name,
                                                           subject_name=test_subject_name,
                                                           object_name=test_object_names)
        # Verify result
        self.assertEqual(['one', 'two', 'three'], matches)

        # Verify mocks
        call_args_list = select_by_values.call_args_list
        self.assertEqual(2, len(call_args_list))
        for i, call_args in enumerate(call_args_list):
            expected_call = call(relationship_type_name='eats',
                                 relationship_number=None,
                                 subject_name=test_subject_name,
                                 object_name=test_object_names[i])
            self.assertEqual(expected_call, call_args)

    @patch.object(fact_model.Relationship, 'select_by_values')
    def test_select_matching_relationships__multiple_objs__no_sub(self, select_by_values):
        """Verify calls made by _select_matching_relationships for multiple objs and no subject.
        """
        # Set up mocks and test data
        select_by_values.side_effect = [['one', 'two'], ['three']]
        test_relationship_type_name = 'eats'
        test_object_names = ['mussel', 'mussels']
        
        # Make call
        matches = FactQuery._select_matching_relationships(test_relationship_type_name,
                                                           object_name=test_object_names)
        # Verify result
        self.assertEqual(['one', 'two', 'three'], matches)

        # Verify mocks
        call_args_list = select_by_values.call_args_list
        self.assertEqual(2, len(call_args_list))
        for i, call_args in enumerate(call_args_list):
            expected_call = call(relationship_type_name='eats',
                                 relationship_number=None,
                                 subject_name=None,
                                 object_name=test_object_names[i])
            self.assertEqual(expected_call, call_args)

    @patch.object(fact_model.Relationship, 'select_by_values')
    def test_select_matching_relationships__multiple_subs__multiple_objs(self, select_by_values):
        """Verify calls made by _select_matching_relationships for multiple subs and objs
        """
        # Set up mocks and test data
        select_by_values.side_effect = [['one', 'two'], ['three'], ['four'], ['five', 'six']]
        test_relationship_type_name = 'eats'
        test_subject_names = ['otter', 'otters']
        test_object_names = ['mussel', 'mussels']
        
        # Make call
        matches = FactQuery._select_matching_relationships(test_relationship_type_name,
                                                           subject_name=test_subject_names,
                                                           object_name=test_object_names)
        # Verify result
        self.assertEqual(['one', 'two', 'three', 'four', 'five', 'six'], matches)

        # Verify mocks
        call_args_list = select_by_values.call_args_list
        self.assertEqual(4, len(call_args_list))
        i = 0
        for subj_idx in range(0,1):
            for obj_idx in range (0,1):
                call_args = call_args_list[i]
                expected_call = call(relationship_type_name='eats',
                                     relationship_number=None,
                                     subject_name=test_subject_names[subj_idx],
                                     object_name=test_object_names[obj_idx])
                self.assertEqual(expected_call, call_args)
                i += 1

    @patch.object(fact_model.Relationship, 'select_by_values')
    def test_select_matching_relationships__multiple_subs__stop_on_match(self, select_by_values):
        """Verify calls made by _select_matching_relationships when stop_on_match is True
        """
        # Set up mocks and test data
        select_by_values.side_effect = [[], [], ['one', 'two']]
        test_relationship_type_name = 'eats'
        test_subject_names = ['otter', 'otters']
        test_object_names = ['mussels', 'mussel']
        
        # Make call
        matches = FactQuery._select_matching_relationships(test_relationship_type_name,
                                                           subject_name=test_subject_names,
                                                           object_name=test_object_names,
                                                           stop_on_match=True)
        # Verify result
        self.assertEqual(['one', 'two'], matches)

        # Verify mocks
        call_args_list = select_by_values.call_args_list
        self.assertEqual(3, len(call_args_list))
        i = 0
        for subj_idx in range(0,1):
            obj_idx = 0
            call_args = call_args_list[i]
            expected_call = call(relationship_type_name='eats',
                                 relationship_number=None,
                                 subject_name=test_subject_names[subj_idx],
                                 object_name=test_object_names[obj_idx])
            self.assertEqual(expected_call, call_args)
            i += 1


class FilterRelationshipsByConceptTypeTests(unittest.TestCase):
    """Verify methods having to do with filtering subjects and objects by species.
    """
    def test_filter_relationships_by_concept_type__subject(self):
        """Verify calls made by _filter_relationships_by_concept_type for 'subject' attr.
        """
        # Set up mocks and test data
        concept_types = ['bird', 'birds']
        mock_match_0 = Mock(name='mock_match_0',
                            subject=Mock(name='mock_subject_0',
                                         concept_name='mock_subject_0',
                                         concept_types=['bird', 'not_bird']))

        mock_match_1 = Mock(name='mock_match_1',
                            subject=Mock(name='mock_subject_1',
                                         concept_name='mock_subject_1',
                                         concept_types=['not_bird', 'also_not_bird']))

        mock_match_2 = Mock(name='mock_match_2',
                            subject=Mock(name='mock_subject_2',
                                         concept_name='mock_subject_2',
                                         concept_types=['not_bird', 'birds']))

        mock_matches = [mock_match_0, mock_match_1, mock_match_2]

        # Make call
        filtered_matches = FactQuery._filter_relationships_by_concept_type(
            mock_matches, concept_types=concept_types, relationship_attr='subject')

        # Verify results
        self.assertEqual([mock_match_0, mock_match_2], filtered_matches)

    def test_filter_relationships_by_concept_type__object(self):
        """Verify calls made by _filter_relationships_by_concept_type for 'object' attr.
        """
        # Set up mocks and test data
        concept_types = ['bird', 'birds']
        mock_match_0 = Mock(name='mock_match_0',
                            object=Mock(name='mock_subject_0',
                                        concept_name='mock_subject_0',
                                        concept_types=['bird', 'not_bird']))

        mock_match_1 = Mock(name='mock_match_1',
                            object=Mock(name='mock_subject_1',
                                        concept_name='mock_subject_1',
                                        concept_types=['not_bird', 'also_not_bird']))

        mock_match_2 = Mock(name='mock_match_2',
                            object=Mock(name='mock_subject_2',
                                        concept_name='mock_subject_2',
                                        concept_types=['not_bird', 'birds']))

        mock_matches = [mock_match_0, mock_match_1, mock_match_2]

        # Make call
        filtered_matches = FactQuery._filter_relationships_by_concept_type(
            mock_matches, concept_types=concept_types, relationship_attr='object')

        # Verify results
        self.assertEqual([mock_match_0, mock_match_2], filtered_matches)


class AnimalAttributeQueryTests(unittest.TestCase):
    """Verify logic of _animal_attribute_query.
    """
    @patch.object(FactQuery, '_select_matching_relationships')
    def test_animal_attribute_query(self, select_relationships):
        """Verify calls made by _animal_attribute_query.
        """
        # Set up mocks and test data
        select_relationships.return_value = [Mock(name='mock_1'), Mock(name='mock_2')]
        parsed_query = Mock(name='parsed_query',
                            text='do herons have wings',
                            subject_name='herons',
                            object_name='wings',
                            relationship_type_name='have',
                            relationship_number=2)
        fact_query = FactQuery(parsed_query=parsed_query)

        # Make call
        result = fact_query._animal_attribute_query()
        
        # Verify results
        self.assertEqual('yes', result)

        # Verify mocks
        select_relationships.assert_called_once_with('have',
                                                     subject_name=['heron', 'herons'],
                                                     object_name=['wing', 'wings'],
                                                     relationship_number=2,
                                                     stop_on_match=True)

    @patch.object(FactQuery, '_concept_is_species')
    @patch.object(FactQuery, '_select_matching_relationships')
    def test_animal_attribute_query__no_match(self, select_relationships, concept_is_species):
        """Verify calls made by _animal_attribute_query.
        """
        # Set up mocks and test data
        select_relationships.return_value = []
        concept_is_species.return_value = False
        parsed_query = Mock(name='parsed_query',
                            text='do herons have wings',
                            subject_name='herons',
                            object_name='wings',
                            relationship_type_name='have',
                            relationship_number=2)
        fact_query = FactQuery(parsed_query=parsed_query)

        # Make call
        result = fact_query._animal_attribute_query()
        
        # Verify results
        self.assertEqual('no', result)

        # Verify mocks
        select_relationships.assert_called_once_with('have',
                                                     subject_name=['heron', 'herons'],
                                                     object_name=['wing', 'wings'],
                                                     relationship_number=2,
                                                     stop_on_match=True)

    @patch.object(FactQuery, '_filter_relationships_by_concept_type')
    @patch.object(FactQuery, '_concept_is_species')
    @patch.object(FactQuery, '_select_matching_relationships')
    def test_animal_attribute_query__species_subject(self, select_relationships, 
                                                     concept_is_species, filter_by_concept_type):
        """Verify calls made by _animal_attribute_query when species is subject.
        """
        # Set up mocks and test data
        mock_1 = Mock(name='mock_1')
        mock_2 = Mock(name='mock_2')
        mock_3 = Mock(name='mock_3')
        select_relationships.side_effect = [[], [mock_1, mock_2, mock_3]]
        concept_is_species.return_value = True
        filter_by_concept_type.return_value = [mock_1, mock_2]

        parsed_query = Mock(name='parsed_query',
                            text='do birds have wings',
                            subject_name='birds',
                            object_name='wings',
                            relationship_type_name='have',
                            relationship_number=2)
        fact_query = FactQuery(parsed_query=parsed_query)

        # Make call
        result = fact_query._animal_attribute_query()
        
        # Verify results
        self.assertEqual('yes', result)

        # Verify mocks
        call_args_list = select_relationships.call_args_list
        self.assertEqual(2, len(call_args_list))
        expected_calls = [
            call('have', subject_name=['bird', 'birds'], object_name=['wing', 'wings'],
                 relationship_number=2, stop_on_match=True),
            call('have', object_name=['wing', 'wings'], relationship_number=2, stop_on_match=True)]
        self.assertEqual(expected_calls, call_args_list)

    @patch.object(FactQuery, '_filter_relationships_by_concept_type')
    @patch.object(FactQuery, '_concept_is_species')
    @patch.object(FactQuery, '_select_matching_relationships')
    def test_animal_attribute_query__species_object(self, select_relationships, 
                                                    concept_is_species, filter_by_concept_type):
        """Verify calls made by _animal_attribute_query when species is subject.
        """
        # Set up mocks and test data
        mock_1 = Mock(name='mock_1')
        mock_2 = Mock(name='mock_2')
        mock_3 = Mock(name='mock_3')
        select_relationships.side_effect = [[], [mock_1, mock_2, mock_3]]
        concept_is_species.side_effect = [False, True]
        filter_by_concept_type.return_value = [mock_1]

        parsed_query = Mock(name='parsed_query',
                            text='do herons eat mammals',
                            subject_name='herons',
                            object_name='mammals',
                            relationship_type_name='eat',
                            relationship_number=2)
        fact_query = FactQuery(parsed_query=parsed_query)

        # Make call
        result = fact_query._animal_attribute_query()
        
        # Verify results
        self.assertEqual('yes', result)

        # Verify mocks
        call_args_list = select_relationships.call_args_list
        self.assertEqual(2, len(call_args_list))
        expected_calls = [
            call('eat', subject_name=['heron', 'herons'], object_name=['mammal', 'mammals'],
                 relationship_number=2, stop_on_match=True),
            call('eat', subject_name=['heron', 'herons'], relationship_number=2, stop_on_match=True)]
        self.assertEqual(expected_calls, call_args_list)


class AnimalValuesQueryTests(unittest.TestCase):
    """Verify logic of _animal_values_query.
    
    Used by _animal_eat_query and _animal_place_query.
    """
    @patch.object(FactQuery, '_concept_is_species')
    @patch.object(FactQuery, '_select_matching_relationships')
    def test_animal_values_query(self, select_relationships, concept_is_species):
        """Verify _animal_values_query for non-species subject.
        """
        # Set up mocks and test data
        concept_is_species.return_value = False
        mock_1 = Mock(name='mock_1', object=Mock(concept_name='mosquitoes'))
        mock_2 = Mock(name='mock_2', object=Mock(concept_name='flies'))
        select_relationships.return_value = [mock_1, mock_2]
        fact_query = FactQuery()

        # Make call
        result = fact_query._animal_values_query(relationship_type_name='eat', subject_name='frog')

        # Verify result
        self.assertEqual(['flies', 'mosquitoes'], result)

        # Verify mocks
        concept_is_species.assert_called_once_with('frog')
        select_relationships.assert_called_once_with('eat', subject_name=['frog', 'frogs'])

    @patch.object(FactQuery, '_filter_relationships_by_concept_type')
    @patch.object(FactQuery, '_concept_is_species')
    @patch.object(FactQuery, '_select_matching_relationships')
    def test_animal_values_query__species_subject(self, select_relationships, concept_is_species,
                                                  filter_by_concept_type):
        """Verify _animal_values_query for subject that is specise.
        """
        # Set up mocks and test data
        concept_is_species.return_value = True
        mock_1 = Mock(name='mock_1', object=Mock(concept_name='mosquitoes'))
        mock_2 = Mock(name='mock_2', object=Mock(concept_name='flies'))
        mock_3 = Mock(name='mock_2', object=Mock(concept_name='salmon'))
        select_relationships.return_value = [mock_1, mock_2, mock_3]
        filter_by_concept_type.return_value = [mock_1, mock_2]
        fact_query = FactQuery()

        # Make call
        result = fact_query._animal_values_query(relationship_type_name='eat', subject_name='reptiles')

        # Verify result
        self.assertEqual(['flies', 'mosquitoes'], result)

        # Verify mocks
        concept_is_species.assert_called_once_with('reptiles')
        select_relationships.assert_called_once_with('eat')
        filter_by_concept_type.assert_called_once_with(
            [mock_1, mock_2, mock_3], concept_types=['reptile', 'reptiles'], relationship_attr='subject')


class WhichAnimalQueryTests(unittest.TestCase):
    """Verify logic of _which_animal_query.
    """
    @patch.object(FactQuery, '_filter_relationships_by_concept_type')
    @patch.object(FactQuery, '_concept_is_species')
    @patch.object(FactQuery, '_select_matching_relationships')
    def test_which_animals(self, select_relationships, concept_is_species, 
                                    filter_by_concept_type):
        """Scenario of relationship='eat', subject='animals', object='bugs'.
        """
        # Set up mocks and test data
        parsed_query = Mock(name='parsed_query',
                            text='which animals eat bugs',
                            subject_name='animals',
                            object_name='bugs',
                            relationship_type_name='eat',
                            relationship_number=3,
                            relationship_negation=False)
        fact_query = FactQuery(parsed_query=parsed_query)

        mock_match_1 = Mock(name='match_1',
                            subject=Mock(concept_name='subject_1'))
        mock_match_2 = Mock(name='match_2',
                            subject=Mock(concept_name='subject_2'))
        select_relationships.return_value = [mock_match_1, mock_match_2]
        concept_is_species.return_value = False
        filter_by_concept_type.return_value = [mock_match_1, mock_match_2]

        # Make call
        results = fact_query._which_animal_query()

        # Verify results
        self.assertEqual(set(['subject_1', 'subject_2']), set(results))

        # Verify mocks
        select_relationships.assert_called_once_with(
            'eat', object_name=['bug', 'bugs'], relationship_number=3)

        call_args_list = concept_is_species.call_args_list
        self.assertEqual(2, len(call_args_list))
        self.assertEqual(call('bugs'), call_args_list[0])
        self.assertEqual(call('animals'), call_args_list[1])

        filter_by_concept_type.assert_called_once_with(
            [mock_match_1, mock_match_2], concept_types=['animal'], relationship_attr='subject')
        
    @patch.object(FactQuery, '_select_by_concept_type')
    @patch.object(FactQuery, '_filter_relationships_by_concept_type')
    @patch.object(FactQuery, '_concept_is_species')
    @patch.object(FactQuery, '_select_matching_relationships')
    def test_which_animals__negation(self, select_relationships, concept_is_species, 
                                    filter_by_concept_type, select_by_concept_type):
        """Scenario of relationship='eat', subject='animals', object='bugs', negation=True.
        """
        # Set up mocks and test data
        parsed_query = Mock(name='parsed_query',
                            text='which animals do not eat bugs',
                            subject_name='animals',
                            object_name='bugs',
                            relationship_type_name='eat',
                            relationship_number=3,
                            relationship_negation=True)
        fact_query = FactQuery(parsed_query=parsed_query)

        concept_1 = Mock(concept_name='subject_1')
        concept_2 = Mock(concept_name='subject_2')
        concept_3 = Mock(concept_name='subject_3')
        concept_4 = Mock(concept_name='subject_4')
        mock_match_1 = Mock(name='match_1', subject=concept_1)
        mock_match_2 = Mock(name='match_2', subject=concept_2)

        select_relationships.return_value = [mock_match_1, mock_match_2]
        concept_is_species.return_value = False
        filter_by_concept_type.return_value = [mock_match_1, mock_match_2]
        select_by_concept_type.return_value = [concept_1, concept_2, concept_3, concept_4]

        # Make call
        results = fact_query._which_animal_query()

        # Verify results
        self.assertEqual(set(['subject_3', 'subject_4']), set(results))

        # Verify mocks
        select_by_concept_type.assert_called_once_with(['animal'])

    @patch.object(FactQuery, '_filter_relationships_by_concept_type')
    @patch.object(FactQuery, '_concept_is_species')
    @patch.object(FactQuery, '_select_matching_relationships')
    def test_which_reptiles__species_subject(self, select_relationships, concept_is_species, 
                                             filter_by_concept_type):
        """Scenario of relationship='eat', subject='reptiles', object='bugs'.
        """
        # Set up mocks and test data
        parsed_query = Mock(name='parsed_query',
                            text='which reptiles eat bugs',
                            subject_name='reptiles',
                            object_name='bugs',
                            relationship_type_name='eat',
                            relationship_number=3,
                            relationship_negation=False)
        fact_query = FactQuery(parsed_query=parsed_query)

        mock_match_1 = Mock(name='match_1',
                            subject=Mock(concept_name='subject_1'))
        mock_match_2 = Mock(name='match_2',
                            subject=Mock(concept_name='subject_2'))
        select_relationships.return_value = [mock_match_1, mock_match_2]
        concept_is_species.side_effect = [False, True]
        filter_by_concept_type.return_value = [mock_match_1, mock_match_2]

        # Make call
        results = fact_query._which_animal_query()

        # Verify results
        self.assertEqual(set(['subject_1', 'subject_2']), set(results))

        # Verify mocks
        select_relationships.assert_called_once_with(
            'eat', object_name=['bug', 'bugs'], relationship_number=3)

        call_args_list = concept_is_species.call_args_list
        self.assertEqual(2, len(call_args_list))
        self.assertEqual(call('bugs'), call_args_list[0])
        self.assertEqual(call('reptiles'), call_args_list[1])

        filter_by_concept_type.assert_called_once_with(
            [mock_match_1, mock_match_2], 
            concept_types=['reptile', 'reptiles'], 
            relationship_attr='subject')

    @patch.object(FactQuery, '_filter_relationships_by_concept_type')
    @patch.object(FactQuery, '_concept_is_species')
    @patch.object(FactQuery, '_select_matching_relationships')
    def test_which_animals__species_object(self, select_relationships, concept_is_species, 
                                           filter_by_concept_type):
        """Scenario of relationship='eat', subject='animals', object='reptiles'.
        """
        # Set up mocks and test data
        parsed_query = Mock(name='parsed_query',
                            text='which animals eat reptiles',
                            subject_name='animals',
                            object_name='reptiles',
                            relationship_type_name='eat',
                            relationship_number=3,
                            relationship_negation=False)
        fact_query = FactQuery(parsed_query=parsed_query)

        mock_match_1 = Mock(name='match_1',
                            subject=Mock(concept_name='subject_1'))
        mock_match_2 = Mock(name='match_2',
                            subject=Mock(concept_name='subject_2'))
        mock_match_3 = Mock(name='match_3',
                            subject=Mock(concept_name='subject_3'))
        select_relationships.side_effect = [[mock_match_1, mock_match_2],
                                            [mock_match_1, mock_match_3]]
        concept_is_species.side_effect = [True, False]
        filter_by_concept_type.side_effect = [
            [mock_match_1, mock_match_3],
            [mock_match_1, mock_match_2, mock_match_1, mock_match_3]]

        # Make call
        results = fact_query._which_animal_query()

        # Verify results
        self.assertEqual(set(['subject_1', 'subject_2', 'subject_3']), set(results))

        # Verify mocks
        call_args_list = select_relationships.call_args_list
        self.assertEqual(2, len(call_args_list))
        expected_calls = [
            call('eat', object_name=['reptile', 'reptiles'], relationship_number=3),
            call('eat', relationship_number=3)]
        self.assertEqual(expected_calls, call_args_list)

        call_args_list = concept_is_species.call_args_list
        self.assertEqual(2, len(call_args_list))
        self.assertEqual(call('reptiles'), call_args_list[0])
        self.assertEqual(call('animals'), call_args_list[1])

        call_args_list = filter_by_concept_type.call_args_list
        self.assertEqual(2, len(call_args_list))
        expected_calls = [
            call([mock_match_1, mock_match_3], 
                 concept_types=['reptile', 'reptiles'], 
                 relationship_attr='object'),
             call([mock_match_1, mock_match_2, mock_match_1, mock_match_3],
                  concept_types=['animal'],
                  relationship_attr='subject')]
        self.assertEqual(expected_calls, call_args_list)
        
        
