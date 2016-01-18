#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from __future__ import unicode_literals

import json
import logging
import re
import uuid 

import wit

from config import Config
import fact_model

logger = logging.getLogger('animalia.FactManager')


class IncomingDataError(Exception):
    """Base class for errors processing incoming fact or query.
    """
    pass

class SentenceParseError(IncomingDataError):
    """To raise if incoming fact or query sentence cannot be parsed.
    """
    pass

class InvalidFactDataError(IncomingDataError):
    """To raise if data parsed from fact sentence does not meet expectations.
    """
    pass

class InvalidQueryDataError(IncomingDataError):
    """To raise if data parsed from query sentence does not meet expectations.
    """
    pass

class ConflictingFactError(IncomingDataError):
    """To raise if incoming fact conflicts with existing fact data.
    """
    def __init__(self, *args, **kwargs):
        """
        :type conflicting_fact_id: uuid
        :arg conflicting_fact_id: conflicting fact_id 
        """
        self.conflicting_fact_id = kwargs.pop('conflicting_fact_id')
        super(ConflictingFactError, self).__init__(*args, **kwargs)

class DuplicateFactError(IncomingDataError):
    """To raise if incoming fact is already represented and associated with existing fact.
    """
    def __init__(self, *args, **kwargs):
        """
        :type duplicate_fact_id: uuid
        :arg duplicate_fact_id: duplicate fact_id 
        """
        self.duplicate_fact_id = kwargs.pop('duplicate_fact_id')
        super(DuplicateFactError, self).__init__(*args, **kwargs)


