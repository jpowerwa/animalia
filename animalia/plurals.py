#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Utility class for generating plural versions of nouns.
"""

from __future__ import unicode_literals

import inflect


class Plurals(object):
    __doc__ = __doc__

    inflect_engine = None
    cached_plurals = {}

    @classmethod
    def get_plural(cls, noun):
        """Find or generate plural version of provided noun whether it is plural or singular.

        :rtype: unicode
        :return: plural version of specified noun

        :type noun: unicode
        :arg noun: singular or plural noun

        """
        plural = cls.cached_plurals.get(noun)
        if not plural:
            cls._ensure_inflect_engine()
            # Inflect.plural_noun does stupid things if provided word is already plural.
            # So, convert words to singular first. Inflect.singular_noun returns False
            # if provided word is already singular.
            singular = cls.inflect_engine.singular_noun(noun)
            if not singular:
                singular = noun
            plural = cls.inflect_engine.plural_noun(singular)
            if not cls.cached_plurals.get(singular):
                cls.cached_plurals[singular] = plural
        if not cls.cached_plurals.get(plural):
            cls.cached_plurals[plural] = plural
        return plural

    @classmethod
    def _ensure_inflect_engine(cls):
        """Initialze cls.inflect_engine if necessary.
        """
        if not cls.inflect_engine:
            cls.inflect_engine = inflect.engine()
