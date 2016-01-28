#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Acceptance tests for query logic. 

Invokes methods that make calls to external wit.ai API.
Intended to be run after training data is bootstrapped by train.py script.

"""

from __future__ import unicode_literals

import unittest

from animalia.fact_manager import FactManager


all_animals = set(['bears', 'bees', 'coyotes', 'deer', 'geckoes', 'herons', 'herrings', 'otters', 
                   'salmon', 'skunks', 'spiders'])

which_animal_test_cases = [
    ('which animals live in trees', ['geckoes']),
    ('which animals do not live in trees', list(all_animals.difference(set(['geckoes'])))),
    ('which animals have legs', 
     ['herons', 'deer', 'spiders', 'bears', 'bees', 'coyotes', 'skunks', 'geckoes', 'otters']),
    ('which animals do not have legs', ['herrings', 'salmon']),
    ('which animals have 4 legs', ['bears', 'coyotes', 'deer', 'geckoes', 'otters', 'skunks']),
    ('which animals have 3 legs', []),
    ('which animals do not have 4 legs', ['bees', 'herons', 'herrings', 'salmon', 'spiders']),
    ('which animals eat geckoes', ['coyotes']),
    ('which animals do not eat geckoes', list(all_animals.difference(set(['coyotes'])))), 
    ('which mammals eat geckoes', ['coyotes']),
    ('which mammals do not eat geckoes', ['bears', 'deer', 'otters', 'skunks']),
    ('which animals eat reptiles', ['coyotes']),
    ('which animals do not eat reptiles', list(all_animals.difference(set(['coyotes'])))),
    ('which animals eat salmon', ['bears', 'otters']),
    ('which animals eat fish', ['bears', 'coyotes', 'herons', 'otters']),
    ]

scalar_tests = {
    'animal_attribute_query': [
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
        ],
    
    'animal_fur_query': [
        ('do bears have fur', 'yes'),
        ('does the bear have fur', 'yes'),
        ('does a bear have fur', 'yes'),
        ('does a salmon have fur', 'no'),
        ('do mammals have fur', 'yes'),
        ],

    'animal_scales_query': [
        ('do salmon have scales', 'yes'),
        ('does the salmon have scales', 'yes'),
        ('does a salmon have scales', 'yes'),
        ('do fish have scales', 'yes'),
        ('do bears have scales', 'no'),
        ('do mammals have scales', 'no'),
        ],

    'how_many_legs_query': [
        ('how many legs does the gecko have', 4),
        ('how many legs does a gecko have', 4),
        ('how many legs do geckoes have', 4),
        ('how many legs do spiders have', 8),
        ],

    'how_many_animals_query': [
        (unicode.replace(q, 'which', 'how many'), len(a)) for q, a in which_animal_test_cases
        ],

}


set_tests = {
    'animal_eat_query': [
        ('what does a heron eat', ['fish', 'herrings']),
        ('what do herons eat', ['fish', 'herrings']),
        ('what do coyotes eat', ['berries', 'fish', 'geckoes', 'insects', 'skunks']),
        ('what do mammals eat', ['grass', 'insects', 'geckoes', 'fish', 'salmon', 'skunks', 'berries', 'herrings']),
        ],

    'animal_place_query': [
        ('where does the otter live', ['rivers', 'oceans']),
        ('where does an otter live', ['rivers', 'oceans']),
        ('where do otters live', ['rivers', 'oceans']),
        ('where does the bear live', ['forests', 'meadows']),
        ('where do mammals live', ['rivers', 'oceans', 'forests', 'meadows']),
        ('where do fish live', ['rivers', 'oceans']),
        ],

    'which_animal_query': which_animal_test_cases,

    }


class QueryLogicTestsMeta(type):
    def __new__(mcs, name, bases, dct):

        def generate_test__scalar_comparison(query_sentence, expectation):
            def test(self):
                answer = FactManager.query_facts(query_sentence)
                self.assertEqual(expectation, answer,
                    "Expected '{0}' as answer to question '{1}'; got '{2}'".format(  
                        expectation, query_sentence, answer))
            return test

        def generate_test__set_comparison(query_sentence, expectation):
            def test(self):
                answer = FactManager.query_facts(query_sentence)
                self.assertEqual(set(expectation), set(answer),
                    "Expected '{0}' as answer to question '{1}'; got '{2}'".format(  
                        expectation, query_sentence, answer))
            return test

        def make_test_name(group_name, query_sentence):
            return "test_{0}__{1}".format(test_group, '_'.join(query_sentence.split(' ')))
            

        # Create tests that compare scalar results
        for test_group, test_cases in scalar_tests.iteritems():
            for query_sentence, expectation in test_cases:
                test_name = make_test_name(test_group, query_sentence)
                dct[test_name] = generate_test__scalar_comparison(query_sentence, expectation)

        # Create tests that compare list results 
        for test_group, test_cases in set_tests.iteritems():
            for query_sentence, expectation in test_cases:
                test_name = "test_{0}_{1}".format(test_group, '_'.join(query_sentence.split(' ')))
                dct[test_name] = generate_test__set_comparison(query_sentence, expectation)

        return type.__new__(mcs, name, bases, dct)


class QueryLogicTests(unittest.TestCase):
    __metaclass__ = QueryLogicTestsMeta