class FactManager(object):
    """Manage lifecycle of persisted facts.
    """

    # Initialize wit exactly once
    _wit_initialized = False

    # Pattern for stripping characters from user-specified fact sentences.
    _non_alnum_exp = re.compile(r'[^\w\s]', flags=re.UNICODE)

    @classmethod
    def delete_fact_by_id(cls, fact_id):
        """Delete persisted data corresponding to this IncomingFact.

        :rtype: UUID
        :return: id of deleted fact; None if no fact was found

        :type fact_id: UUID
        :arg fact_id: id of IncomingFact to be deleted

        """
        deleted_fact_id = None
        fact = fact_model.IncomingFact.select_by_id(fact_id)
        if fact:
            for relationship in fact_model.Relationship.select_by_fact_id(fact_id):
                cls._delete_from_db_session(relationship)
            cls._delete_from_db_session(fact)
            deleted_fact_id = fact_id
        return deleted_fact_id

    @classmethod
    def fact_from_sentence(cls, fact_sentence):
        """Factory method to create IncomingFact from sentence.

        :rtype: :py:class:`~fact_model.IncomingFact`
        :return: IncomingFact object created from provided sentence
        :raise: :py:class:`IncomingDataError` if fact cannot be processed

        :type fact_sentence: unicode
        :arg fact_sentence: fact sentence in format understandable by configured wit.ai instance

        """
        fact_sentence = cls._normalize_sentence(fact_sentence)
        if not fact_sentence:
            raise SentenceParseError("Empty fact sentence provided")
        incoming_fact = fact_model.IncomingFact.select_by_text(fact_sentence)
        if not incoming_fact:
            wit_response = cls._query_wit(fact_sentence)
            # TODO: Handle wit parse error
            try:
                parsed_sentence = ParsedSentence.from_wit_response(json.loads(wit_response))
                if not parsed_sentence.is_fact():
                    raise ValueError("Sentence has non-fact intent '{0}'".format(
                            parsed_sentence.intent))
                if parsed_sentence.relationship_negation:
                    raise ValueError("Cannot handle fact with negated relationship".format(
                            parsed_sentence.intent))
            except ValueError as ex:
                raise InvalidFactDataError("Invalid fact: {0}; wit_response={1}".format(
                        ex, wit_response))
            incoming_fact = cls._save_parsed_fact(parsed_sentence)
            fact_model.db.session.commit()
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
    def query_facts(cls, query_sentence):
        """Use wit to parse incoming sentence; use recorded facts to answer query if possible.

        :rtype: unicode 
        :return: string that answers provided question; None if there is no known answer
        :raise: InvalidQueryDataError if provided sentence is invalid or cannot be parsed

        :type query_sentence: unicode
        :arg query_sentence: query sentence in format understandable by configured wit.ai instance

        """
        query_sentence = cls._normalize_sentence(query_sentence)
        if not query_sentence:
            raise InvalidQueryDataError("Empty query sentence provided")
        wit_response = cls._query_wit(query_sentence)
        # TODO: Handle wit parse error
        try:
            parsed_sentence = ParsedSentence.from_wit_response(json.loads(wit_response))
        except ValueError as ex:
            raise InvalidQueryDataError("Invalid query: {0}; wit_response={1}".format(
                    ex, wit_response))
        return cls._retrieve_query_answer(parsed_sentence)


    # private methods

    @classmethod
    def _delete_from_db_session(cls, model):
        """Delete provided model object to database session.

        :type model: instance of class from fact_model
        :arg model: instance to delete from db session

        """
        fact_model.db.session.delete(relationship)

    @classmethod
    def _ensure_concept(cls, concept_name):
        """
        :rtype :py:class:`~fact_model.Concept`
        :return: existing or unpersisted, newly created Concept object with specified name

        :type concept_name: unicode
        :arg concept_name: name of concept

        """
        concept = fact_model.Concept.select_by_name(concept_name)
        if not concept:
            concept = fact_model.Concept(concept_name=concept_name)
        return concept

    @classmethod
    def _ensure_concept_with_type(cls, concept_name, concept_type, new_fact_id=None):
        """Select or create Concept ORM for provided data.

        :rtype: :py:class:`~fact_model.Concept`
        :return: existing or unpersisted, newly-created Concept for provided data 
        
        :type concept_name: unicode
        :arg concept_name: name of concept, e.g. 'otter', 'fish'

        :type concept_type: unicode
        :arg concept_type: concept type associated with provided concept data, e.g. 'animal', 'food'

        :type new_fact_id: uuid
        :arg new_fact_id: optional fact_id to assign to newly created 'is' Relationship

        """
        # Ensure concept for subject, e.g. 'otter' 
        subject_concept = cls._ensure_concept(concept_name)
        # Ensure concept for type, e.g. 'animal'
        type_concept = cls._ensure_concept(concept_type)

        # Verify no contradiction or loop
        # TODO

        # Ensure 'is' relationship for subject and type, e.g. 'otter is animal'
        is_relationship = cls._ensure_relationship(subject_concept,
                                                   type_concept,
                                                   relationship_name='is',
                                                   new_fact_id=new_fact_id,
                                                   error_on_duplicate=False)
        return is_relationship.subject

    @classmethod
    def _ensure_relationship(cls, subject_concept, object_concept, relationship_name=None, 
                             relationship_number=None, new_fact_id=None, error_on_duplicate=False):
        """Select or create Relationship ORM for provided data.

        :rtype: :py:class:`~fact_model.Relationship`
        :return: existing or unpersisted, newly created Relationship linking subject and object

        :raise: :py:class:`DuplicateFactError` if relationship already exists
        :raise: :py:class:`ConflictingFactError` if relationship conflicts with existing data

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
        
        :type error_on_duplicate: bool
        :type error_on_duplicate: if True and relationship exists, raise DuplicateFactError
        
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

        # If relationship exists, it may be a duplicate or a conflict or in need of update,
        # depending on state of relationship_number and relationship.count.
        if relationship:
            if relationship_number is None or relationship_number == relationship.count:
                if error_on_duplicate:
                    raise DuplicateFactError(
                        ("Found existing fact {fact_id} with subject={subj}, object={obj}, "
                         "relationship={rel}").format(
                            fact_id=relationship.fact_id,
                            subj=subject_concept.concept_name,
                            obj=object_concept.concept_name,
                            rel=relationship_name),
                        duplicate_fact_id=relationship.fact_id)

            elif relationship.count is not None and relationship_number != relationship.count:
                raise ConflictingFactError(
                    ("Found conflicting fact {fact_id} with subject={subj}, object={obj}, "
                     "relationship={rel}; persisted count conflicts with specified count: "
                     "{current_count} vs {new_count}").format(
                        fact_id=relationship.fact_id,
                        subj=subject_concept.concept_name,
                        obj=object_concept.concept_name,
                        rel=relationship_name,
                        current_count=relationship.count,
                        new_count=relationship_number),
                    conflicting_fact_id=relationship.fact_id)

            elif relationship_number is not None:
                # Otherwise, update existing relationship with count information.
                relationship.count = relationship_number

        if not relationship:
            relationship = fact_model.Relationship(subject=subject_concept,
                                                   object=object_concept,
                                                   relationship_types=[relationship_type],
                                                   count=relationship_number,
                                                   fact_id=new_fact_id)
        return relationship

    @classmethod
    def _merge_to_db_session(cls, model):
        """Merge provided model object to database session.

        :rtype: instance of class from fact_model
        :return: instance after db session merge

        :type model: instance of class from fact_model
        :arg model: instance to merge to db session

        """
        return fact_model.db.session.merge(model)

    @classmethod
    def _normalize_sentence(cls, sentence):
        """Normalize provided sentence for comparison, parsing and persistence.

        :rtype: unicode
        :return: normalized sentence

        :type sentence: unicode
        :arg sentence: user-provided fact or query sentence

        """
        if sentence:
            sentence = re.sub(cls._non_alnum_exp, '', sentence)
            sentence = sentence.lower()
        return sentence

    @classmethod
    def _query_wit(cls, sentence):
        """Wrapper around wit.ai text_query API.

        :rtype: dict
        :return: wit.ai response

        :type sentence: unicode
        :arg sentence: input for wit.text_query
        
        """
        if not cls._wit_initialized:
            wit.init()   
            cls._wit_initialized = True
        return wit.text_query(sentence, Config.wit_access_token)

    @classmethod
    def _retrieve_query_answer(cls, parsed_sentence):
        """
        :rtype: unicode
        :return: answer to question or None if no answer could be found

        :type parsed_sentence: :py:class:`ParsedSentence`
        :arg parsed_sentence: object containing parsed query components

        """
        pass

    @classmethod
    def _save_parsed_fact(cls, parsed_sentence):
        """Persist IncomingFact and related ORM objects created from provided parsed_data.

        :rtype: :py:class:`~fact_model.IncomingFact`
        :return: newly saved IncomingFact created from provided data; None if fact cannot be created

        :raise: :py:class:`InvalidFactDataError` if ORM objects cannot be created
        :raise: :py:class:`ConflictingFactError` if data conflicts with existing fact
        :raise: :py:class:`DuplicateFactError` if data is attributed to existing fact

        :type parsed_sentence: :py:class:`ParsedSentence`
        :arg parsed_sentence: object containing parsed fact components

        Note: New and updated ORM objects are merged to db session but not committed.

        """
        # Id for new IncomingFact and for any Relationships created to record fact.
        new_fact_id = uuid.uuid4()
        logger.debug("New fact_id={0}".format(new_fact_id))

        # Create or select subject and object Concept ORM objects.
        subject_concept = cls._ensure_concept_with_type(
            parsed_sentence.subject_name, parsed_sentence.subject_type, new_fact_id=new_fact_id)
        object_concept = cls._ensure_concept_with_type(
            parsed_sentence.object_name, parsed_sentence.object_type, new_fact_id=new_fact_id)

        # Create or select Relationship ORM object.
        try:
            relationship = cls._ensure_relationship(
                subject_concept,
                object_concept,
                relationship_name=parsed_sentence.relationship_name,
                relationship_number=parsed_sentence.relationship_number,
                new_fact_id=new_fact_id,
                error_on_duplicate=True)

            # Merge relationship to db session
            cls._merge_to_db_session(relationship)

            # Create, merge and return IncomingFact record
            incoming_fact = fact_model.IncomingFact(fact_id=new_fact_id, 
                                                    fact_text=parsed_sentence.text,
                                                    parsed_fact=parsed_sentence.orig_response)
            incoming_fact = cls._merge_to_db_session(incoming_fact)

        except DuplicateFactError as ex:
            logger.warn(ex.message)
            incoming_fact = fact_model.IncomingFact.select_by_id(ex.duplicate_fact_id)
            
        return incoming_fact


class ParsedSentence(object):
    """Encapsulate data contained in response from wit.ai text_query request.

    See wit_responses.py for samples of valid parsed_data.
    """

    # Value between 0 and 1 that is threshold for acceptable outcome returned by wit.ai
    CONFIDENCE_THRESHOLD = Config.parsed_data_confidence_threshold

    # Names of entities that are related to relationships or are subjects
    RELATIONSHIP_KEY = 'relationship'
    RELATIONSHIP_COUNT_KEY = 'number'
    RELATIONSHIP_NEGATION_KEY = 'negation'
    SUBJECT_ENTITY_TYPES = Config.parsed_data_subject_entity_types

    def __init__(self, text=None, confidence=None, intent=None, 
                 subject_name=None, subject_type=None, object_name=None, object_type=None,
                 relationship_name=None, relationship_number=None, relationship_negation=False):
        """
        :type text: unicode
        :type confidence: float
        :type intent: unicode
        :type subject_name: unicode
        :type subject_type: unicode
        :type object_name: unicode
        :type object_type: unicode
        :type relationship_name: unicode
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
        self.relationship_name = relationship_name
        self.relationship_number = relationship_number or None
        self.relationship_negation = relationship_negation
        self.orig_response = None

    @classmethod
    def from_wit_response(cls, response_data):
        """Factory method that extracts subject, object and relationship and data from wit response.

        Verify:
        * Presence of '_text' attribute
        * Presence of exactly one outcome
        * Outcome 'intent' is defined
        * Confidence rating meets threshold
        * Outcome has exactly one relationship entity
        * Outcome has exactly one subject entity
        * Outcome has exactly one object

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

        # Expect exactly one outcome
        outcomes = response_data.get('outcomes') or []
        if len(outcomes) != 1:
            raise ValueError("Expected 1 outcome, found {0}".format(len(outcomes)))
        outcome = outcomes[0]

        # Intent attribute is required
        instance.intent = outcome.get('intent')
        if not instance.intent:
            raise ValueError("Outcome has no intent attribute")

        # Skip outcomes with low confidence rating
        instance.confidence = outcome['confidence']
        if instance.confidence < cls.CONFIDENCE_THRESHOLD:
            raise ValueError("Outcome confidence falls below threshold: {0} < {1}".format(
                    instance.confidence, cls.CONFIDENCE_THRESHOLD))

        # Expect at least 3 entities overall: relationship, subject and object
        for entity_type, entity_data in outcome['entities'].iteritems(): 
            vals, suggested_vals = cls._filter_entity_values(entity_data)
            if entity_type == cls.RELATIONSHIP_KEY:
                if suggested_vals:
                    logger.warn("Skipping suggested relationship names: {0}".format(
                            suggested_vals))
                if len(vals) > 1:
                    logger.warn("Multiple relationship names: {0}; ignoring all but '{1}'".format(
                            vals, vals[0]))
                instance.relationship_name = vals[0]

            elif entity_type == cls.RELATIONSHIP_COUNT_KEY:
                if len(vals) > 1:
                    raise ValueError("Expected at most 1 relationship number; found {0}".format(
                            len(vals)))
                if vals:
                    instance.relationship_number = vals[0]

            elif entity_type == cls.RELATIONSHIP_NEGATION_KEY:
                if len(vals) > 1:
                    raise ValueError("Expected at most 1 negation entity; found {0}".format(
                            len(vals)))
                if vals:
                    if vals[0] == 'not':
                        instance.relationship_negation = True
                    else:
                        raise ValueError("Unexpected value of negation entity: '{0}'".format(
                                vals[0]))

            elif entity_type in cls.SUBJECT_ENTITY_TYPES:
                if instance.subject_type:
                    raise ValueError("Found multiple subject entities: {0}, {1}".format(
                            instance.subject_type, entity_type))
                instance.subject_type = entity_type
                if suggested_vals:
                    logger.warn("Skipping suggested subjects for type {0}: {1}".format(
                            instance.subject_type, suggested_vals))
                if len(vals) > 1:
                    logger.warn("Multiple subjects for type {0}: {1}; ignoring all but '{2}'".format(
                            instance.subject_type, vals, vals[0]))
                instance.subject_name = vals[0]

            elif instance.object_type:
                raise ValueError("Found multiple object entities: {0}, {1}".format(
                        instance.object_type, entity_type))

            else:
                instance.object_type = entity_type
                if suggested_vals:
                    logger.warn("Skipping suggested objects for type {0}: {1}".format(
                            instance.subject_type, suggested_vals))
                if len(vals) > 1:
                    logger.warn("Multiple objects for type {0}: {1}; ignoring all but {2}".format(
                            instance.object_type, vals, vals[0]))
                instance.object_name = vals[0]

        if not instance.subject_type:
            raise ValueError("No subject entity found")
        if not instance.object_type:
            raise ValueError("No object entity found")
        if not instance.relationship_name:
            raise ValueError("No relationship entity found")

        # Serialize and preserve original response data
        instance.orig_response = json.dumps(response_data)

        return instance

    def is_fact(self):
        """Determine if this sentence data represents fact or query.

        :rtype: bool
        :return: True if this sentence is for a fact

        """
        return self.intent.endswith('fact')


    # private methods

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
        for entity in [e for e in entity_data or [] if e.get('type') == 'value']:
            target_list = suggested_vals if entity.get('suggested') else vals
            target_list.append(entity['value'])
        return vals, suggested_vals

