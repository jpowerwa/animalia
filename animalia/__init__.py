#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
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

ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter(fmt='%(asctime)s %(name)s [%(levelname)s] %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S'))
logging.root.addHandler(ch)
logger = logging.getLogger('animalia')
logger.setLevel(logging.DEBUG)


# Import after app has been created
from fact_manager import FactManager, IncomingFactError


@app.route("/")
def main():
    return flask.render_template('index.html')

@app.route('/animals', methods=['GET'])
def query_facts():
    response_data = None
    response_code = status.HTTP_200_OK
    question = flask.request.args.get('q')
    if not question:
        response_data = {'message': 'No question specified'}
        response_code = status.HTTP_400_BAD_REQUEST 
    else:
        answer = FactManager.query_facts(question)
        if answer:
            response_data = {'fact': answer}
        else:
            response_data = {'message': "I can't answer your question."}
            response_code = status.HTTP_404_NOT_FOUND
    return json.dumps(response_data), response_code

@app.route('/animals/facts/<fact_id>', methods=['DELETE'])
def delete_fact(fact_id):
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
        except IncomingFactError as ex:
            logger.exception(ex)
            response_data = {'message': 'Failed to parse your fact',
                             'details': '{0}'.format(ex)}
            response_code = status.HTTP_400_BAD_REQUEST
    return json.dumps(response_data), response_code

