#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Application exceptions.
"""

from __future__ import unicode_literals

class ExternalApiError(Exception):
    """Error communicating with external API.
    """
    pass

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
        self.conflicting_fact_id = kwargs.pop('conflicting_fact_id', None)
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
