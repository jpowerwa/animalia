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

