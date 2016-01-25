#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Acceptance tests for query logic. 

Invokes methods that make calls to external wit.ai API.
Intended to be run after training data is bootstrapped by train.py script.

"""

from __future__ import unicode_literals

import logging
import unittest

from animalia.fact_manager import FactManager


class QueryLogicTestCase(unittest.TestCase):
    """Base case for test of intent-specific queries.
    """
    def run_tests(self, test_cases, transform_fn=None):
        """
        :type test_cases: [(unicode, object), ...]
        :arg test_cases: list of tuples that are (query_sentence, expected_answer)
        
        :type transform_fn: callable
        :arg transform_fn: optional function to apply to answer and expected answer before comparing

        """
        for query_sentence, expected_answer in test_cases:
            answer = FactManager.query_facts(query_sentence)
            if transform_fn:
                answer = transform_fn(answer)
                expected_answer = transform_fn(expected_answer)
            self.assertEqual(
                expected_answer, 
                answer, 
                "Expected '{0}' as answer to question '{1}'; got '{2}'".format(
                    expected_answer, query_sentence, answer))

class AnimalAttributeQueryTests(QueryLogicTestCase):
    """Verify 'animal_attribute_query'
    """
    test_cases = [
        ('do herons have wings', 'yes'),
        ('does the heron have wings', 'yes'),
        ('does a heron have wings', 'yes'),
        ('does a heron have fur', 'no'),
        ('does a heron have scales', 'no'),
        ('do herons have tails', 'yes'),
        ('does the heron have a tail', 'yes'),
        ('does a heron have legs', 'yes'),
        ('does a heron have 2 legs', 'yes'),
        ('does a heron have 4 legs', 'no'),
        ('does a heron live in the ocean', 'yes'),
        ('does the heron live in the ocean', 'yes'),
        ('do herons live in the ocean', 'yes'),
        ('do herons live in oceans', 'yes'),
        ('does the heron live in trees', 'no'),
        ('do herons live in trees', 'no'),
        ('do herons eat fish', 'yes'),
        ('do herons eat berries', 'no'),
        ('do bears eat salmon', 'yes'),
        ('do bears eat fish', 'yes'),
        ('do bears eat berries', 'yes'),
        ('do coyotes eat mammals', 'yes'),
        ]
    
    def test_animal_attribute_query(self):
        self.run_tests(self.test_cases)
                    

class AnimalEatQueryTests(QueryLogicTestCase):
    test_cases = [
        ('what does a heron eat', ['fish', 'herring']),
        ('what do herons eat', ['fish', 'herring']),
        ('what do coyotes eat', ['berries', 'fish', 'gecko', 'insects', 'skunk']),
        ('what do mammals eat', ['grass', 'insects', 'gecko', 'fish', 'salmon', 'skunk', 'berries', 'herring']),
        ]
    
    def test_animal_eat_query(self):
        self.run_tests(self.test_cases, lambda l: set(l))


class AnimalFurQueryTests(QueryLogicTestCase):
    test_cases = [
        ('do bears have fur', 'yes'),
        ('does the bear have fur', 'yes'),
        ('does a bear have fur', 'yes'),
        ('does a salmon have fur', 'no'),
        ('do mammals have fur', 'yes'),
        ]
    
    def test_animal_fur_query(self):
        self.run_tests(self.test_cases)
                    

class AnimalPlaceQueryTests(QueryLogicTestCase):
    test_cases = [
        ('where does the otter live', ['river', 'ocean']),
        ('where does an otter live', ['river', 'ocean']),
        ('where do otters live', ['river', 'ocean']),
        ('where does the bear live', ['forest', 'meadow']),
        ('where do mammals live', ['river', 'ocean', 'forest', 'meadow']),
        ('where do fish live', ['river', 'ocean']),
        ]
    
    def test_animal_place_query(self):
        self.run_tests(self.test_cases, lambda l: set(l))
                    

class AnimalScalesQueryTests(QueryLogicTestCase):
    test_cases = [
        ('do salmon have scales', 'yes'),
        ('does the salmon have scales', 'yes'),
        ('does a salmon have scales', 'yes'),
        ('do fish have scales', 'yes'),
        ('do bears have scales', 'no'),
        ('do mammals have scales', 'no'),
        ]
    
    def test_animal_scales_query(self):
        self.run_tests(self.test_cases)


class WhichAnimalQueryTests(QueryLogicTestCase):
    """Also test animal_how_many query.
    """
    all_animals = set(['bear', 'bee', 'coyote', 'deer', 'gecko', 
                       'heron', 'herring', 'otter', 'salmon', 'skunk', 'spider'])

    test_cases = [
        ('which animals live in trees', ['gecko']),
        ('which animals do not live in trees', list(all_animals.difference(set(['gecko'])))),
        ('which animals have legs', 
         ['heron', 'deer', 'spider', 'bear', 'bee', 'coyote', 'skunk', 'gecko', 'otter']),
        ('which animals do not have legs', ['herring', 'salmon']),
        ('which animals have 4 legs', ['bear', 'coyote', 'deer', 'gecko', 'otter', 'skunk']),
        ('which animals have 3 legs', []),
        ('which animals do not have 4 legs', ['bee', 'heron', 'herring', 'salmon', 'spider']),
        ('which animals eat geckos', ['coyote']),
        ('which animals do not eat geckos', list(all_animals.difference(set(['coyote'])))), 
        ('which mammals eat geckos', ['coyote']),
        ('which mammals do not eat geckos', ['bear', 'deer', 'otter', 'skunk']),
        ('which animals eat reptiles', ['coyote']),
        ('which animals do not eat reptiles', list(all_animals.difference(set(['coyote'])))),
        ('which animals eat salmon', ['bear', 'otter']),
        ('which animals eat fish', ['bear', 'coyote', 'heron', 'otter']),
        ]
    
    def test_which_animal_query(self):
        self.run_tests(self.test_cases, lambda l: set(l))

    def test_animal_how_many_query(self):
        """Use same data to test animal_how_many_query.

        Result is number of matches rather than matches themselves.
        """
        self.run_tests(self.test_cases, lambda r: len(r))
                    

class HowManyLegsQueryTests(QueryLogicTestCase):
    test_cases = [
        ('how many legs does the gecko have', 4),
        ('how many legs does a gecko have', 4),
        ('how many legs do geckos have', 4),
        ('how many legs do spiders have', 8),
        ]

    def test_how_many_legs_query(self):
        self.run_tests(self.test_cases)
