#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from __future__ import unicode_literals

import fact_model

class FactManager(object):

    def ParseError(Exception):
        pass
    

    def __init__(self, **kwargs):
        self.fact_id = kwargs.get('fact_id') or None
        self.sentence = kwargs.get('sentence') or None


    # classmethods

    @classmethod
    def answer_question(cls, question):
        """

        :rtype: unicode 
        :return: string that answers provided question or None if there is no known answer

        """
        pass

    @classmethod
    def fact_from_sentence(cls, sentence):
        """Factory method to create Fact from sentence.

        :rtype: :py:class:`Fact`
        :return: Fact created from provided sentence

        :type sentence: unicode
        :arg sentence: fact sentence in supported format

        """
        sentence = cls._normalize_sentence(sentence)
        incoming_fact = fact_model.IncomingFact.select_by_text(sentence)
        if not incoming_fact:
            incoming_fact = fact_model.IncomingFact(fact_text=sentence).save()
        return incoming_fact

    @classmethod
    def get_fact_by_id(cls, fact_id):
        """Retrieve specified Fact by id.

        :rtype: :py:class:`Fact`
        :return: retrieved Fact or None if no matching fact exists

        :type fact_id: UUID
        :arg fact_id: id of persisted Fact

        """
        return fact_model.IncomingFact.select_by_id(fact_id)


    @classmethod
    def delete(cls, fact_id):
        """Delete persisted data corresponding to this Fact.
        """
        pass

    @classmethod
    def _normalize_sentence(cls, sentence):
        return sentence.lower()


        

    
