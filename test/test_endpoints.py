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
from animalia.fact_manager import FactManager, IncomingFactError


class FactManagerTests(unittest.TestCase):
    """Verify /animals/facts endpoints.
    """
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True 

    def query_facts(self, question):
        """Helper method to call ask question API with provided question.
        """
        return self.app.get('/animals?q={0}'.format(question))

    def delete_fact(self, fact_id):
        """Helper method to call delete fact API with provided fact_id.
        """
        return self.app.delete('/animals/facts/{0}'.format(fact_id))

    def get_fact(self, fact_id):
        """Helper method to call get fact API with provided fact_id.
        """
        return self.app.get('/animals/facts/{0}'.format(fact_id))

    def post_fact(self, fact_sentence):
        """Helper method to call post fact API with provided fact sentence.
        """
        return self.app.post('/animals/facts', 
                             data=json.dumps({'fact': fact_sentence}),
                             content_type='application/json')

    @mock.patch.object(FactManager, 'delete_fact_by_id')
    def test_delete_fact(self, delete_fact):
        """Verify success scenario.
        """
        # Set up mocks and test data
        delete_fact.return_value = fact_id = uuid.uuid4()

        # Make call
        response = self.delete_fact(fact_id)

        # Verify response status and data
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(json.dumps({'id': str(fact_id)}),
                         response.data)

        # Verify mocks
        delete_fact.assert_called_once_with(fact_id)

    @mock.patch.object(FactManager, 'delete_fact_by_id')
    def test_delete_fact__no_fact_found(self, delete_fact):
        """Verify fact not found scenario.
        """
        # Set up mocks and test data
        delete_fact.return_value = None

        # Make call
        response = self.delete_fact(uuid.uuid4())
        
        # Verify response status and data
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_delete_fact__invalid_fact_id(self):
        """Verify invalid fact_id scenario.
        """
        # Set up mocks and test data
        fact_id = 'not uuid'

        # Make call
        response = self.delete_fact(fact_id)
        
        # Verify response status and data
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(json.dumps({'message': 'Specified fact_id is not valid UUID'}),
                         response.data)

    @mock.patch.object(FactManager, 'get_fact_by_id')
    def test_get_fact(self, get_fact):
        """Verify success scenario.
        """
        # Set up mocks and test data
        get_fact.return_value = mock.Mock(name='fact', fact_text='abracadabra')
        fact_id = uuid.uuid4()

        # Make call
        response = self.get_fact(fact_id)

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
        response = self.get_fact(fact_id)
        
        # Verify response status and data
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_get_fact__invalid_fact_id(self):
        """Verify invalid fact_id scenario.
        """
        # Set up mocks and test data
        fact_id = 'not uuid'

        # Make call
        response = self.get_fact(fact_id)
        
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
        response = self.post_fact('')

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
        make_fact.side_effect = IncomingFactError('boo hoo')

        # Make call
        response = self.post_fact('unparseable fact')

        # Verify response status and data
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(json.dumps({'message': 'Failed to parse your fact',
                                     'details': 'boo hoo'}),
                         response.data)

    @mock.patch.object(FactManager, 'query_facts')
    def test_query_facts(self, query_facts):
        """Verify success scenario.
        """
        # Set up mocks and test data
        question = "who's your best friend"
        answer = "not barney"
        query_facts.return_value = answer

        # Make call
        response = self.query_facts(question)

        # Verify response status and data
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(json.dumps({'fact': answer}),
                         response.data)

        # Verify mocks
        query_facts.assert_called_once_with(question)

    @mock.patch.object(FactManager, 'query_facts')
    def test_query_facts__no_answer(self, query_facts):
        """Verify unknown answer scenario.
        """
        # Set up mocks and test data
        question = "who's your best friend"
        query_facts.return_value = None

        # Make call
        response = self.query_facts(question)
        
        # Verify response status and data
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertEqual(json.dumps({'message': "I can't answer your question."}),
                         response.data)

    def test_query_facts__invalid_question(self):
        """Verify invalid fact_question scenario.
        """
        # Make call
        response = self.query_facts('')
        
        # Verify response status and data
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(json.dumps({'message': 'No question specified'}),
                         response.data)














