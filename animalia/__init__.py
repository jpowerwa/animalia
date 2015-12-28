#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from __future__ import unicode_literals

import json
import uuid

import flask

# Create Flask app
app = flask.Flask(__name__)

# Initialize db connection and orm
from fact_model import db, Concept, ConceptType
from fact import Fact


@app.route("/")
def main():
    return flask.render_template('index.html')

@app.route('/show_signup')
def show_signup():
    return flask.render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    req_data = flask.request.json
    subj_concept = req_data.get('username')
    obj_concept = req_data.get('email')
    response_data = {}
    if not (subj_concept and obj_concept):
        response_data = {'html':'<span>Subject and object are required</span>'}
    else:
        try:
            concept_type = ConceptType.select_by_name(obj_concept)
            if not concept_type:
                concept_type = ConceptType(concept_type_name=obj_concept)
            concept = Concept.select_by_name(subj_concept)
            if not concept:
                concept = Concept(concept_name=subj_concept)
            concept.concept_types.append(concept_type)
            concept.save()
            response_data = {'message': 'Concept {0} added as type {1}'.format(
                    concept.concept_name, concept_type.concept_type_name)}
        except Exception as ex:
            response_data = {'error': str(ex)}
        return json.dumps(response_data)

@app.route('/animal/fact', methods=['POST'])
def post_fact():
    req_data = flask.request.json
    fact_sentence = req_data.get('fact')
    response_data = {}
    if not fact_sentence:
        response_data = {'html':'<span>Fact sentence is required</span>'}
    else:
        fact = Fact.from_sentence(fact_sentence)
        response_data = {'id': str(fact.fact_id)}
    return json.dumps(response_data)

