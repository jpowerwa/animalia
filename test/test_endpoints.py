#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from __future__ import unicode_literals

import unittest
import uuid

from flask.ext.api import status
import json
import mock

from animalia import app
from animalia.fact_manager import FactManager


class GetFactTests(unittest.TestCase):
    """Verify /fact/animal/<fact_id> endpoint.
    """
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True 

    def get_fact(self, fact_id=None):
        """Helper method to call get fact API with provided fact_id.
        """
        return self.app.get('/animal/fact/{0}'.format(fact_id))

    def post_fact(self, fact_sentence=None):
        """Helper method to call post fact API with provided fact sentence.
        """
        return self.app.post('/animal/fact', 
                             data=json.dumps({'fact': fact_sentence}),
                             content_type='application/json')

    @mock.patch.object(FactManager, 'get_fact_by_id')
    def test_get_fact(self, get_fact):
        """Verify success scenario.
        """
        # Set up mocks and test data
        get_fact.return_value = mock.Mock(name='fact', fact_text='abracadabra')
        fact_id = uuid.uuid4()

        # Make call
        response = self.get_fact(fact_id=fact_id)

        # Verify response status and data
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(json.dumps({'fact': 'abracadabra'}),
                         response.data)

        # Verify mocks
        get_fact.assert_called_once_with(fact_id)

    @mock.patch.object(FactManager, 'get_fact_by_id')
    def test_get_fact__no_fact_found(self, get_fact):
        """Verify fact not found scenario.
        """
        # Set up mocks and test data
        get_fact.return_value = None
        fact_id = uuid.uuid4()

        # Make call
        response = self.get_fact(fact_id=fact_id)
        
        # Verify response status and data
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_get_fact__invalid_fact_id(self):
        """Verify invalid fact_id scenario.
        """
        # Set up mocks and test data
        fact_id = 'not uuid'

        # Make call
        response = self.get_fact(fact_id=fact_id)
        
        # Verify response status and data
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(json.dumps({'message': 'Specified fact_id is not valid UUID'}),
                         response.data)

    @mock.patch.object(FactManager, 'fact_from_sentence')
    def test_post_fact(self, make_fact):
        """Verify success scenario.
        """
        # Set up mocks and test data
        fact_id = uuid.uuid4()
        make_fact.return_value = mock.Mock(name='fact', fact_id=fact_id)

        # Make call
        response = self.post_fact(fact_sentence='the otter lives in the river')

        # Verify response status and data
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(json.dumps({'id': str(fact_id)}),
                         response.data)

        # Verify mocks
        make_fact.assert_called_once_with('the otter lives in the river')

    def test_post_fact__no_post_data(self):
        """Verify 400 if no data is posted.
        """
        # Set up mocks and test data
        fact_id = uuid.uuid4()

        # Make call
        response = self.post_fact(fact_sentence='')

        # Verify response status and data
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(json.dumps({'message': 'Fact sentence is required'}),
                         response.data)

    @mock.patch.object(FactManager, 'fact_from_sentence')
    def test_post_fact__parse_error(self, make_fact):
        """Verify 400 response if sentence fails to parse.
        """
        # Set up mocks and test data
        fact_id = uuid.uuid4()
        make_fact.side_effect = FactManager.ParseError()

        # Make call
        response = self.post_fact(fact_sentence='unparseable fact')

        # Verify response status and data
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(json.dumps({'message': 'Failed to parse your fact'}),
                         response.data)















