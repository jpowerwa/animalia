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
#                concept_type = concept_type.save()
            # print("\nCONCEPT_TYPE: {0}, {1}".format(concept_type.concept_type_id,
            #                                         concept_type.concept_type_name))
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

