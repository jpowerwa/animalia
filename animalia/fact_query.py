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

    def _bool_as_str(self, val):
        """Tranform provided boolean value into 'yes' or 'no'.

        """
        return 'yes' if val else 'no'

    def _filter_objects_by_species(self, matches):
        """If appropriate, filter relationships for those with objects of specified species.

        :rtype: [:py:class:`fact_model.Relationship`, ...]
        :return: list of relationships with objects of specified species

        :type matches: [:py:class:`fact_model.Relationship`, ...]
        :arg matches: list of Relationships to filter by object species

        """
        return self._filter_relationships_by_species(
            matches, self.parsed_query.object_name, 'object')
    
    def _filter_relationships_by_species(self, matches, species_name, attr_name):
        """If appropriate, filter relationships for those with subjects of specified species.

        :rtype: [:py:class:`fact_model.Relationship`, ...]
        :return: list of relationships with subjects of specified species

        :type matches: [:py:class:`fact_model.Relationship`, ...]
        :arg matches: list of Relationships to filter by subject species

        :type species_name: unicode
        :arg species_name: name of species to filter on
        
        :type attr_name: unicode
        :arg attr_name: 'subject' or 'object'

        """
        species_names = set(self._get_synonymous_species_names(species_name))
        filtered_matches = []
        for m in matches:
            concept_types = set([ct.concept_name for ct in (getattr(m, attr_name)).concept_types])
            if len(concept_types.intersection(species_names)) > 0:
                filtered_matches.append(m)
        return filtered_matches

    def _filter_subjects_by_species(self, matches):
        """If appropriate, filter relationships for those with subjects of specified species.

        :rtype: [:py:class:`fact_model.Relationship`, ...]
        :return: list of relationships with subjects of specified species

        :type matches: [:py:class:`fact_model.Relationship`, ...]
        :arg matches: list of Relationships to filter by subject species

        """
        return self._filter_relationships_by_species(
            matches, self.parsed_query.subject_name, 'subject')
    
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

    def _get_synonymous_species_names(self, orig_name):
        """Generate variations of specified species name.

        :rtype: [unicode, ...]
        :return: list of synonymous species names (sorted for test convenience)

        :type orig_name: unicode
        :arg orig_name: name of species, e.g. 'fish', 'mammals'

        """
        species_names = [orig_name]
        if orig_name.endswith('s'):
            species_names.append(orig_name[0:-1])
        else:
            species_names.append(orig_name + 's')
        return sorted(species_names)

    def _query_object_is_species(self):
        """Determine if current query is for all animals of a particular species or not.

        :rtype: bool
        :return: True if query is for all animals of a particular species, False otherwise

        """
        return self.parsed_query.object_type == 'species'
    
    def _query_subject_is_species(self):
        """Determine if subject of current query is all animals of a particular species or not.

        :rtype: bool
        :return: True if query subject is all animals of a particular species, False otherwise

        """
        for species_name in self._get_synonymous_species_names(self.parsed_query.subject_name):
            matches = self._select_matching_relationships('is', 
                                                          subject_name=species_name,
                                                          object_name='species')
            if len(matches) == 1:
                return True
        return False

    def _select_all_animals(self):
        """Select all concepts that have 'is' relationship to 'animal'.

        :rtype: [:py:class:`fact_model.Concept`]
        :return: concepts that are animals
        
        """
        return self._select_matching_relationships('is', object_name='animal')

    def _select_matching_relationships(self, relationship_type_name, subject_name=None, 
                                       object_name=None, relationship_number=None):
        """Wrapper around fact_model.Relationshop.select_by_names.

        :rtype: [:py:class:`fact_model.Relationship`]
        :return: matching Relationships

        :type relationship_type_name: unicode
        :arg relationship_type_name: name of relationship_type

        :type subject_name: unicode
        :arg subject_name: optional name of subject concept

        :type object_name: unicode
        :arg object_name: optional name of object concept

        """
        logger.debug("Searching for relationship for type {0}, subject {1} and object {2}".format(
                relationship_type_name, subject_name, object_name))
        matches = fact_model.Relationship.select_by_names(
            relationship_type_name=relationship_type_name,
            subject_name=subject_name,
            object_name=object_name)
        if relationship_number is not None:
            matches = [m for m in matches if m.count == relationship_number]
        logger.debug("Found {0} matches".format(len(matches) if matches else 0))
        return matches


    # per-intent methods

    def _animal_attribute_query(self):
        """Do subject and object have type of relationship?

        Examples: 
          Do herons have wings?
          Do spiders live in webs?
          Do bears eat berries?
          Do salmon have scales?
          Do otters have legs?
          Do otters have four legs?
          Do otters have two legs?

        :rtype: unicode
        :return: 'yes' if relationship exists, 'no' otherwise

        """
        matches = self._select_matching_relationships(
            self.parsed_query.relationship_type_name,
            subject_name=self.parsed_query.subject_name,
            object_name=self.parsed_query.object_name,
            relationship_number=self.parsed_query.relationship_number)
        return self._bool_as_str(len(matches) == 1)

    def _animal_eat_query(self):
        """What does the subject eat?

        Examples: 
          What does the otter eat?
          What do birds eat?

        :rtype: [unicode, ...]
        :return: list of foods eaten by subject

        """
        if self._query_subject_is_species():
            matches = self._filter_subjects_by_species(self._select_matching_relationships('eat'))
        else:
            matches = self._select_matching_relationships(
                'eat', subject_name=self.parsed_query.subject_name)

        return sorted([o.concept_name for o in [r.object for r in matches]])

    def _animal_fur_query(self):
        """Does the subject have fur?

        Examples:
          Does the otter have fur?
          Do mammals have fur?

        :rtype: unicode
        :return: 'yes' if relationship exists, 'no' otherwise

        """
        if self._query_subject_is_species():
            matches = self._filter_subjects_by_species(
                self._select_matching_relationships('has', object_name='fur'))
        else:
            matches = self._select_matching_relationships(
                'has', 
                subject_name=self.parsed_query.subject_name, 
                object_name='fur')
        return self._bool_as_str(len(matches) == 1)

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
          How many animals eat reptiles? (Not handled)
          
        :rtype: int
        :return: number of relationships or relationship count attribute

        """
        answer = None
        if self.parsed_query.subject_name == 'animals':
            # First scenario: How many animals have legs?
            answer = len(self._which_animal_query())
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
        logger.debug("animal_place_query for subject '{0}'".format(self.parsed_query.subject_name))
        if self._query_subject_is_species():
            matches = self._filter_subjects_by_species(self._select_matching_relationships('live'))
        else:
            matches = self._select_matching_relationships(
                'live',
                subject_name=self.parsed_query.subject_name)
        return sorted([o.concept_name for o in [r.object for r in matches]])

    def _animal_scales_query(self):
        """Does the subject have scales?

        Examples:
          Does an otter have scales?
          Do mammals have scales?

        :rtype: unicode
        :return: 'yes' if relationship exists, 'no' otherwise

        """
        if self._query_subject_is_species():
            matches = self._filter_subjects_by_species(
                self._select_matching_relationships('has', object_name='scales'))
        else:
            matches = self._select_matching_relationships(
                'has',
                subject_name=self.parsed_query.subject_name,
                object_name='scales')
        return self._bool_as_str(len(matches) == 1)

    def _which_animal_query(self):
        """Which animals have relationship_type with object?

        Examples:
          Which animals eat fish?
          Which animals do not eat fish?
          Which animals are mammals? 
          Which animals live in trees?
          Which animals have fur?
          Which animals do not have fur?
          Which animals have four legs?
          Which animals do not have four legs?
          Which animals eat mammals?

        :rtype: [unicode, ...]
        :return: list of animals that meet specified criteria

        """
        if self._query_object_is_species():
            matches = self._filter_objects_by_species(
                self._select_matching_relationships(
                    self.parsed_query.relationship_type_name,
                    relationship_number=self.parsed_query.relationship_number))
        else:
            matches = self._select_matching_relationships(
                self.parsed_query.relationship_type_name,
                object_name=self.parsed_query.object_name,
                relationship_number=self.parsed_query.relationship_number)

        # Make sure all subjects are animals
        match_names = [m.subject.concept_name 
                       for m in matches if 'animal' in m.subject.concept_types]

        # Reverse selection if relationship is negated
        if self.parsed_query.relationship_negation:
            all_animal_names = [c.concept_name for c in self._select_all_animals()]
            match_names = list(set(all_animal_names) - set(match_names))

        return match_names


