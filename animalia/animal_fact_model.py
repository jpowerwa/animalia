#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from __future__ import unicode_literals

import uuid

from flask_sqlalchemy import SQLAlchemy

# local 
from animalia import app
from config import Config

__all__ = ('Concept',
           'ConceptType'
           )

app.config['SQLALCHEMY_DATABASE_URI'] = Config.db_connection
db = SQLAlchemy(app)

class AnimalFactModel(object):
    def ensure_id(self, id_val):
        return id_val or str(uuid.uuid4())

    def save(self):
        db.session.add(self)
        db.session.commit()


concept_to_concept_types = db.Table(
    'concept_to_concept_type',
    db.Column('concept_id', db.String(36), db.ForeignKey('concepts.concept_id')),
    db.Column('concept_type_id', db.String(36), db.ForeignKey('concept_types.concept_type_id')))

class Concept(db.Model, AnimalFactModel):
    __tablename__ = 'concepts'
    concept_id = db.Column(db.String(36), primary_key=True)
    concept_name = db.Column(db.String(255), unique=True)
    concept_types = db.relationship('ConceptType', 
                                    secondary=concept_to_concept_types,
                                    backref=db.backref('concepts', lazy='dynamic'))

    def __init__(self, concept_id=None, **kwargs):
        self.concept_id = self.ensure_id(concept_id)
        super(Concept, self).__init__(**kwargs)

    @classmethod
    def select_by_name(cls, name):
        return db.session.query(ConceptType).filter_by(concept_name=name).first()


class ConceptType(db.Model, AnimalFactModel):
    __tablename__ = 'concept_types'
    concept_type_id = db.Column(db.String(36), primary_key=True)
    concept_type_name = db.Column(db.String(255), unique=True)

    def __init__(self, concept_type_id=None, **kwargs):
        self.concept_type_id = self.ensure_id(concept_type_id)
        super(ConceptType, self).__init__(**kwargs)

    @classmethod
    def select_by_name(cls, name):
        return db.session.query(ConceptType).filter_by(concept_type_name=name).first()


