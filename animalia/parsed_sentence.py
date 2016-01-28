#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ParsedSentence encapsulates parsed sentence data represented in wit.ai response.

Like FactManager, ParsedSentence is agnostic to data domain. Animalia-specific data is
provided by Config module.

See wit_responses.py for samples of valid parsed_data.

"""

from __future__ import unicode_literals

import json
import logging

from config import Config
from plurals import Plurals


logger = logging.getLogger('animalia.ParsedSentence')


class ParsedSentence(object):
    __doc__ = __doc__

    # Value between 0 and 1 that is threshold for acceptable outcome returned by wit.ai
    CONFIDENCE_THRESHOLD = Config.parsed_data_confidence_threshold

    # Names of entities that are related to relationships or are subjects
    RELATIONSHIP_KEY = 'relationship'
    RELATIONSHIP_COUNT_KEY = 'number'
    RELATIONSHIP_NEGATION_KEY = 'negation'
    SUBJECT_ENTITY_TYPES = Config.wit_subject_entity_types
    ALT_SUBJECT_ENTITY_TYPES = Config.wit_alt_subject_entity_types

    def __init__(self, text=None, confidence=None, intent=None, 
                 subject_name=None, subject_type=None, object_name=None, object_type=None,
                 relationship_type_name=None, relationship_number=None, 
                 relationship_negation=False):
        """
        :type text: unicode
        :type confidence: float
        :type intent: unicode
        :type subject_name: unicode
        :type subject_type: unicode
        :type object_name: unicode
        :type object_type: unicode
        :type relationship_type_name: unicode
        :type relationship_number: int
        :type relationship_negation: bool
        
        """
        self.text = text
        self.confidence = confidence
        self.intent = intent
        self.subject_name = subject_name
        self.subject_type = subject_type
        self.object_name = object_name
        self.object_type = object_type
        self.relationship_type_name = relationship_type_name
        self.relationship_number = relationship_number or None
        self.relationship_negation = relationship_negation
        self.orig_response = None

    @classmethod
    def from_wit_response(cls, response_data):
        """Factory method that extracts subject, object and relationship and data from wit response.

        Extract if present:
        * Sentence subject and subject_type, e.g. 'otters' and 'animals'
        * Sentence object and object_type, e.g. 'legs' and 'body_parts'
        * Relationship type name, e.g. 'has'
        * Relationship number, e.g. '4' 
        * Relationship negation

        Verify:
        * Presence of '_text' attribute
        * Presence of exactly one outcome
        * Outcome 'intent' is defined
        * Maximum one subject, one object and one relationship value

        :rtype: :py:class:`ParsedSentence`
        :return: instance of ParsedSentence
        :raise: ValueError if provided data does not meet expectations

        :type response_data: dict
        :arg response_data: JSON response from wit.ai

        """
        instance = cls()

        # _text attribute is required
        instance.text = response_data.get('_text')
        if not instance.text:
            raise ValueError("Response data has no _text attribute")

        logger.debug("Parsing wit response for sentence '{0}'".format(instance.text))

        # Expect exactly one outcome
        outcomes = response_data.get('outcomes') or []
        if len(outcomes) != 1:
            raise ValueError("Expected 1 outcome, found {0}".format(len(outcomes)))
        outcome = outcomes[0]

        # Intent attribute is required
        instance.intent = outcome.get('intent')
        if not instance.intent:
            raise ValueError("Outcome has no intent attribute")

        # Warn if outcome has low confidence rating
        instance.confidence = outcome['confidence']
        if instance.confidence < cls.CONFIDENCE_THRESHOLD:
            logger.warn("Outcome confidence falls below threshold: {0} < {1}".format(
                    instance.confidence, cls.CONFIDENCE_THRESHOLD))

        # Identify relationship, subject and object entities if present
        # Hold onto entities with types in ALT_SUBJECT_ENTITY_TYPES list as temporary vars
        alt_subject_name = None
        alt_subject_type = None

        # Iterate over entities; each entity is key (entity_type) referencing list of data
        # from with entity value can be extracted.
        for entity_type, entity_data in outcome['entities'].iteritems(): 
            val, is_suggested = cls._get_entity_value(entity_type, entity_data)
            logger.debug("Parsed value '{0}' for entity '{1}'{2}".format(
                    val, entity_type, ' (suggested)' if is_suggested else ''))
            if val:
                if is_suggested:
                    logger.warn("Using suggested parsed value '{0}' for entity '{1}'".format(
                            val, entity_type))

            if entity_type == cls.RELATIONSHIP_KEY:
                instance.relationship_type_name = val

            elif entity_type == cls.RELATIONSHIP_COUNT_KEY:
                instance.relationship_number = val

            elif entity_type == cls.RELATIONSHIP_NEGATION_KEY:
                instance.relationship_negation = True

            elif entity_type in cls.SUBJECT_ENTITY_TYPES:
                if instance.subject_type:
                    raise ValueError("Parsed multiple subject entities: {0}, {1}".format(
                            instance.subject_type, entity_type))
                instance.subject_type = Plurals.get_plural(entity_type)
                instance.subject_name = Plurals.get_plural(val)

            elif entity_type in cls.ALT_SUBJECT_ENTITY_TYPES:
                if alt_subject_type:
                    raise ValueError("Parsed multiple alt subject entities: {0}, {1}".format(
                            alt_subject_type, entity_type))
                alt_subject_type = Plurals.get_plural(entity_type)
                alt_subject_name = Plurals.get_plural(val)

            else:
                if instance.object_type:
                    raise ValueError("Parsed multiple object entities: {0}, {1}".format(
                            instance.object_type, entity_type))
                instance.object_type = Plurals.get_plural(entity_type)
                instance.object_name = Plurals.get_plural(val)

        # If alt_subject data was found, determine whether it is subject, object or just confusing.
        if alt_subject_type:
            if not instance.subject_type:
                logger.debug("Using alt_subject as subject: {0}, {1}".format(
                        alt_subject_type, alt_subject_name))
                instance.subject_type = alt_subject_type
                instance.subject_name = alt_subject_name
            elif not instance.object_type:
                logger.debug("Using alt_subject as object: {0}, {1}".format(
                        alt_subject_type, alt_subject_name))
                instance.object_type = alt_subject_type
                instance.object_name = alt_subject_name
            else:
                raise ValueError("Parsed alt_subject but both subject and object were found")

        # Serialize and preserve original response data
        instance.orig_response = json.dumps(response_data)

        return instance

    def validate_fact(self):
        """Determine if this sentence data represents valid fact.

        :raise: ValueError if sentence does not meet requirements for a valid fact

        Verify:
        * Intent is fact
        * Sentence has relationship entity 
        * Sentence has subject entity
        * Sentence has object entity
        * Relationship is not negated

        """
        if not self.intent.endswith('_fact'):
            raise ValueError("Sentence has non-fact intent '{0}'".format(self.intent))
        if self.relationship_negation:
            raise ValueError("Cannot handle fact with negated relationship")
        if not self.relationship_type_name:
            raise ValueError("No relationship entity found")
        if not self.subject_type:
            raise ValueError("No subject entity found")
        if not self.object_type: 
            raise ValueError("No object entity found")


    # private methods

    @classmethod
    def _get_entity_value(cls, entity_type, entity_data):
        """Extract string that is 'value' of entity. Indicate if returned value is suggested.

        :rtype: (unicode, bool)
        :return: tuple that is value of entity and is_suggested flag

        :type entity_data: list of dicts with keys 'type', 'value' and, optionally, 'suggested'
        :arg entity_data: value of 'entities' dict in wit.ai parsed fact

        """
        val = None
        is_suggested = False

        vals = []
        suggested_vals = []
        for entity in [e for e in entity_data or [] if e.get('type') == 'value']:
            target_list = suggested_vals if entity.get('suggested') else vals
            target_list.append(str(entity['value']).lower())

        if not vals and suggested_vals:
            logger.warn("Only suggested values found for entity '{0}': {1}".format(
                    entity_type, suggested_vals))
            vals = suggested_vals
            is_suggested = True
        elif suggested_vals:
            logger.warn("Ignoring suggested values for entity '{0}': {1}".format(
                    entity_type, suggested_vals))
        if vals:
            if len(vals) > 1:
                logger.warn("Multiple values for entity '{0}': {1}; ignoring all but '{2}'".format(
                        entity_type, vals, vals[0]))
            val = vals[0]

        return val, is_suggested
