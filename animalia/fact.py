#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from __future__ import unicode_literals

import fact_model

class Fact(object):

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
    def from_sentence(cls, sentence):
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
    def _normalize_sentence(cls, sentence):
        return sentence.lower()

    @classmethod
    def get_by_id(cls, fact_id):
        """Retrieve specified Fact by id.

        :rtype: :py:class:`Fact`
        :return: retrieved Fact or None if no matching fact exists

        :type fact_id: UUID
        :arg fact_id: id of persisted Fact

        """
        return None

    @classmethod
    def get_by_sentence(cls, sentence):
        """Retrieve specified Fact by sentence

        :rtype: :py:class:`Fact`
        :return: retrieved Fact or None if no matching fact exists

        :type sentence: unicode
        :arg sentence: sentence of persisted Fact

        """
        return None


    # instance methods

    def delete(self):
        """Delete persisted data corresponding to this Fact.
        """
        pass

    def save(self):
        """Save member data as persisted Fact.

        :rtype: Fact
        :return: new instance of Fact that corresponds to persisted data

        """
        pass
        
        

    
