#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Flask animalia application.

Implements API described in README.md.

"""

from __future__ import unicode_literals

import logging
import json
import uuid

import flask
from flask.ext.api import status

# Create Flask app
app = flask.Flask(__name__)

# Init logging
import logging

app.logger.setLevel(logging.INFO)
logger = app.logger

# Import after app has been created
from fact_manager import FactManager
from exc import IncomingDataError

@app.route("/")
def main():
    return flask.render_template('index.html')

@app.route('/animals/facts/<fact_id>', methods=['DELETE'])
def delete_fact(fact_id):
    """Delete fact with specified id.

    Success response: 200 OK
    Response body: {'id': <UUID>}

    If no such fact exists, response is 404 Not Found.

    When a fact is deleted then the information it represents about animals is no longer 
    available to the service and the service must stop answering questions with information 
    from the fact.
    
    """
    response_data = None
    response_code = status.HTTP_200_OK
    try:
        fact_id = uuid.UUID(hex=fact_id)
    except ValueError:
        response_data = {'message': 'Specified fact_id is not valid UUID'}
        response_code = status.HTTP_400_BAD_REQUEST 
        fact_id = None
    if fact_id:
        deleted_fact_id = FactManager.delete_fact_by_id(fact_id)
        if not deleted_fact_id:
            response_data = ''
            response_code = status.HTTP_404_NOT_FOUND
        else:
            response_data = {'id': str(deleted_fact_id)}
    return json.dumps(response_data), response_code

@app.route('/animals/facts/<fact_id>', methods=['GET'])
def get_fact(fact_id):
    """Retrieve fact with specified id.

    Success response: 200 OK
    Response body: {'fact': <sentence>}
    
    If no such fact exists, response is 404 Not Found.

    """
    response_data = None
    response_code = status.HTTP_200_OK
    try:
        fact_id = uuid.UUID(hex=fact_id)
    except ValueError:
        response_data = {'message': 'Specified fact_id is not valid UUID'}
        response_code = status.HTTP_400_BAD_REQUEST 
        fact_id = None
    if fact_id:
        fact = FactManager.get_fact_by_id(fact_id)
        if not fact:
            response_data = ''
            response_code = status.HTTP_404_NOT_FOUND
        else:
            response_data = {'fact': fact.fact_text}
    return json.dumps(response_data), response_code
    
@app.route('/animals/facts', methods=['POST'])
def post_fact():
    """Add fact represented by sentence.
    
    Request body: {'fact': <sentence>}
    Sentence should be phrased like 'otters live in rivers'

    Success response: 200 OK
    Response body: {'id': <UUID>}

    Error response: 400 Bad Request
    Response body: {'message': <error message>}

    Submitting an already existing fact returns the identifier of the original fact.

    """
    response_data = None
    response_code = status.HTTP_200_OK
    req_data = flask.request.json
    fact_sentence = req_data.get('fact')
    if not fact_sentence:
        response_data = {'message': 'Fact sentence is required'}
        response_code = status.HTTP_400_BAD_REQUEST
    else:
        try:
            fact = FactManager.fact_from_sentence(fact_sentence)
            response_data = {'id': str(fact.fact_id)}
        except IncomingDataError as ex:
            logger.exception(ex)
            response_data = {'message': 'Failed to parse your fact',
                             'details': '{0}'.format(ex)}
            response_code = status.HTTP_400_BAD_REQUEST
    return json.dumps(response_data), response_code

@app.route('/animals', methods=['GET'])
def query_facts():
    """Respond to question about semantic relationships of animals.

    A query is submitted as a sentence in specific form that follows one of the following patterns:
      "Where do otters live?"
      "How many legs does the otter have"?
      "Which animals have 4 legs?"
      "How many animals are mammals?"

    Query sentence is specified as query string arg named 'q'.

    Success response: 200 OK
    Response body: {'fact': <answer>}

    If no response is found, response is 404 Not Found.
    Response body: {'message': <error>}
    { "message": "I can't answer your question." }

    If request is malformed, response is 400 Bad Request.

    """
    response_data = None
    response_code = status.HTTP_200_OK
    question = flask.request.args.get('q')
    if not question:
        response_data = {'message': 'No question specified'}
        response_code = status.HTTP_400_BAD_REQUEST 
    else:
        try:
            answer = FactManager.query_facts(question)
            if answer:
                response_data = {'fact': answer}
            else:
                response_data = {'message': "I can't answer your question."}
                response_code = status.HTTP_404_NOT_FOUND
        except IncomingDataError as ex:
            logger.exception(ex)
            response_data = {'message': 'Failed to parse your question',
                             'details': '{0}'.format(ex)}
            response_code = status.HTTP_400_BAD_REQUEST
    return json.dumps(response_data), response_code

