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

    def _filter_concepts_by_type(self, concepts, concept_types):
        """Filter concepts by list of concept_types.

        :rtype: [:py:class:`fact_model.Concept`, ...]
        :return: list of concepts with concept_type intersecting provided list of concept_types

        :type concepts: [:py:class:`fact_model.Concept`, ...]
        :arg concepts: list of concepts to filter by concept_type

        :type concept_types: [unicode, ...]
        :arg concept_types: concept_types to filter on
        
        """
        filtered_concepts = []
        target_concept_types = set(concept_types)
        for c in concepts:
            if len(target_concept_types.intersection(set(c.concept_types))) > 0:
                filtered_concepts.append(c)
        return filtered_concepts

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
        # Look for matches on both singular and plural species name.
        species_names = set(self._get_synonymous_names(species_name))
        logging.debug("Filtering relationships by species names {0}".format(species_names))

        filtered_matches = []
        for m in matches:
            concept_types = set([ct for ct in (getattr(m, attr_name)).concept_types])
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

    def _get_synonymous_names(self, orig_name):
        """Generate singular and plural versions of specified species or animal name.

        :rtype: [unicode, ...]
        :return: list of singular and plural versions of name (sorted for test convenience)

        :type orig_name: unicode
        :arg orig_name: name of animal or species, e.g. 'otter', 'mammals'

        """
        names = [orig_name]
        if orig_name.endswith('s'):
            names.append(orig_name[0:-1])
        else:
            names.append(orig_name + 's')
        return sorted(names)

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
        matches = self._select_matching_relationships(
            'is', 
            subject_name=self._get_synonymous_names(self.parsed_query.subject_name),
            object_name='species',
            stop_on_match=True)
        return bool(matches)

    def _select_by_concept_type(self, concept_types):
        """Select all concepts that have 'is' relationship to one of specified concept_types.

        :rtype: [:py:class:`fact_model.Concept`]
        :return: concepts with one of specified concept_types
        
        :type concept_types: [unicode, ...]
        :arg concept_types: concept_types to filter on

        """
        matches = []
        for concept_type in concept_types:
            matches.extend(self._select_matching_relationships('is', object_name=concept_type))
        return [m.subject for m in matches]

    def _select_matching_relationships(self, relationship_type_name, relationship_number=None,
                                       subject_name=None, object_name=None, stop_on_match=False):
        """Wrapper around fact_model.Relationship.select_by_values.

        :rtype: [:py:class:`fact_model.Relationship`]
        :return: matching Relationships

        :type relationship_type_name: unicode
        :arg relationship_type_name: name of relationship_type

        :type relationship_number: int
        :arg relationship_number: optional int that is count attribute of matched relationship

        :type subject_name: unicode or [unicode, ...]
        :arg subject_name: optional name or list of names of subject concept

        :type object_name: unicode or [unicode, ...]
        :arg object_name: optional name or list of names of object concept

        :type stop_on_match: bool
        :arg stop_on_match: True to return results after first match is found; default False

        """
        logger.debug(
            "Searching for '{0}' relationship where subject={1}, object={2}, count={3}".format(
                relationship_type_name, subject_name, object_name, relationship_number))

        if relationship_number:
            relationship_number = int(relationship_number)

        all_matches = []
        if not subject_name and not object_name:
            all_matches = fact_model.Relationship.select_by_values(
                relationship_type_name=relationship_type_name,
                relationship_number=relationship_number)
        else:
            # Handle strings and lists of strings
            s_names = [subject_name] if isinstance(subject_name, unicode) else subject_name
            o_names = [object_name] if isinstance(object_name, unicode) else object_name
            logger.debug("s_names={0}\no_names={1}".format(s_names, o_names))
            for s_name in s_names or [None]:
                for o_name in o_names or [None]:
                    logger.debug("s={0}, o={1}".format(s_name, o_name))
                    logger.debug("len(all_matches)={0}, stop_on_match={1}".format(
                            len(all_matches), stop_on_match))
                    if not all_matches or not stop_on_match:
                        logger.debug("Querying...")
                        matches = fact_model.Relationship.select_by_values(
                            relationship_type_name=relationship_type_name,
                            relationship_number=relationship_number,
                            subject_name=s_name,
                            object_name=o_name)
                        logger.debug("Found {0} matches".format(len(matches)))
                        all_matches.extend(matches)

        logger.debug(
            "Found {0} '{1}' relationships where subject={2}, object={3}, count={4}".format(
                len(all_matches), relationship_type_name, subject_name, object_name, 
                relationship_number))

        return all_matches


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
        logger.debug("animal_attribute_query: '{0}'".format(self.parsed_query.text))
        if not (self.parsed_query.subject_name 
                and self.parsed_query.object_name
                and self.parsed_query.relationship_type_name):
            raise ValueError("animal_attribute_query requires subject, object and relationship")

        matches = self._select_matching_relationships(
            self.parsed_query.relationship_type_name,
            subject_name=self._get_synonymous_names(self.parsed_query.subject_name),
            object_name=self._get_synonymous_names(self.parsed_query.object_name),
            relationship_number=self.parsed_query.relationship_number,
            stop_on_match=True)
        return self._bool_as_str(len(matches) == 1)

    def _animal_eat_query(self):
        """What does the subject eat?

        Examples: 
          What does the otter eat?
          What do birds eat?

        :rtype: [unicode, ...]
        :return: list of foods eaten by subject

        """
        logger.debug("animal_eat_query: '{0}'".format(self.parsed_query.text))
        if not self.parsed_query.subject_name:
            raise ValueError("animal_eat_query requires subject_name")

        if self._query_subject_is_species():
            logger.debug("Filter 'eat' relationships by species")
            matches = self._filter_subjects_by_species(self._select_matching_relationships('eat'))
        else:
            matches = self._select_matching_relationships(
                'eat', 
                subject_name=self._get_synonymous_names(self.parsed_query.subject_name))

        return sorted([o.concept_name for o in [r.object for r in matches]])

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

        if self._query_subject_is_species():
            matches = self._filter_subjects_by_species(
                self._select_matching_relationships('has', object_name='fur'))
        else:
            matches = self._select_matching_relationships(
                'has', 
                subject_name=self._get_synonymous_names(self.parsed_query.subject_name), 
                object_name='fur',
                stop_on_match=True)
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
        logger.debug("animal_how_many_query: '{0}'".format(self.parsed_query.text))
        if not (self.parsed_query.subject_name 
                and self.parsed_query.object_name
                and self.parsed_query.relationship_type_name):
            raise ValueError("animal_how_many_query requires subject, object and relationship")

        answer = None
        if self.parsed_query.subject_name == 'animals':
            # First scenario: How many animals have legs?
            matches = self._which_animal_query()
            logger.debug("{0} matches".format(len(matches)))
            answer = len(matches)
        else:
            # Second scenario: How many legs does the otter have?
            matches = self._select_matching_relationships(
                self.parsed_query.relationship_type_name,
                subject_name=self._get_synonymous_names(self.parsed_query.subject_name),
                object_name=self._get_synonymous_names(self.parsed_query.object_name),
                stop_on_match=True)
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

        if self._query_subject_is_species():
            matches = self._filter_subjects_by_species(self._select_matching_relationships('live'))
        else:
            matches = self._select_matching_relationships(
                'live',
                subject_name=self._get_synonymous_names(self.parsed_query.subject_name))
        return sorted([o.concept_name for o in [r.object for r in matches]])

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

        if self._query_subject_is_species():
            matches = self._filter_subjects_by_species(
                self._select_matching_relationships('has', object_name='scales'))
        else:
            matches = self._select_matching_relationships(
                'has',
                subject_name=self._get_synonymous_names(self.parsed_query.subject_name),
                object_name='scales',
                stop_on_match=True)
        return self._bool_as_str(len(matches) == 1)

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
          Which animals eat mammals?

        :rtype: [unicode, ...]
        :return: list of animals that meet specified criteria

        """
        logger.debug("which_animal_query: '{0}'".format(self.parsed_query.text))
        if not (self.parsed_query.subject_name 
                and self.parsed_query.object_name
                and self.parsed_query.relationship_type_name):
            raise ValueError("which_animal_query requires subject, object and relationship")

        if self._query_object_is_species():
            logger.debug("_which_animal_query on species '{0}', relationship_type='{1}'".format(
                    self.parsed_query.object_name,
                    self.parsed_query.relationship_type_name))
            matches = self._filter_objects_by_species(
                self._select_matching_relationships(
                    self.parsed_query.relationship_type_name,
                    relationship_number=self.parsed_query.relationship_number))
        else:
            logger.debug("_which_animal_query on '{0}', relationship_type='{1}'".format(
                    self.parsed_query.object_name,
                    self.parsed_query.relationship_type_name))
            matches = self._select_matching_relationships(
                self.parsed_query.relationship_type_name,
                object_name=self._get_synonymous_names(self.parsed_query.object_name),
                relationship_number=self.parsed_query.relationship_number)
 
        logger.debug("Found {0} matches: {1}".format(
                len(matches), [m.subject.concept_name for m in matches]))


        # matches = self._select_matching_relationships(
        #     self.parsed_query.relationship_type_name,
        #     object_name=self.parsed_query.object_name,
        #     relationship_number=self.parsed_query.relationship_number)

        for m in matches:
            logger.debug("{0}.concept_types={1}".format(m.subject.concept_name, m.subject.concept_types))

        # Filter results by concept_type, i.e. 'animal' or particular species
        target_concept_types = ['animal']
        if self.parsed_query.subject_type == 'species':
            target_concept_types = self._get_synonymous_names(self.parsed_query.subject_name)
        match_names = [
            c.concept_name for c in 
            self._filter_concepts_by_type([m.subject for m in matches], target_concept_types)]
        logger.debug("Matching subjects: {0}".format(match_names))

        # Reverse selection if relationship is negated
        if self.parsed_query.relationship_negation:
            logger.debug("Reversing selected set of animals")
            all_possibilities = [c.concept_name 
                                 for c in self._select_by_concept_type(target_concept_types)]
            match_names = list(set(all_possibilities) - set(match_names))
            logger.debug("Reversed match names: {0}".format(match_names))

        return match_names


