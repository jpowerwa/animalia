#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from __future__ import unicode_literals

import json

import flask

# Create Flask app
app = flask.Flask(__name__)

# Initialize db connection and orm
from animal_fact_model import db, Concept, ConceptType


@app.route("/")
def main():
    return flask.render_template('index.html')

@app.route('/show_signup')
def show_signup():
    return flask.render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    req_data = flask.request.json
    concept_name = req_data.get('username')
    response_data = {}
    if not concept_name:
        response_data = {'html':'<span>No concept name provided</span>'}
    else:
        try:
            concept = Concept(concept_name=concept_name)
            concept.concept_types.append(ConceptType(concept_type_name='fruit'))
            concept.save()
            response_data = {'message': 'Concept {0} added'.format(concept.concept_id)}
        except Exception as ex:
            response_data = {'error': str(ex)}
        return json.dumps(response_data)

