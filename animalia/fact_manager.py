#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from __future__ import unicode_literals

import json
import logging
import uuid 

import wit

from config import Config
import fact_model

logger = logging.getLogger('animalia.FactManager')


class FactManager(object):
    """
    """

    # Value between 0 and 1 that is threshold for acceptable outcome returned by wit.ai
    CONFIDENCE_THRESHOLD = Config.parsed_data_confidence_threshold

    # List of strings that indicate concept that is subject of relationship
    SUBJECT_CONCEPTS = Config.parsed_data_subject_concepts

    # Initialize wit exactly once
    _wit_initialized = False

    class ConflictError(Exception):
        """To raise if provided fact conflicts with an existing fact.
        """
        pass

    class ParseError(Exception):
        """To raise if user-supplied fact sentence cannot be parsed or if parsed data is invalid.
        """
        pass

    @classmethod
    def answer_question(cls, question):
        """

        :rtype: unicode 
        :return: string that answers provided question; None if there is no known answer

        """
        pass

    @classmethod
    def fact_from_sentence(cls, sentence):
        """Factory method to create IncomingFact from sentence.

        :rtype: :py:class:`~fact_model.IncomingFact`
        :return: IncomingFact created from provided sentence

        :type sentence: unicode
        :arg sentence: fact sentence in supported format

        """
        sentence = cls._normalize_sentence(sentence)
        incoming_fact = fact_model.IncomingFact.select_by_text(sentence)
        if not incoming_fact:
            cls._ensure_wit_initialized()
            wit_response = wit.text_query(sentence, Config.wit_access_token)
            parsed_data = json.loads(wit_response)
            incoming_fact = cls._save_parsed_fact(parsed_data=parsed_data)
        return incoming_fact

    @classmethod
    def get_fact_by_id(cls, fact_id):
        """Retrieve specified IncomingFact by id.

        :rtype: :py:class:`~fact_model.IncomingFact`
        :return: retrieved Fact; None if no matching fact exists

        :type fact_id: UUID
        :arg fact_id: id of persisted IncomingFact

        """
        return fact_model.IncomingFact.select_by_id(fact_id)

    @classmethod
    def delete(cls, fact_id):
        """Delete persisted data corresponding to this IncomingFact.

        :type fact_id: UUID
        :arg fact_id: id of IncomingFact to be deleted

        """
        pass


    # private methods

    @classmethod
    def _ensure_concept(cls, concept_name):
        """
        :rtype :py:class:`~fact_model.Concept`
        :return: existing or unpersisted, newly created Concept object with specified name

        :type concept_name: unicode
        :arg concept_name: name of concept

        """
        concept = Concept.select_by_name(concept_name)
        if not concept:
            concept = Concept(concept_name=concept_name)
        return concept

    @classmethod
    def _ensure_concept_with_type(cls, concept_data, concept_type, new_fact_id=None):
        """
        Example concept_data: [{"type": "value", "value": "otter"}]
        Example concept_type: 'animal'

        :rtype: :py:class:`~fact_model.Concept`; None if Concept cannot be created
        :return: existing or unpersisted, newly-created Concept for provided data 
        
        :type concept_data: list of dicts with 'type', 'value' and optional 'suggested' keys
        :arg concept_data: data about concept associated with specified concept_type

        :type concept_type: unicode
        :arg concept_type: concept type associated with provided concept data, e.g. 'animal', 'food'

        :type new_fact_id: uuid
        :arg new_fact_id: optional fact_id to assign to newly created Concepts or Relationship

        """
        typed_concept = None

        subjects, suggested_subjects = cls._filter_entity_values(concept_data)
        for subject in suggested:
            logger.warn("Skipping suggested subject '{0}' for concept_type '{1}'".format(
                    subject, concept_type))

        if subjects:
            if len(subjects) > 1:
                logger.warn(("Multiple subjects for concept_type '{0}': {1}; "
                             "ignoring all but '{2}'").format(
                        concept_type, subjects, subjects[0]))

            # Ensure concept for subject, e.g. 'otter' 
            subject_concept = cls._ensure_concept(subjects[0])
            # Ensure concept for type, e.g. 'animal'
            type_concept = cls._ensure_concept(concept_type)
            # Ensure 'is' relationship for subject and type, e.g. 'otter is animal'
            subject_is_type_rel = cls._ensure_relationship(subject_concept,
                                                           type_concept,
                                                           relationship_name='is',
                                                           new_fact_id=new_fact_id)
            typed_concept = subject_is_type_rel.subject
        else:
            logger.error("No subjects for concept type '{0}': {1}".format(
                    concept_type, concept_data))

        return typed_concept

    @classmethod
    def _ensure_relationship(cls, subject_concept, object_concept, relationship_name=None, 
                             relationship_number=None, new_fact_id=None):
        """
        :rtype: :py:class:`~fact_model.Relationship`
        :return: existing or unpersisted, newly created Relationship linking subject and object
        :raise: :py:class:`FactManager.ConflictError` if relationship conflicts with existing data

        :type subject_concept: :py:class:`~fact_model.Concept`
        :arg subject: subject of relationship

        :type object_concept: :py:class:`~fact_model.Concept`
        :arg object: object of relationship

        :type relationship_name: unicode
        :arg relationship_name: name of relationship, e.g. 'is', 'lives', 'eats'
        
        :type relationship_number: int
        :arg relationship_number: optional number associated with relationship, e.g. number of legs

        :type new_fact_id: uuid
        :arg new_fact_id: optional fact_id to be associated with newly-created relationship
        
        """
        # Find or create relevant RelationshipType
        relationship_type = fact_model.RelationshipType.select_by_name(relationship_name)
        if not relationship_type:
            relationship_type = fact_model.RelationshipType(
                relationship_type_name=relationship_name)

        # If subject and object concepts and relationship type all exist, check for existing
        # relationship.
        relationship = None
        if (subject_concept.concept_id 
            and object_concept.concept_id 
            and relationship_type.relationship_type_id):
            relationship = fact_model.Relationship.select_by_foreign_keys(
                subject_concept.concept_id, 
                object_concept.concept_id, 
                relationship_type.relationship_type_id)

        if relationship and relationship_number is not None:
            if relationship.count is None:
                # Update relationship data if needed
                relationship.count = relationship_number
            elif relationship.count != relationship_number:
                # If specified number conflicts with persisted number, raise.
                raise cls.ConflictError(
                    ("Conflict with existing relationship where subject={subj}, "
                     "object={obj} and relationship={rel}; persisted count conflicts "
                     "with specified count: {current_count} vs {new_count}").format(
                        subj=subject_concept.concept_name,
                        obj=object_concept.concept_name,
                        rel=relationship_name,
                        current_count=relationship.count,
                        new_count=relationship_number))
                        
        if not relationship:
            relationship = fact_model.Relationship(subject=subject_concept,
                                                   object=object_concept,
                                                   relationship_type=relationship_type,
                                                   count=relationship_number,
                                                   fact_id=new_fact_id)
        return relationship

    @classmethod
    def _ensure_wit_initialized(cls):
        """Ensure that proxy to wit.ai is ready to be used.
        """
        if not cls._wit_initialized:
            wit.init()   
            cls._wit_initialized = True

    @classmethod
    def _filter_entity_values(cls, entity_data):
        """Return lists of strings that are values of 'value' entities.

        :rtype: ([unicode, ...], [unicode, ...])
        :return: tuple of lists; first is non-suggested values, second is suggested values

        :type entity_data: list of dicts with keys 'type', 'value' and, optionally, 'suggested'
        :arg entity_data: value of 'entities' dict in wit.ai parsed fact

        """
        vals = []
        suggested_vals = []
        for entity in [e for e in entity_data if e.get('type') == 'value']:
            target_list = suggested_vals if entity.get('suggested') else vals
            target_list.append(entity['value'])
        return vals, suggested_vals

    @classmethod
    def _is_fact_intent(cls, intent):
        """Determine if specfied intent fact or query.

        :rtype: bool
        :return: True if specified intent is for a fact

        :type intent: unicode
        :arg intent: intent returned by wit.ai; e.g. 'animal_place_fact'

        """
        return (outcome.get('intent') or '').endswith('fact')

    @classmethod
    def _merge_to_db_session(cls, model):
        """Merge provided model object to database session.

        Do not commit db session.

        :rtype: instance of class from fact_model
        :return: instance after db session merge

        :type model: instance of class from fact_model
        :arg model: instance to merge to db session

        """
        return db.session.merge(model)

    @classmethod
    def _normalize_sentence(cls, sentence):
        """Normalize provided sentence for comparison, parsing and persistence.

        :rtype: unicode
        :return: normalized sentence

        :type sentence: unicode
        :arg sentence: user-provided fact or query sentence

        """
        return sentence.lower()

    @classmethod
    def _reorder_concepts_by_subject(cls, concepts):
        """Reorder provided Concepts so that subject concept is first.

        :rtype: [:py:class:`~fact_model.Concept`]
        :return: list of Concepts in which first Concept is subject
        :raise: ValueError if zero or multiple subject Concepts are found

        :type concepts: [:py:class:`~fact_model.Concept`]
        :arg concepts: list of Concepts, presumably containing one subject concept

        """
        subjects = []
        other = []
        for c in concepts:
            if c.concept_name.lower() in cls.SUBJECT_CONCEPTS:
                subjects.append(c)
            else:
                other.append(c)

        if not subjects:
            raise ValueError(
                "No subject concept found in concepts: {0}; possible subjects: {1}".format(
                    [c.concept_name for c in concepts], cls.SUBJECT_CONCEPTS))
        if len(subjects) != 1:
            raise ValueError(
                "Multiple subject concepts found in concepts: {0}; subjects: {1}".format(
                    [c.concept_name for c in concepts], [c.concept_name for c in subjects]))

        return subjects.extend(other)

    @classmethod
    def _save_parsed_fact(cls, parsed_data=None):
        """Persist IncomingFact and related ORM objects created from provided parsed_data.

        Do not commit db session.
        See wit_responses.py for sample response data.

        :rtype: :py:class:`~fact_model.IncomingFact`
        :return: newly saved IncomingFact created from provided data; None if fact cannot be created
        :raise: :py:class:`FactManager.ParseError` if provided data is invalid
        :raise: :py:class:`FactManager.ConflictError` if provided data conflicts with existing fact

        :type parsed_data: dict
        :arg parsed_data: data returned from wit.ai

        """
        # print("\nPARSED_DATA")
        # from pprint import pprint
        # pprint(parsed_data)

        def raise_parse_error(message):
            """Wrapper to raise consistently formatted ParseError exceptions.
            """
            raise cls.ParseError("Invalid parsed fact data: {0}; parsed_data={1}".format(
                    message, json.dumps(parsed_data)))

        # Verify parsed_data as much as possible before processing
        cls._verify_parsed_fact_data(parsed_data, raise_parse_error)

        # It is safe to grab first outcome since verification passed
        outcome = parsed_data['outcomes'][0]
        logger.debug("Handling outcome data: {0}".format(outcome))

        # Id for new IncomingFact and for any Relationships created to record fact.
        new_fact_id = uuid.uuid4()
        logger.debug("New fact_id={0}".format(new_fact_id))

        # Iterate entities, selecting or creating Concepts as needed
        outcome_entities = outcome.get('entities') or {}
        concepts = []
        for entity_type, entity_data in outcome_entities.iteritems(): 
            # entity_type is 'relationship', 'number', 'animal', 'species', 'place', etc.
            # entity_data is list of dicts with keys 'type', 'value' and optionally 'suggested'
            if entity_type not in ('relationship', 'number'):
                concept = cls._ensure_concept_with_type(entity_data, entity_type)
                if not concept:
                    raise_parse_error("Invalid data for concept_type '{0}': {1}".format(
                            entity_type, json.dumps(entity_data)))
                concepts.append(concept)

        # Verify two concepts
        if len(concepts) != 2:
            raise_parse_error("Expected 2 concept entities, found {0}: {1}".format(
                    len(concepts), ["'{}'".format(c.concept_name) for c in concepts]))

        # Reorder concepts so that subject concept is first
        try:
            concepts = cls._reorder_concepts_by_subject(concepts)
            subject_concept = concepts[0]
            object_concept = concepts[1]
        except ValueError as ex:
            raise_parse_error(str(ex))

        # Select or create Relationship linking Concepts
        relationship_entity_data = outcome_entities.get('relationship')
        relationship_names, suggested = cls._filter_entity_values(relationship_entity_data)
        if len(relationship_names) != 1:
            raise_parse_error(
                ("Expected 1 relationship entity for subject '{subj}' and object '{obj}'; "
                 "found {count}").format
                (subj=subject_concept.concept_name, 
                 obj=object_concept.concept_name, 
                 count=len(relationship_names)))
        for name in suggested:
            logger.warn(("Skipping suggested relationship '{0}' for subject '{1}' "
                         "and object '{2}'").format(
                    name, subject_concept.concept_name, object_concept.concept_name))

        # Find relationship number if present
        relationship_number = None
        if outcome_entities.get('number'):
            relationship_numbers, _ = cls._filter_entity_values(outcome_entities['number'])
            if len(relationship_numbers) == 1:
                relationship_number = relationship_numbers[0]

        # Select, create or update relationship
        relationship = cls._ensure_relationship(subject_concept, 
                                                object_concept, 
                                                relationship_name=relationship_names[0], 
                                                relationship_number=relationship_number,
                                                new_fact_id=new_fact_id)

        # TODO: Deal with failed or duplicated relationships

        # Merge relationship to db session
        cls._merge_to_db_session(relationship)

        # Create, merge and return IncomingFact record
        incoming_fact = fact_model.IncomingFact(fact_id=new_fact_id, 
                                                fact_text=parsed_data['_text'], 
                                                parsed_fact=json.dumps(parsed_data))
        return cls._merge_to_db_session(incoming_fact)

    @classmethod
    def _verify_parsed_fact_data(cls, parsed_fact_data, raise_fn):
        """Raise if provided parsed fact data does not appear valid.

        Run checks that do not require much processing:
        * Presence of '_text' attribute
        * Intent looks like fact
        * Confidence rating meets threshold
        * Presence of exactly one outcome
        * Outcome has sufficient entities
        * Outcome has exactly one relationship entity

        :type parsed_fact_data: dict
        :arg parsed_fact_data: JSON response from wit.ai

        :type raise_fn: fn(message)
        :arg raise_fn: function to call if problem is found

        """
        # _text attribute is required
        sentence = parsed_fact_data.get('_text')
        if not sentence:
            raise_fn("No _text attribute")

        # Verify that parsed data is fact and not query
        if not cls._is_fact_intent(outcome['intent']):
            raise_fn("Non-fact outcome intent '{0}'".format(outcome['intent']))

        # Skip outcomes with low confidence rating
        if outcome['confidence'] < cls.CONFIDENCE_THRESHOLD:
            raise_fn("Confidence={0}, threshold={1}".format(
                    outcome['confidence'], cls.CONFIDENCE_THRESHOLD))

        # Expect exactly one outcome
        outcomes = parsed_fact_data.get('outcomes') or []
        if len(outcomes) != 1:
            raise_fn("Expected 1 outcome, found {0}".format(len(outcomes)))
        outcome = outcomes[0]

        # Expect at least 3 entities overall: relationship, subject and object
        entities = outcome.get('entities') or {}
        if len(entities) < 3:
            raise_fn("Expected at least 3 entities, found {0}".format(len(entities)))

        # Expect exactly one relationship entity
        relationship_entity = entities.get('relationship') or []
        if len(relationship_entity) != 1:
            raise_fn("Expected 1 relationship entity, found {0}".format(len(relationship_entity)))


