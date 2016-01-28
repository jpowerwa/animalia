#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from __future__ import unicode_literals

import logging

import fact_model

logger = logging.getLogger('animalia.FactQuery')


class FactQuery(object):
    """Encapsulation of logic to answer query based on facts database.
    """

    def __init__(self, parsed_query=None):
        """
        :type parsed_query: :py:class:`ParsedSentence`
        :arg parsed_query: object containing parsed query components
        """
        self.parsed_query = parsed_query

    def find_answer(self):
        """Query persisted fact data to answer question presented in parsed sentence.

        :rtype: object
        :return: answer to question or None if no answer could be found

        """
        if not self.parsed_query:
            raise ValueError("No query to answer")

        fn = self._find_answer_function()
        if not fn:
            raise ValueError("No answer function found")
        return fn()


    # private methods

    @staticmethod
    def _bool_as_str(val):
        """Tranform provided boolean value into 'yes' or 'no'.
        """
        return 'yes' if val else 'no'

    @classmethod
    def _concept_is_species(cls, concept_name):
        """Determine if specified concept is a species or not.

        :rtype: bool
        :return: True if specified concept is a species, False otherwise

        :type concept_name: unicode
        :arg concept_name: name of concept

        """
        matches = cls._select_matching_relationships(
            'is', subject_name=concept_name, object_name='species')
        return bool(matches)

    @classmethod
    def _filter_relationships_by_concept_type(cls, matches, concept_type, relationship_attr=None):
        """Filter relationships by concept_type on attr_name.
        
        :rtype: [:py:class:`fact_model.Relationship`, ...]
        :return: list of relationships filtered by concept_type on attr_name
        
        :type matches: [:py:class:`fact_model.Relationship`, ...]
        :arg matches: list of Relationships to filter by concept_type on attr_name
        
        :type concept_type: unicode
        :arg concept_type: name of concept_type to filter on
        
        :type relationship_attr: unicode
        :arg relationship_attr: 'subject' or 'object'
        
        """
        filtered_matches = []
        for m in matches:
            if concept_type in set([ct for ct in (getattr(m, relationship_attr)).concept_types]):
                filtered_matches.append(m)
        return filtered_matches

    def _find_answer_function(self):
        """Find function that will answer question represented by current parsed_sentence.

        :rtype: fn(parsed_sentence) or None
        :return: appropriate function or None if no function is found

        """
        intent = self.parsed_query.intent.lower()

        # Sometimes queries are labeled as facts. These appear to translate as 
        # 'animal_attribute_question'.
        if intent.endswith('_fact'):
            intent = 'animal_attribute_question'
            
        # Normalize _question and _query intents.
        intent_base = '_'.join(intent.split('_')[0:-1])
        fn_name = '_{0}_query'.format(intent_base)
        return getattr(self, fn_name, None)

    @classmethod
    def _select_by_concept_type(cls, concept_type):
        """Select all concepts that have 'is' relationship to one of specified concept_types.

        :rtype: [:py:class:`fact_model.Concept`]
        :return: concepts with one of specified concept_types
        
        :type concept_type: unicode
        :arg concept_type: concept_type to filter on

        """
        matches = cls._select_matching_relationships('is', object_name=concept_type)
        return [m.subject for m in matches]

    @classmethod
    def _select_matching_relationships(cls, relationship_type_name, relationship_number=None,
                                       subject_name=None, object_name=None):
        """Wrapper around fact_model.Relationship.select_by_values.

        :rtype: [:py:class:`fact_model.Relationship`]
        :return: matching Relationships

        :type relationship_type_name: unicode
        :arg relationship_type_name: name of relationship_type

        :type relationship_number: int
        :arg relationship_number: optional int that is count attribute of matched relationship

        :type subject_name: unicode
        :arg subject_name: optional name of subject concept

        :type object_name: unicode
        :arg object_name: optional name of object concept

        """
        logger.debug(
            "Searching for '{0}' relationship where subject={1}, object={2}, count={3}".format(
                relationship_type_name, subject_name, object_name, relationship_number))

        if relationship_number:
            relationship_number = int(relationship_number)

        matches = fact_model.Relationship.select_by_values(
            relationship_type_name=relationship_type_name,
            relationship_number=relationship_number,
            subject_name=subject_name,
            object_name=object_name)

        logger.debug(
            "Found {0} '{1}' relationships where subject={2}, object={3}, count={4}".format(
                len(matches), relationship_type_name, subject_name, object_name, 
                relationship_number))

        return matches


    # per-intent methods

    def _animal_attribute_query(self, relationship_type_name=None, 
                                subject_name=None, object_name=None):
        """Do subject and object have type of relationship?

        Examples: 
          Do herons have legs?
          Does a heron have four legs?
          Do spiders live in webs?
          Do spiders eat insects?
          Do otters have fur?
          Do otters have scales?
          Do mammals have fur?
          Do coyotes eat mammals?

        :rtype: unicode
        :return: 'yes' if relationship exists, 'no' otherwise

        :type relationship_type_name: unicode
        :arg relationship_type_name: optional override for self.parsed_query.relationship_type_name

        :type subject_name: unicode
        :arg subject_name: optional override for self.parsed_query.subject_name

        :type object_name: unicode
        :arg object_name: optional override for self.parsed_query.object_name

        """
        logger.debug("animal_attribute_query: '{0}'".format(self.parsed_query.text))
        relationship_type_name = relationship_type_name or self.parsed_query.relationship_type_name
        subject_name = subject_name or self.parsed_query.subject_name
        object_name = object_name or self.parsed_query.object_name
        if not (subject_name and object_name and relationship_type_name):
            raise ValueError("animal_attribute_query requires subject, object and relationship")

        # Start off by querying with subject and object as specified
        matches = self._select_matching_relationships(
            relationship_type_name,
            subject_name=subject_name,
            object_name=object_name,
            relationship_number=self.parsed_query.relationship_number)

        # If that didn't work, look to see if subject or object is species.
        if not matches:
            # If the subject is a species name, select relationships without specifying 
            # subject_name, then filter for subjects that are specified species.
            if subject_name and self._concept_is_species(subject_name):
                logger.debug("Filter subjects of '{0}' '{1}' to species '{2}'".format( 
                        relationship_type_name, object_name, subject_name))
                matches = self._filter_relationships_by_concept_type(
                    self._select_matching_relationships(
                        relationship_type_name,
                        relationship_number=self.parsed_query.relationship_number,
                        object_name=object_name),
                    subject_name,
                    relationship_attr='subject')

            # Otherwise, if the object is a species name, select relationships without 
            # specifying object_name, then filter objects of specified species.
            elif object_name and self._concept_is_species(object_name):
                logger.debug("Filter objects of '{0}' '{1}' to species '{2}'".format( 
                        subject_name, relationship_type_name, object_name))
                matches = self._filter_relationships_by_concept_type(
                    self._select_matching_relationships(
                        relationship_type_name,
                        relationship_number=self.parsed_query.relationship_number,
                        subject_name=subject_name),
                    object_name,
                    relationship_attr='object')

        return self._bool_as_str(len(matches) >= 1)

    def _animal_eat_query(self):
        """What does the subject eat?

        Examples: 
          What does the otter eat?
          What do herons eat?
          What do birds eat?

        :rtype: [unicode, ...]
        :return: list of foods eaten by subject

        """
        logger.debug("animal_eat_query: '{0}'".format(self.parsed_query.text))
        if not self.parsed_query.subject_name:
            raise ValueError("animal_eat_query requires subject_name")

        return self._animal_values_query(
            relationship_type_name='eat', subject_name=self.parsed_query.subject_name)

    def _animal_fur_query(self):
        """Does the subject have fur?

        Examples:
          Does the otter have fur?
          Do mammals have fur?

        :rtype: unicode
        :return: 'yes' if relationship exists, 'no' otherwise

        """
        logger.debug("animal_fur_query: '{0}'".format(self.parsed_query.text))
        if not self.parsed_query.subject_name:
            raise ValueError("animal_fur_query requires subject_name")
        return self._animal_attribute_query(relationship_type_name='has', object_name='furs')

    def _animal_how_many_query(self):
        """Number of relationships or count attribute of specific relationship.

        Examples:
          How many legs does the otter have?
          How many animals have fur?
          How many animals do not have fur?
          How many animals have legs?
          How many animals have four legs? 
          How many animals do not have four legs?
          How many animals live in the forest?
          How many animals eat berries?
          How many animals eat reptiles?
          
        :rtype: int
        :return: number of relationships or relationship count attribute

        """
        logger.debug("animal_how_many_query: '{0}'".format(self.parsed_query.text))
        if not (self.parsed_query.subject_name 
                and self.parsed_query.object_name
                and self.parsed_query.relationship_type_name):
            raise ValueError("animal_how_many_query requires subject, object and relationship")

        answer = None
        if (self.parsed_query.subject_name == 'animals' or
            self._concept_is_species(self.parsed_query.subject_name)):
            # First scenario: How many animals have legs?
            matches = self._which_animal_query()
            answer = len(matches)
        else:
            # Second scenario: How many legs does the otter have?
            matches = self._select_matching_relationships(
                self.parsed_query.relationship_type_name,
                subject_name=self.parsed_query.subject_name,
                object_name=self.parsed_query.object_name)
            if len(matches) == 1:
                answer = matches[0].count
        return answer

    def _animal_place_query(self):
        """Where does the subject live.

        Examples:
          Where does the otter live?
          Where do reptiles live? 

        :rtype: [unicode, ...]
        :return: list of places where subject lives

        """
        logger.debug("animal_place_query: '{0}'".format(self.parsed_query.text))
        if not self.parsed_query.subject_name:
            raise ValueError("animal_place_query requires subject_name")

        return self._animal_values_query(
            relationship_type_name='live', subject_name=self.parsed_query.subject_name)

    def _animal_scales_query(self):
        """Does the subject have scales?

        Examples:
          Does an otter have scales?
          Do mammals have scales?

        :rtype: unicode
        :return: 'yes' if relationship exists, 'no' otherwise

        """
        logger.debug("animal_scales_query: '{0}'".format(self.parsed_query.text))
        if not self.parsed_query.subject_name:
            raise ValueError("animal_scales_query requires subject_name")

        return self._animal_attribute_query(relationship_type_name='has', object_name='scales')

    def _animal_values_query(self, relationship_type_name=None, subject_name=None):
        """Where does the subject live, what does the subject eat, etc.

        :rtype: [unicode, ...]
        :return: list of objects matching specified relationship type with subject

        :type relationship_type_name: unicode
        :arg relationship_type_name: name of relationship between subject and desired objects

        :type subject_name: unicode
        :arg subject_name: name of relationship subject

        """
        if not (relationship_type_name and subject_name):
            raise ValueError("animal_values_query requires relationship_type_name and subject_name")

        if self._concept_is_species(subject_name):
            logger.debug("Filter subjects of '{0}' relationships by species '{1}'".format(
                    relationship_type_name, subject_name))
            matches = self._filter_relationships_by_concept_type(
                self._select_matching_relationships(relationship_type_name),
                subject_name,
                relationship_attr='subject')
        else:
            matches = self._select_matching_relationships(
                relationship_type_name,
                subject_name=subject_name)

        match_names = list(set([o.concept_name for o in [r.object for r in matches]]))
        return sorted(match_names)

    def _which_animal_query(self):
        """Which animals have relationship_type with object?

        Examples:
          Which animals eat fish?
          Which animals do not eat fish?
          Which mammals eat fish?
          Which animals are mammals? 
          Which animals live in trees?
          Which animals have fur?
          Which animals do not have fur?
          Which animals have four legs?
          Which animals do not have four legs?

        :rtype: [unicode, ...]
        :return: list of animals that meet specified criteria

        """
        logger.debug("which_animal_query: '{0}'".format(self.parsed_query.text))
        if not (self.parsed_query.subject_name 
                and self.parsed_query.object_name
                and self.parsed_query.relationship_type_name):
            raise ValueError("which_animal_query requires subject, object and relationship")

        # Start off querying on specified object
        logger.debug("Find animals with relationship '{0}' to '{1}'".format(
                self.parsed_query.relationship_type_name,
                self.parsed_query.object_name))
        matches = self._select_matching_relationships(
            self.parsed_query.relationship_type_name,
            object_name=self.parsed_query.object_name,
            relationship_number=self.parsed_query.relationship_number)

        # Do next query even if there are matches from previous query. This takes care
        # of cases where object is sometimes direct reference to species and other times
        # member of species.
        if self._concept_is_species(self.parsed_query.object_name):
            logger.debug("Find animals with relationship '{0}' to species '{1}'".format(
                    self.parsed_query.relationship_type_name,
                    self.parsed_query.object_name))
            matches.extend(self._filter_relationships_by_concept_type(
                    self._select_matching_relationships(
                        self.parsed_query.relationship_type_name,
                        relationship_number=self.parsed_query.relationship_number),
                    self.parsed_query.object_name, 
                    relationship_attr='object'))

        # Filter results by concept_type of subject, i.e. 'animals' or particular species
        concept_type = 'animals'
        if self._concept_is_species(self.parsed_query.subject_name):
            concept_type = self.parsed_query.subject_name
        matches = self._filter_relationships_by_concept_type(
            matches, concept_type, relationship_attr='subject')
        # De-dupe match names.
        match_names = list(set([m.subject.concept_name for m in matches]))
        logger.debug("Matching subjects: {0}".format(match_names))

        # Reverse selection if relationship is negated
        if self.parsed_query.relationship_negation:
            logger.debug("Reversing selection")
            possibilities = self._select_by_concept_type(concept_type)
            match_names = list(set([c.concept_name for c in possibilities]) - set(match_names))
            logger.debug("Reversed match names: {0}".format(match_names))

        return match_names


