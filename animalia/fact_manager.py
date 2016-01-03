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


class IncomingFactError(Exception):
    """Base class for errors processing incoming fact.
    """
    pass

class FactParseError(IncomingFactError):
    """To raise if incoming fact sentence cannot be parsed or if parsed data is invalid.
    """
    pass

class InvalidFactDataError(IncomingFactError):
    """To raise if data parsed from fact does not meet expectations.
    """
    pass

class ConflictingFactError(IncomingFactError):
    """To raise if incoming fact conflicts with existing fact data.
    """
    def __init__(self, *args, **kwargs):
        """
        :type conflicting_fact_id: uuid
        :arg conflicting_fact_id: conflicting fact_id 
        """
        self.conflicting_fact_id = kwargs.pop('conflicting_fact_id')
        super(ConflictingFactError, self).__init__(*args, **kwargs)

class DuplicateFactError(IncomingFactError):
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
    """
    """

    # Value between 0 and 1 that is threshold for acceptable outcome returned by wit.ai
    CONFIDENCE_THRESHOLD = Config.parsed_data_confidence_threshold

    # Names of entities that are related to relationships or are subjects
    RELATIONSHIP_ENTITY_TYPES = Config.parsed_data_relationship_entity_types
    SUBJECT_ENTITY_TYPES = Config.parsed_data_subject_entity_types

    # Initialize wit exactly once
    _wit_initialized = False

    # Pattern for stripping characters from user-specified fact sentences.
    _non_alnum_exp = re.compile(r'[^\w\s]', flags=re.UNICODE)

    @classmethod
    def delete_fact_by_id(cls, fact_id):
        """Delete persisted data corresponding to this IncomingFact.

        :type fact_id: UUID
        :arg fact_id: id of IncomingFact to be deleted

        """
        pass

    @classmethod
    def fact_from_sentence(cls, sentence):
        """Factory method to create IncomingFact from sentence.

        :rtype: :py:class:`~fact_model.IncomingFact`
        :return: IncomingFact object created from provided sentence
        :raise: :py:class:`IncomingFactError` if fact cannot be processed

        :type sentence: unicode
        :arg sentence: fact sentence in supported format

        """
        sentence = cls._normalize_sentence(sentence)
        if not sentence:
            raise FactParseError("Invalid fact sentence provided")
        incoming_fact = fact_model.IncomingFact.select_by_text(sentence)
        if not incoming_fact:
            wit_response = cls._query_wit(sentence)
            # TODO: Handle wit parse error
            parsed_data = json.loads(wit_response)
            incoming_fact = cls._save_parsed_fact(parsed_data=parsed_data)
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
    def query_facts(cls, query):
        """

        :rtype: unicode 
        :return: string that answers provided question; None if there is no known answer

        """
        pass


    # private methods

    @classmethod
    def _concepts_from_entity_data(cls, entities, raise_fn, new_fact_id=None):
        """Select existing or create new Concepts to represent subject and object entities.

        Dict 'entities' maps entity_types to lists of entity_data dicts.
        Values of entity_type are 'relationship', 'number', 'animal', 'species', 'place', etc.
        Keys of entity data dict are 'type', 'value' and optionally 'suggested'.

        :rtype: tuple of two :py:class:`~fact_model.Concept` objects
        :return: (subject_concept, object_concept)
        :raise: raise_fn is called if subject and object concepts cannot be found or created

        :type entities: dict
        :arg entities: dict of entity_types to list of entity data dicts
        
        :type raise_fn: fn(message)
        :arg raise_fn: function to call if problem is found

        :type new_fact_id: uuid
        :arg new_fact_id: optional fact_id to assign to newly created 'is' Relationships

        """
        subject_concept = None
        object_concept = None
        for entity_type, entity_data in entities.iteritems(): 
            if entity_type not in cls.RELATIONSHIP_ENTITY_TYPES:
                concept = cls._ensure_concept_with_type(
                    entity_data, entity_type, new_fact_id=new_fact_id)
                if not concept:
                    raise_fn("Invalid data for concept_type '{0}': {1}".format(
                            entity_type, entity_data))
                if entity_type in cls.SUBJECT_ENTITY_TYPES:
                    if subject_concept != None:
                        raise_fn("Found multiple subject concepts: {0}, {1}".format(
                                subject_concept.concept_name, concept.concept_name))
                    subject_concept = concept
                else:
                    if object_concept != None:
                        raise_fn("Found multiple object concepts: {0}, {1}".format(
                                object_concept.concept_name, concept.concept_name))
                    object_concept = concept
        if not subject_concept:
            raise_fn("No subject concept found")
        if not object_concept:
            raise_fn("No object concept found")
        return subject_concept, object_concept

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
        :arg new_fact_id: optional fact_id to assign to newly created 'is' Relationships

        """
        typed_concept = None

        subjects, suggested_subjects = cls._filter_entity_values(concept_data)
        for subject in suggested_subjects:
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
                                                           new_fact_id=new_fact_id,
                                                           error_on_duplicate=False)
            typed_concept = subject_is_type_rel.subject
        else:
            logger.error("No subjects for concept type '{0}': {1}".format(
                    concept_type, concept_data))

        return typed_concept

    @classmethod
    def _ensure_relationship(cls, subject_concept, object_concept, relationship_name=None, 
                             relationship_number=None, new_fact_id=None, error_on_duplicate=False):
        """
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
                                                   relationship_type=relationship_type,
                                                   count=relationship_number,
                                                   fact_id=new_fact_id)
        return relationship

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
        return intent.endswith('fact')

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
    def _relationship_from_entity_data(cls, entities, raise_fn, new_fact_id=None):
        """Select existing or create new Relationship ORM to represent relationship data.

        Dict 'entities' maps entity_types to lists of entity_data dicts.
        Values of entity_type are 'relationship', 'number', 'animal', 'species', 'place', etc.
        Keys of entity data dict are 'type', 'value' and optionally 'suggested'.

        :rtype: :py:class:`~fact_model.Relationship`
        :return: existing or newly-created and non-persisted Relationship
        :raise: raise_fn is called if trouble arises

        :type entities: dict
        :arg entities: dict of entity_types to lists of entity data dicts
        
        :type raise_fn: fn(message)
        :arg raise_fn: function to call if problem is found

        :type new_fact_id: uuid
        :arg new_fact_id: optional fact_id to assign to Relationship, if newly created

        """
        # Select or create subject and object Concept objects
        subject_concept, object_concept = cls._concepts_from_entity_data(
            entities, raise_fn, new_fact_id=new_fact_id)

        # Select or create Relationship linking Concepts
        relationship_entity_data = entities.get('relationship') or []
        relationship_names, suggested = cls._filter_entity_values(relationship_entity_data)
        if len(relationship_names) != 1:
            raise_fn(("Expected 1 relationship entity for subject '{subj}' and object '{obj}'; "
                      "found {count}").format(
                    subj=subject_concept.concept_name, 
                    obj=object_concept.concept_name, 
                    count=len(relationship_names)))

        # Skip suggested relationships
        for name in suggested:
            logger.warn(("Skipping suggested relationship '{0}' for subject '{1}' "
                         "and object '{2}'").format(
                    name, subject_concept.concept_name, object_concept.concept_name))

        # Find relationship number if present
        relationship_number = None
        if entities.get('number'):
            relationship_numbers, _ = cls._filter_entity_values(entities['number'])
            if len(relationship_numbers) == 1:
                relationship_number = relationship_numbers[0]

        # Select, create or update relationship, raising if relationship duplicates existing data.
        relationship = cls._ensure_relationship(subject_concept, 
                                                object_concept, 
                                                relationship_name=relationship_names[0], 
                                                relationship_number=relationship_number,
                                                new_fact_id=new_fact_id,
                                                error_on_duplicate=True)
        return relationship


    @classmethod
    def _save_parsed_fact(cls, parsed_data=None):
        """Persist IncomingFact and related ORM objects created from provided parsed_data.

        :rtype: :py:class:`~fact_model.IncomingFact`
        :return: newly saved IncomingFact created from provided data; None if fact cannot be created
        :raise: :py:class:`InvalidFactDataError` if provided data is invalid
        :raise: :py:class:`ConflictingFactError` if data conflicts with existing fact
        :raise: :py:class:`DuplicateFactError` if data is attributed to existing fact

        :type parsed_data: dict
        :arg parsed_data: data returned from wit.ai

        See wit_responses.py for samples of valid parsed_data.
        Note: New and updated ORM objects are merged to db session but not committed.


        """
        # print("\nPARSED_DATA")
        # from pprint import pprint
        # pprint(parsed_data)

        def raise_invalid_data_error(message):
            """Wrapper to raise consistently formatted InvalidFactData exceptions.
            """
            raise InvalidFactDataError("Invalid parsed fact data: {0}; parsed_data={1}".format(
                    message, parsed_data))

        # Verify parsed_data as much as possible before processing
        parsed_outcome = cls._verify_parsed_fact_data(parsed_data, raise_invalid_data_error)
        logger.debug("Handling outcome data: {0}".format(parsed_outcome))

        # Id for new IncomingFact and for any Relationships created to record fact.
        new_fact_id = uuid.uuid4()
        logger.debug("New fact_id={0}".format(new_fact_id))

        # Create or select Relationship ORM object representing parsed entity data.
        # It is safe to directly access outcome['entities'] since verification passed.
        try:
            relationship = cls._relationship_from_entity_data(
                parsed_outcome['entities'], raise_invalid_data_error, new_fact_id=new_fact_id)

            # Merge relationship to db session
            cls._merge_to_db_session(relationship)

            # Create, merge and return IncomingFact record
            incoming_fact = fact_model.IncomingFact(fact_id=new_fact_id, 
                                                    fact_text=parsed_data['_text'], 
                                                    parsed_fact=json.dumps(parsed_data))
            incoming_fact = cls._merge_to_db_session(incoming_fact)

        except DuplicateFactError as ex:
            logger.warn(ex.message)
            incoming_fact = fact_model.IncomingFact.select_by_id(ex.duplicate_fact_id)
            
        return incoming_fact

    @classmethod
    def _verify_parsed_fact_data(cls, parsed_fact_data, raise_fn):
        """Raise if provided parsed fact data does not appear valid.

        Run checks that do not require much processing:
        * Presence of '_text' attribute
        * Presence of exactly one outcome
        * Intent looks like fact
        * Confidence rating meets threshold
        * Outcome has sufficient entities
        * Outcome has exactly one relationship entity
        * Outcome has exactly one subject entity

        :rtype: dict
        :return: 'outcome' element of provided parsed_fact_data if everything meets expectations
        :raise: :py:class:`InvalidFactDataError` if parsed_fact_data does not meet expectations

        :type parsed_fact_data: dict
        :arg parsed_fact_data: JSON response from wit.ai

        :type raise_fn: fn(message)
        :arg raise_fn: function to call if problem is found

        """
        # _text attribute is required
        sentence = parsed_fact_data.get('_text')
        if not sentence:
            raise_fn("No _text attribute")

        # Expect exactly one outcome
        outcomes = parsed_fact_data.get('outcomes') or []
        if len(outcomes) != 1:
            raise_fn("Expected 1 outcome, found {0}".format(len(outcomes)))
        outcome = outcomes[0]

        # Verify that parsed data is fact and not query
        if not cls._is_fact_intent(outcome['intent']):
            raise_fn("Non-fact outcome intent '{0}'".format(outcome['intent']))

        # Skip outcomes with low confidence rating
        if outcome['confidence'] < cls.CONFIDENCE_THRESHOLD:
            raise_fn("Confidence={0}, threshold={1}".format(
                    outcome['confidence'], cls.CONFIDENCE_THRESHOLD))

        # Expect at least 3 entities overall: relationship, subject and object
        entities = outcome.get('entities') or {}
        if len(entities) < 3:
            raise_fn("Expected at least 3 entities, found {0}".format(len(entities)))

        # Expect exactly one relationship entity
        relationship_entity = entities.get('relationship') or []
        if len(relationship_entity) != 1:
            raise_fn("Expected 1 relationship entity, found {0}".format(len(relationship_entity)))

        # Expect exactly one subject entity
        subjects = filter(lambda k: k in cls.SUBJECT_ENTITY_TYPES, entities.keys())
        if len(subjects) != 1:
            raise_fn("Expected 1 subject entity, found {0}: {1}; possible subjects: {2}".format(
                    len(subjects), subjects, cls.SUBJECT_ENTITY_TYPES))

        return outcome

