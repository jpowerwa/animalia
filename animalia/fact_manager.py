#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""FactManager is entry point for all animalia API functionality.

FactManager manages lifecycle of persisted facts and provides entry point for querying data.
Uses external wit.ai API for parsing user-provided facts and queries.

FactManager is agnostic to data domain.

"""

from __future__ import unicode_literals

import json
import logging
import re
import uuid 

import wit

from config import Config
import exc
import fact_model
from fact_query import FactQuery
from parsed_sentence import ParsedSentence


logger = logging.getLogger('animalia.FactManager')


class FactManager(object):
    __doc__ = __doc__

    # Initialize wit exactly once
    _wit_initialized = False

    # Pattern for stripping characters from user-specified fact sentences.
    _non_alnum_exp = re.compile(r'[^\w\s]', flags=re.UNICODE)

    @classmethod
    def add_concept(cls, concept_name, concept_type):
        """Add Concept for name and type and 'is' relationship between the two.

        Need this because wit is unfortunately bad at parsing important base facts
        like 'mammals is a species.'

        :type concept_name: unicode
        :arg concept_name: name of concept, e.g. 'mammals'

        :type concept_type: unicode
        :arg concept_type: name of concept_type, e.g. 'species'
        
        """
        concept = cls._ensure_concept(concept_name)
        type_concept = cls._ensure_concept(concept_type)
        is_relationship = cls._ensure_relationship(concept,
                                                   type_concept,
                                                   relationship_type_name='is',
                                                   error_on_duplicate=False)

        cls._merge_to_db_session(is_relationship)
        fact_model.db.session.commit()

    @classmethod
    def delete_fact_by_id(cls, fact_id):
        """Delete persisted data corresponding to this IncomingFact.

        :rtype: UUID
        :return: id of deleted fact; None if no fact was found

        :type fact_id: UUID
        :arg fact_id: id of IncomingFact to be deleted

        """
        logger.debug("Deleting fact {0}".format(fact_id))
        deleted_fact_id = None
        fact = fact_model.IncomingFact.select_by_id(fact_id)
        if fact:
            for relationship in fact_model.Relationship.select_by_fact_id(fact_id):
                cls._delete_from_db_session(relationship)
            cls._delete_from_db_session(fact)
            deleted_fact_id = fact_id
            fact_model.db.session.commit()
        return deleted_fact_id

    @classmethod
    def fact_from_sentence(cls, fact_sentence):
        """Factory method to create IncomingFact from sentence.

        :rtype: :py:class:`~fact_model.IncomingFact`
        :return: IncomingFact object created from provided sentence
        :raise: :py:class:`~exc.IncomingDataError` if fact cannot be processed

        :type fact_sentence: unicode
        :arg fact_sentence: fact sentence in format understandable by configured wit.ai instance

        """
        logger.debug("Processing sentence '{0}'".format(fact_sentence))
        fact_sentence = cls._normalize_sentence(fact_sentence)
        if not fact_sentence:
            raise exc.SentenceParseError("Empty fact sentence provided")
        incoming_fact = fact_model.IncomingFact.select_by_text(fact_sentence)
        if not incoming_fact:
            wit_response = cls._query_wit(fact_sentence)
            # TODO: Handle wit parse error
            try:
                parsed_sentence = ParsedSentence.from_wit_response(json.loads(wit_response))
                parsed_sentence.validate_fact()
            except ValueError as ex:
                raise exc.InvalidFactDataError("Invalid fact: {0}; wit_response={1}".format(
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
        :raise: :py:class:`~exc.IncomingQueryDataError` if sentence is invalid or cannot be parsed

        :type query_sentence: unicode
        :arg query_sentence: query sentence in format understandable by configured wit.ai instance

        """
        query_sentence = cls._normalize_sentence(query_sentence)
        if not query_sentence:
            raise exc.InvalidQueryDataError("Empty query sentence provided")
        query_sentence += '?'
        wit_response = cls._query_wit(query_sentence)
        # TODO: Handle wit parse error
        try:
            parsed_sentence = ParsedSentence.from_wit_response(json.loads(wit_response))
            return FactQuery(parsed_query=parsed_sentence).find_answer()
        except ValueError as ex:
            raise exc.InvalidQueryDataError("Invalid query: {0}; wit_response={1}".format(
                    ex, wit_response))


    # private methods

    @classmethod
    def _delete_from_db_session(cls, model):
        """Delete provided model object to database session.

        :type model: instance of class from fact_model
        :arg model: instance to delete from db session

        """
        fact_model.db.session.delete(model)

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
        :raise: :py:class:`~exc.ConflictingFactError` if data conflicts with existing fact
        
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

        # Verify no loop; if 'animal' has type 'food', 'food' cannot have type 'animal'
        if concept_name in type_concept.concept_types:
            conflicting_fact_id = None
            for concept_type_rel in type_concept.concept_type_relationships:
                if concept_type_rel.object.concept_name == concept_name:
                    conflicting_fact_id = concept_type_rel.fact_id
                    break
            msg = "Cannot add relationship '{0} is {1}'; existing relationship '{1} is {0}'".format(
                concept_name, concept_type)
            raise exc.ConflictingFactError(msg, conflicting_fact_id=conflicting_fact_id)

        # Ensure 'is' relationship for subject and type, e.g. 'otter is animal'
        is_relationship = cls._ensure_relationship(subject_concept,
                                                   type_concept,
                                                   relationship_type_name='is',
                                                   new_fact_id=new_fact_id,
                                                   error_on_duplicate=False)
        return is_relationship.subject

    @classmethod
    def _ensure_relationship(cls, subject_concept, object_concept, relationship_type_name=None, 
                             relationship_number=None, new_fact_id=None, error_on_duplicate=False):
        """Select or create Relationship ORM for provided data.

        :rtype: :py:class:`~fact_model.Relationship`
        :return: existing or unpersisted, newly created Relationship linking subject and object

        :raise: :py:class:`~exc.DuplicateFactError` if relationship already exists
        :raise: :py:class:`~exc.ConflictingFactError` if relationship conflicts with existing data

        :type subject_concept: :py:class:`~fact_model.Concept`
        :arg subject: subject of relationship

        :type object_concept: :py:class:`~fact_model.Concept`
        :arg object: object of relationship

        :type relationship_type_name: unicode
        :arg relationship_type_name: name of relationship, e.g. 'is', 'lives', 'eats'
        
        :type relationship_number: int
        :arg relationship_number: optional number associated with relationship, e.g. number of legs

        :type new_fact_id: uuid
        :arg new_fact_id: optional fact_id to be associated with newly-created relationship
        
        :type error_on_duplicate: bool
        :type error_on_duplicate: if True and relationship exists, raise DuplicateFactError
        
        """
        # Find or create relevant RelationshipType
        relationship_type = fact_model.RelationshipType.select_by_name(relationship_type_name)
        if not relationship_type:
            relationship_type = fact_model.RelationshipType(
                relationship_type_name=relationship_type_name)

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
                    raise exc.DuplicateFactError(
                        ("Found existing fact {fact_id} with subject={subj}, object={obj}, "
                         "relationship={rel}").format(
                            fact_id=relationship.fact_id,
                            subj=subject_concept.concept_name,
                            obj=object_concept.concept_name,
                            rel=relationship_type_name),
                        duplicate_fact_id=relationship.fact_id)

            elif relationship.count is not None and relationship_number != relationship.count:
                raise exc.ConflictingFactError(
                    ("Found conflicting fact {fact_id} with subject={subj}, object={obj}, "
                     "relationship={rel}; persisted count conflicts with specified count: "
                     "{current_count} vs {new_count}").format(
                        fact_id=relationship.fact_id,
                        subj=subject_concept.concept_name,
                        obj=object_concept.concept_name,
                        rel=relationship_type_name,
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
        
        Transform to lowercase and remove non-alphanumeric characters.

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
    def _save_parsed_fact(cls, parsed_sentence):
        """Persist IncomingFact and related ORM objects created from provided parsed_data.

        :rtype: :py:class:`~fact_model.IncomingFact`
        :return: newly saved IncomingFact created from provided data; None if fact cannot be created

        :raise: :py:class:`~exc.InvalidFactDataError` if ORM objects cannot be created
        :raise: :py:class:`~exc.ConflictingFactError` if data conflicts with existing fact
        :raise: :py:class:`~exc.DuplicateFactError` if data is attributed to existing fact

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
                relationship_type_name=parsed_sentence.relationship_type_name,
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

        except exc.DuplicateFactError as ex:
            logger.warn(ex.message)
            incoming_fact = fact_model.IncomingFact.select_by_id(ex.duplicate_fact_id)
            
        return incoming_fact

