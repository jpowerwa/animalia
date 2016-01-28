#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit tests for parsed_sentence.py
"""

from __future__ import unicode_literals

import copy
import json
import logging
import unittest

from mock import Mock, patch

from animalia.parsed_sentence import logger, ParsedSentence
import wit_responses

# Set log level for unit tests
logger.setLevel(logging.WARN)


class FromWitResponseTests(unittest.TestCase):
    """Verify ParsedSentence.from_wit_response behavior.
    """
    def setUp(self):
        self.parsed_data = copy.deepcopy(wit_responses.animal_species_fact_data)

    def test_from_wit_response(self):
        """Verify that valid data passes from_wit_response factory method.
        """
        parsed_sentence = ParsedSentence.from_wit_response(self.parsed_data)
        self.assertEqual('the otter is a mammal', parsed_sentence.text)
        self.assertEqual(0.9, parsed_sentence.confidence)
        self.assertEqual('animal_species_fact', parsed_sentence.intent)
        self.assertEqual('otters', parsed_sentence.subject_name)
        self.assertEqual('animals', parsed_sentence.subject_type)
        self.assertEqual('mammals', parsed_sentence.object_name)
        self.assertEqual('species', parsed_sentence.object_type)
        self.assertEqual('is a', parsed_sentence.relationship_type_name)
        self.assertIsNone(parsed_sentence.relationship_number)
        self.assertFalse(parsed_sentence.relationship_negation)
        self.assertEqual(json.dumps(self.parsed_data), parsed_sentence.orig_response)

    def test_from_wit_response__normalize_concepts(self):
        """Verify that concept names are normalized when wit_response is processed.
        """
        entities = self.parsed_data['outcomes'][0]['entities']
        entities['animal'][0]['value'] = 'OTTER'
        entities['species'][0]['value'] = 'MAMMAL'
        parsed_sentence = ParsedSentence.from_wit_response(self.parsed_data)

        self.assertEqual('the otter is a mammal', parsed_sentence.text)
        self.assertEqual(0.9, parsed_sentence.confidence)
        self.assertEqual('animal_species_fact', parsed_sentence.intent)
        self.assertEqual('otters', parsed_sentence.subject_name)
        self.assertEqual('animals', parsed_sentence.subject_type)
        self.assertEqual('mammals', parsed_sentence.object_name)
        self.assertEqual('species', parsed_sentence.object_type)
        self.assertEqual('is a', parsed_sentence.relationship_type_name)
        self.assertIsNone(parsed_sentence.relationship_number)
        self.assertFalse(parsed_sentence.relationship_negation)
        self.assertEqual(json.dumps(self.parsed_data), parsed_sentence.orig_response)

    def test_from_wit_response__number_entity(self):
        """Verify that valid data with 'number' entity passes from_wit_response factory method.
        """
        test_data = copy.deepcopy(wit_responses.animal_leg_fact_data)
        parsed_sentence = ParsedSentence.from_wit_response(test_data)
        self.assertEqual('the otter has four legs', parsed_sentence.text)
        self.assertEqual(0.994, parsed_sentence.confidence)
        self.assertEqual('animal_leg_fact', parsed_sentence.intent)
        self.assertEqual('otters', parsed_sentence.subject_name)
        self.assertEqual('animals', parsed_sentence.subject_type)
        self.assertEqual('legs', parsed_sentence.object_name)
        self.assertEqual('body_parts', parsed_sentence.object_type)
        self.assertEqual('has', parsed_sentence.relationship_type_name)
        self.assertEqual('4', parsed_sentence.relationship_number)
        self.assertFalse(parsed_sentence.relationship_negation)
        self.assertEqual(json.dumps(test_data), parsed_sentence.orig_response)

    def test_from_wit_response__relationship_negation(self):
        """Verify that 'negation' entity is detected.
        """
        test_data = copy.deepcopy(wit_responses.which_animal_question__negated)
        parsed_sentence = ParsedSentence.from_wit_response(test_data)
        self.assertEqual('which animals do not eat fish', parsed_sentence.text)
        self.assertEqual(0.998, parsed_sentence.confidence)
        self.assertEqual('which_animal_question', parsed_sentence.intent)
        self.assertEqual('animals', parsed_sentence.subject_name)
        self.assertEqual('animals', parsed_sentence.subject_type)
        self.assertEqual('fish', parsed_sentence.object_name)
        self.assertEqual('foods', parsed_sentence.object_type)
        self.assertEqual('eat', parsed_sentence.relationship_type_name)
        self.assertTrue(parsed_sentence.relationship_negation)
        self.assertEqual(json.dumps(test_data), parsed_sentence.orig_response)

    def test_from_wit_response__multiple_relationship_type_names(self):
        """Verify that outcome with multiple relationship names is handled.
        """
        self.parsed_data['outcomes'][0]['entities']['relationship'].append(
            {'type': 'value', 'value': 'another_relationship'})
        parsed_sentence = ParsedSentence.from_wit_response(self.parsed_data)
        self.assertEqual('the otter is a mammal', parsed_sentence.text)
        self.assertEqual('is a', parsed_sentence.relationship_type_name)

    def test_from_wit_response__no_text_attr(self):
        """Verify that parsed data without _text attribute fails.
        """
        del self.parsed_data['_text']
        self.assertRaisesRegexp(ValueError,
                                'Response data has no _text attribute',
                                ParsedSentence.from_wit_response,
                                self.parsed_data)

    def test_from_wit_response__multiple_outcomes(self):
        """Verify that parsed data with extra 'outcome' attributes fails.
        """
        self.parsed_data['outcomes'].append({})
        self.assertRaisesRegexp(ValueError,
                                'Expected 1 outcome, found 2',
                                ParsedSentence.from_wit_response,
                                self.parsed_data)

    def test_from_wit_response__low_confidence(self):
        """Verify that outcome with confidence below threshold results in warning.
        """
        self.parsed_data['outcomes'][0]['confidence'] = ParsedSentence.CONFIDENCE_THRESHOLD - 0.1
        with patch.object(logger, 'warn') as log_warn:
            parsed_sentence = ParsedSentence.from_wit_response(self.parsed_data)
        self.assertEqual(1, log_warn.call_count)
        self.assertTrue(log_warn.call_args[0][0].startswith(
                'Outcome confidence falls below threshold:'))
        self.assertEqual('the otter is a mammal', parsed_sentence.text)
        self.assertEqual('is a', parsed_sentence.relationship_type_name)

    def test_from_wit_response__multiple_subject_entities(self):
        """Verify that outcome with multiple subject entities fails.
        """
        orig_subject_types = ParsedSentence.SUBJECT_ENTITY_TYPES
        ParsedSentence.SUBJECT_ENTITY_TYPES = ['animal', 'vegetable']
        entities = self.parsed_data['outcomes'][0]['entities']
        entities['vegetable'] = [{'type': 'value', 'value': 'carrot'}]
        del entities['species']

        try:
            ParsedSentence.from_wit_response(self.parsed_data)
            self.fail("Did not expect to get here")
        except ValueError as ex:
            msg = str(ex)
            self.assertTrue(msg.startswith('Parsed multiple subject entities: '))
            self.assertTrue('animal' in msg)
            self.assertTrue('vegetable' in msg)
        finally:
            ParsedSentence.SUBJECT_ENTITY_TYPES = orig_subject_types

    def test_from_wit_response__multiple_object_entities(self):
        """Verify that outcome with multiple object entities fails.
        """
        entities = self.parsed_data['outcomes'][0]['entities']
        entities['vegetable'] = [{'type': 'value', 'value': 'carrot'}]
        entities['pickle'] = [{'type': 'value', 'value': 'gherkin'}]
        del entities['species']

        try:
            ParsedSentence.from_wit_response(self.parsed_data)
            self.fail("Did not expect to get here")
        except ValueError as ex:
            msg = str(ex)
            self.assertTrue(msg.startswith('Parsed multiple object entities: '))
            self.assertTrue('pickle' in msg)
            self.assertTrue('vegetable' in msg)

    def test_from_wit_response__alt_subject_entity__subject(self):
        """Verify alt_subject used as subject.
        """
        del self.parsed_data['outcomes'][0]['entities']['animal']
        parsed_sentence = ParsedSentence.from_wit_response(self.parsed_data)
        self.assertEqual('species', parsed_sentence.subject_type)
        self.assertEqual('mammals', parsed_sentence.subject_name)
        self.assertIsNone(parsed_sentence.object_type)
        self.assertIsNone(parsed_sentence.object_name)

    def test_from_wit_response__alt_subject_entity__object(self):
        """Verify alt_subject used as object.
        """
        parsed_sentence = ParsedSentence.from_wit_response(self.parsed_data)
        self.assertEqual('species', parsed_sentence.object_type)
        self.assertEqual('mammals', parsed_sentence.object_name)
        self.assertEqual('animals', parsed_sentence.subject_type)
        self.assertEqual('otters', parsed_sentence.subject_name)

    def test_from_wit_response__alt_subject_entity__extra(self):
        """Verify that outcome with unused alt_subject fails.
        """
        entities = self.parsed_data['outcomes'][0]['entities']
        entities['vegetable'] = [{'type': 'value', 'value': 'carrot'}]
        self.assertRaisesRegexp(ValueError,
                                'Parsed alt_subject but both subject and object were found',
                                ParsedSentence.from_wit_response,
                                self.parsed_data)

    def test_from_wit_response__multiple_alt_subject_entities(self):
        """Verify that outcome with multiple alt_subject entities fails.
        """
        orig_alt_subject_types = ParsedSentence.ALT_SUBJECT_ENTITY_TYPES
        ParsedSentence.ALT_SUBJECT_ENTITY_TYPES = ['species', 'vegetable']
        entities = self.parsed_data['outcomes'][0]['entities']
        entities['vegetable'] = [{'type': 'value', 'value': 'carrot'}]

        try:
            ParsedSentence.from_wit_response(self.parsed_data)
            self.fail("Did not expect to get here")
        except ValueError as ex:
            msg = str(ex)
            self.assertTrue(msg.startswith('Parsed multiple alt subject entities: '))
            self.assertTrue('species' in msg)
            self.assertTrue('vegetable' in msg)
        finally:
            ParsedSentence.ALT_SUBJECT_ENTITY_TYPES = orig_alt_subject_types


class GetEntityValueTests(unittest.TestCase):
    """Verify ParsedSentence._get_entity_value behavior.
    """
    def test_get_entity_value(self):
        """Verify result of _get_entity_value.
        """
        # Set up mocks and test data
        entity_type = 'vegetable'
        entity_data = [{'type': 'season', 'value': 'summer'}, {'type': 'value', 'value': 'tomato'}]
        
        # Make call
        entity_value, suggested = ParsedSentence._get_entity_value(entity_type, entity_data)
        
        # Verify results
        self.assertEqual('tomato', entity_value)
        self.assertFalse(suggested)
        
    def test_get_entity_value__case_insensitive(self):
        """Verify result of _get_entity_value is lowercased.
        """
        # Set up mocks and test data
        entity_type = 'vegetable'
        entity_data = [{'type': 'season', 'value': 'summer'}, {'type': 'value', 'value': 'TOMATO'}]
        
        # Make call
        entity_value, suggested = ParsedSentence._get_entity_value(entity_type, entity_data)
        
        # Verify results
        self.assertEqual('tomato', entity_value)
        self.assertFalse(suggested)

    def test_get_entity_value__ignore_suggested(self):
        """Verify result of _get_entity_value when extra suggested value is present.
        """
        # Set up mocks and test data
        entity_type = 'vegetable'
        entity_data = [{'type': 'season', 'value': 'summer'}, 
                       {'type': 'value', 'value': 'love apple', 'suggested': True},
                       {'type': 'value', 'value': 'tomato'}]
        
        # Make call
        with patch.object(logger, 'warn') as log_warn:
            entity_value, suggested = ParsedSentence._get_entity_value(entity_type, entity_data)

        log_warn.assert_called_once_with(
            "Ignoring suggested values for entity 'vegetable': ['love apple']")
        
        # Verify results
        self.assertEqual('tomato', entity_value)
        self.assertFalse(suggested)
        
    def test_get_entity_value__use_suggested(self):
        """Verify result of _get_entity_value when only suggested value is present.
        """
        # Set up mocks and test data
        entity_type = 'vegetable'
        entity_data = [{'type': 'season', 'value': 'summer'}, 
                       {'type': 'value', 'value': 'love apple', 'suggested': True}]
        
        # Make call
        with patch.object(logger, 'warn') as log_warn:
            entity_value, suggested = ParsedSentence._get_entity_value(entity_type, entity_data)
        
        log_warn.assert_called_once_with(
            "Only suggested values found for entity 'vegetable': ['love apple']")

        # Verify results
        self.assertEqual('love apple', entity_value)
        self.assertTrue(suggested)

    def test_get_entity_value__multiple(self):
        """Verify result of _get_entity_value when multiple value entities are present.
        """
        # Set up mocks and test data
        entity_type = 'vegetable'
        entity_data = [{'type': 'season', 'value': 'summer'}, 
                       {'type': 'value', 'value': 'love apple'},
                       {'type': 'value', 'value': 'tomato'}]
        
        # Make call
        with patch.object(logger, 'warn') as log_warn:
            entity_value, suggested = ParsedSentence._get_entity_value(entity_type, entity_data)

        self.assertEqual(1, log_warn.call_count)
        msg = log_warn.call_args[0][0]
        self.assertTrue(msg.startswith("Multiple values for entity 'vegetable':"))
        self.assertTrue('love apple' in msg)
        self.assertTrue('tomato' in msg)
        
        # Verify results
        self.assertTrue(entity_value in ('tomato', 'love apple'))
        self.assertFalse(suggested)
        
    def test_get_entity_value__empty_data(self):
        """Verify result of _get_entity_value when empty data is supplied.
        """
        for empty in (None, []):
            self.assertEqual((None, False), ParsedSentence._get_entity_value('foo', empty))
        


class ValidateFactTests(unittest.TestCase):
    """Verify ParsedSentence.validate_fact behavior.
    """
    def _get_parsed_sentence(self):
        """Return ParsedSentence that represents valid fact.
        """
        parsed_sentence = ParsedSentence()
        parsed_sentence.intent = 'animal_eats_fact'
        parsed_sentence.relationship_negation = False
        parsed_sentence.relationship_type_name = 'eats'
        parsed_sentence.subject_type = 'animal'
        parsed_sentence.object_type = 'food'
        return parsed_sentence
        
    def test_validate_fact(self):
        parsed_sentence = self._get_parsed_sentence()
        parsed_sentence.validate_fact()
        self.assertTrue(True)

    def test_validate_fact__not_fact_intent(self):
        """Non-fact intent fails fact validation.
        """
        parsed_sentence = self._get_parsed_sentence()
        parsed_sentence.intent = 'foo_query'
        self.assertRaisesRegexp(ValueError,
                                "Sentence has non-fact intent 'foo_query'",
                                parsed_sentence.validate_fact)

    def test_validate_fact__no_relationship(self):
        """Absence of relationship fails fact validation.
        """
        parsed_sentence = self._get_parsed_sentence()
        parsed_sentence.relationship_type_name = None
        
        self.assertRaisesRegexp(ValueError,
                                "No relationship entity found",
                                parsed_sentence.validate_fact)

    def test_validate_fact__no_subject(self):
        """Absence of subject fails fact validation.
        """
        parsed_sentence = self._get_parsed_sentence()
        parsed_sentence.subject_type = None
        
        self.assertRaisesRegexp(ValueError,
                                "No subject entity found",
                                parsed_sentence.validate_fact)

    def test_validate_fact__no_object(self):
        """Absence of object fails fact validation.
        """
        parsed_sentence = self._get_parsed_sentence()
        parsed_sentence.object_type = None
        
        self.assertRaisesRegexp(ValueError,
                                "No object entity found",
                                parsed_sentence.validate_fact)

    def test_validate_fact__negation(self):
        """Negated relationship fails fact validation.
        """
        parsed_sentence = self._get_parsed_sentence()
        parsed_sentence.relationship_negation = True
        
        self.assertRaisesRegexp(ValueError,
                                "Cannot handle fact with negated relationship",
                                parsed_sentence.validate_fact)

