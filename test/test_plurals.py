#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Verify Plurals utility object.
"""

from __future__ import unicode_literals

from mock import patch
import unittest

from animalia.plurals import Plurals


class PluralsTests(unittest.TestCase):
    """Verify Plurals behavior.
    """

    singular = 'berry'
    plural = 'berries'

    def setUp(self):
        Plurals.inflect_engine = None
        Plurals.cached_plurals = {}

    def test_get_plural(self):
        """Verify behavior for generating plural of singular noun.
        """
        plural = Plurals.get_plural(self.singular)
        self.assertEqual(self.plural, plural)

    def test_get_plural__plural(self):
        """Verify behavior for generating plural of plural noun.
        """
        plural = Plurals.get_plural(self.plural)
        self.assertEqual(self.plural, plural)

    def test_get_plural__plural__cache(self):
        """Verify that cache is used on second call with same plural noun.
        """
        plural = Plurals.get_plural(self.plural)
        self.assertEqual(self.plural, plural)
        with patch.object(Plurals, '_ensure_inflect_engine') as inflect_engine:
            second_plural = Plurals.get_plural(self.plural)
        self.assertEqual(self.plural, second_plural)
        self.assertEqual(0, inflect_engine.call_count)

    def test_get_plural__singular__cache(self):
        """Verify that cache is used on second call with same singular noun.
        """
        plural = Plurals.get_plural(self.singular)
        self.assertEqual(self.plural, plural)
        with patch.object(Plurals, '_ensure_inflect_engine') as inflect_engine:
            second_plural = Plurals.get_plural(self.singular)
        self.assertEqual(self.plural, second_plural)
        self.assertEqual(0, inflect_engine.call_count)

    def test_get_plural__singular__cache_both_versions(self):
        """Verify that get_plural for singular noun results in cached plural for both versions.
        """
        plural = Plurals.get_plural(self.singular)
        self.assertEqual(self.plural, plural)
        with patch.object(Plurals, '_ensure_inflect_engine') as inflect_engine:
            second_plural = Plurals.get_plural(self.plural)
        self.assertEqual(second_plural, plural)
        self.assertEqual(0, inflect_engine.call_count)
        
    def test_get_plural__plural__cache_both_versions(self):
        """Verify that get_plural for plural noun results in cached plural for both versions.
        """
        plural = Plurals.get_plural(self.plural)
        self.assertEqual(self.plural, plural)
        with patch.object(Plurals, '_ensure_inflect_engine') as inflect_engine:
            second_plural = Plurals.get_plural(self.singular)
        self.assertEqual(second_plural, plural)
        self.assertEqual(0, inflect_engine.call_count)
        
