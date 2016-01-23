#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit tests for FactQuery class.
"""

from __future__ import unicode_literals

import logging
import unittest
import uuid

from mock import Mock, patch

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

    def test_find_answer_function__does_not_exit(self):
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

    def test_get_synonymous_species_names(self):
        """Verify logic of get_synonymous_species_name with singular name.
        """
        names = FactQuery()._get_synonymous_species_names('mammal')
        self.assertEqual(['mammal', 'mammals'], names)

    def test_get_synonymous_species_names__plural(self):
        """Verify logic of get_synonymous_species_names with plural name.
        """
        names = FactQuery()._get_synonymous_species_names('mammals')
        self.assertEqual(['mammal', 'mammals'], names)

    def test_query_object_is_species(self):
        """Verify logic of query_object_is_species.
        """
        parsed_query = Mock(name='parsed_query', object_type='species')
        fact_query = FactQuery(parsed_query=parsed_query)
        self.assertTrue(fact_query._query_object_is_species())

    def test_query_object_is_species__false(self):
        """Verify logic of query_object_is_species when object is not species.
        """
        parsed_query = Mock(name='parsed_query', object_type='place')
        fact_query = FactQuery(parsed_query=parsed_query)
        self.assertFalse(fact_query._query_object_is_species())

    @patch.object(FactQuery, '_select_matching_relationships')
    def test_query_subject_is_species(self, select_relationships):
        """Verify logic of query_subject_is_species.
        """
        # Set up mocks and test data
        select_relationships.side_effect = [[], [Mock(name='match')]]
        parsed_query = Mock(name='parsed_query', subject_name='mammal')
        fact_query = FactQuery(parsed_query=parsed_query)
        
        # Verify result
        self.assertTrue(fact_query._query_subject_is_species())
        
        # Verify mocks
        call_args_list = select_relationships.call_args_list
        self.assertEqual(2, len(call_args_list))
        self.assertEqual('is', call_args_list[0][0][0])
        self.assertEqual({'subject_name': 'mammal', 'object_name': 'species'}, 
                         call_args_list[0][1])
        self.assertEqual('is', call_args_list[1][0][0])
        self.assertEqual({'subject_name': 'mammals', 'object_name': 'species'}, 
                         call_args_list[1][1])
        
    @patch.object(FactQuery, '_select_matching_relationships')
    def test_query_subject_is_species__false(self, select_relationships):
        """Verify logic of query_subject_is_species when no matching relationship is found.
        """
        # Set up mocks and test data
        select_relationships.side_effect = [[], []]
        parsed_query = Mock(name='parsed_query', subject_name='mammal')
        fact_query = FactQuery(parsed_query=parsed_query)
        
        # Verify result
        self.assertFalse(fact_query._query_subject_is_species())
        
        # Verify mocks
        self.assertEqual(2, len(select_relationships.call_args_list))

    @patch.object(FactQuery, '_select_matching_relationships')
    def test_select_all_animals(self, select_relationships):
        """Verify calls made by _select_all_animals.
        """
        # Set up mocks and test data
        select_relationships.return_value = mock_matches = Mock(name='matches')
        fact_query = FactQuery()
        
        # Make call
        matches = fact_query._select_all_animals()
        
        # Verify result
        self.assertEqual(mock_matches, matches)

        # Verify mocks
        select_relationships.assert_called_once_with('is', object_name='animal')

    @patch.object(fact_model.Relationship, 'select_by_names')
    def test_select_matching_relationships(self, select_by_names):
        """Verify calls made by _select_matching_relationships.
        """
        # Set up mocks and test data
        select_by_names.return_value = mock_matches = Mock(name='matches')
        test_relationship_type_name = 'eats'
        test_subject_name = 'otter'
        test_object_name = 'mussels'
        fact_query = FactQuery()
        
        # Make call
        matches = fact_query._select_matching_relationships(test_relationship_type_name,
                                                            subject_name=test_subject_name,
                                                            object_name=test_object_name)
        
        # Verify result
        self.assertEqual(mock_matches, matches)

        # Verify mocks
        select_by_names.assert_called_once_with(relationship_type_name=test_relationship_type_name,
                                                subject_name=test_subject_name,
                                                object_name=test_object_name)

    @patch.object(fact_model.Relationship, 'select_by_names')
    def test_select_matching_relationships__with_relationship_number(self, select_by_names):
        """Verify calls made by _select_matching_relationships with relationship_number.
        """
        # Set up mocks and test data
        m1 = Mock(name='mock_match_1', count=None)
        m2 = Mock(name='mock_match_2', count=3)
        m3 = Mock(name='mock_match_3', count=1)
        m4 = Mock(name='mock_match_2', count=3)
        select_by_names.return_value = mock_matches = [m1, m2, m3, m4]
        test_relationship_type_name = 'eats'
        test_subject_name = 'otter'
        test_object_name = 'mussels'
        test_relationship_number = 3
        fact_query = FactQuery()
        
        # Make call
        matches = fact_query._select_matching_relationships(
            test_relationship_type_name,
            subject_name=test_subject_name,
            object_name=test_object_name,
            relationship_number=test_relationship_number)
        
        # Verify result
        self.assertEqual([m2, m4], matches)

        # Verify mocks
        select_by_names.assert_called_once_with(relationship_type_name=test_relationship_type_name,
                                                subject_name=test_subject_name,
                                                object_name=test_object_name)


class SpeciesFilterTests(unittest.TestCase):
    """Verify methods having to do with filtering subjects and objects by species.
    """

    @patch.object(FactQuery, '_filter_relationships_by_species')
    def test_filter_objects_by_species(self, filter_relationships):
        """Verify calls made by _filter_objects_by_species.
        """
        # Set up mocks and test data
        mock_matches = Mock(name='matches')
        filter_relationships.return_value = mock_filtered_matches = Mock(name='filtered_matches')
        object_name = 'fish'
        parsed_query = Mock(name='parsed_query', object_name=object_name)
        fact_query = FactQuery(parsed_query=parsed_query)
        
        # Make call
        filtered_matches = fact_query._filter_objects_by_species(mock_matches)
        
        # Verify result
        self.assertEqual(mock_filtered_matches, filtered_matches)

        # Verify mocks
        filter_relationships.assert_called_once_with(mock_matches, 'fish', 'object')

    @patch.object(FactQuery, '_filter_relationships_by_species')
    def test_filter_subjects_by_species(self, filter_relationships):
        """Verify calls made by _filter_subjects_by_species.
        """
        # Set up mocks and test data
        mock_matches = Mock(name='matches')
        filter_relationships.return_value = mock_filtered_matches = Mock(name='filtered_matches')
        subject_name = 'fish'
        parsed_query = Mock(name='parsed_query', subject_name=subject_name)
        fact_query = FactQuery(parsed_query=parsed_query)
        
        # Make call
        filtered_matches = fact_query._filter_subjects_by_species(mock_matches)
        
        # Verify result
        self.assertEqual(mock_filtered_matches, filtered_matches)

        # Verify mocks
        filter_relationships.assert_called_once_with(mock_matches, 'fish', 'subject')

    @patch.object(FactQuery, '_get_synonymous_species_names')
    def test_filter_relationships_by_species(self, get_species_names):
        """Verify calls made by _filter_relationships_by_species.
        """
        # Set up mocks and test data
        species_name = 'bird'
        get_species_names.return_value = ['bird', 'birds']
        mock_match_0 = Mock(name='mock_match_0',
                            subject=Mock(name='mock_subject_0',
                                         concept_name='mock_subject_0',
                                         concept_types=[Mock(name='concept_type_0_0',
                                                             concept_name='bird'),
                                                        Mock(name='concept_type_0_1',
                                                             concept_name='not_bird')]))
        mock_match_1 = Mock(name='mock_match_1',
                            subject=Mock(name='mock_subject_1',
                                         concept_name='mock_subject_1',
                                         concept_types=[Mock(name='concept_type_1_0',
                                                             concept_name='not_bird'),
                                                        Mock(name='concept_type_1_1',
                                                             concept_name='also_not_bird')]))

        mock_match_2 = Mock(name='mock_match_2',
                            subject=Mock(name='mock_subject_2',
                                         concept_name='mock_subject_2',
                                         concept_types=[Mock(name='concept_type_2_0',
                                                             concept_name='not_bird'),
                                                        Mock(name='concept_type_1_1',
                                                             concept_name='birds')]))

        mock_matches = [mock_match_0, mock_match_1, mock_match_2]
        fact_query = FactQuery(parsed_query=Mock(name='parsed_query'))

        # Make call
        filtered_matches = fact_query._filter_relationships_by_species(
            mock_matches, species_name, 'subject')

        # Verify results
        self.assertEqual(2, len(filtered_matches))
        self.assertEqual(set(['mock_subject_0', 'mock_subject_2']),
                         set([m.subject.concept_name for m in filtered_matches]))

