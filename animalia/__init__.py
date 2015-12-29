#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from __future__ import unicode_literals

import json
import uuid

import flask
from flask.ext.api import status

# Create Flask app
app = flask.Flask(__name__)

# Import after app has been created
from fact_manager import FactManager


@app.route("/")
def main():
    return flask.render_template('index.html')

@app.route('/animal/fact', methods=['POST'])
def post_fact():
    req_data = flask.request.json
    fact_sentence = req_data.get('fact')
    response_data = {}
    if not fact_sentence:
        response_data = {'html':'<span>Fact sentence is required</span>'}
    else:
        fact = FactManager.fact_from_sentence(fact_sentence)
        response_data = {'id': str(fact.fact_id)}
    return json.dumps(response_data)

@app.route('/animal/fact/<fact_id>', methods=['GET'])
def get_fact(fact_id):
    fact = FactManager.get_fact_by_id(fact_id)
    if not fact:
        return '', status.HTTP_404_NOT_FOUND
    return json.dumps({'fact': fact.fact_text})
    
