#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from __future__ import unicode_literals

import uuid

from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
import sqlalchemy.types as sa_types

from animalia import app
from config import Config

__all__ = ('Concept',
           'IncomingFact',
#           'Relationship'
           )

app.config['SQLALCHEMY_DATABASE_URI'] = Config.db_connection
db = SQLAlchemy(app)

class UUIDType(sa_types.TypeDecorator):
    """
    http://docs.sqlalchemy.org/en/latest/core/custom_types.html#backend-agnostic-guid-type
    """
    impl = sa_types.CHAR

    def process_bind_param(self, value, dialect):
        if value:
            value = str(value)
        return value

    def process_result_value(self, value, dialect):
        return uuid.UUID(hex=value)

    @staticmethod
    def new_uuid():
        return str(uuid.uuid4())


class FactModel():
    def save(self):
        saved = db.session.merge(self)
        db.session.commit()
        return saved


concept_to_concept_types = db.Table(
    'concept_to_concept_type',
    sa.Column('concept_id', sa.String(36), sa.ForeignKey('concepts.concept_id')),
    sa.Column('concept_type_id', sa.String(36), sa.ForeignKey('concept_types.concept_type_id')))

class Concept(db.Model, FactModel):
    __tablename__ = 'concepts'
    concept_id = sa.Column(UUIDType(), primary_key=True, default=UUIDType.new_uuid)
    concept_name = sa.Column(sa.String(255), unique=True)
    concept_types = sa_orm.relationship('ConceptType', 
                                        secondary=concept_to_concept_types,
                                        backref=sa_orm.backref('concepts', lazy='dynamic'))


    @classmethod
    def select_by_name(cls, name):
        return db.session.query(cls).filter_by(concept_name=name).first()


class ConceptType(db.Model):
    __tablename__ = 'concept_types'
    concept_type_id = sa.Column(UUIDType(), primary_key=True, default=UUIDType.new_uuid)
    concept_type_name = sa.Column(sa.String(255), unique=True)

    @classmethod
    def select_by_name(cls, name):
        return db.session.query(cls).filter_by(concept_type_name=name).first()


class RelationshipType(db.Model):
    __tablename__ = 'relationship_types'
    relationship_type_id = sa.Column(UUIDType(), primary_key=True, default=UUIDType.new_uuid)
    # subject_type_id = sa.Column(UUIDType())
    # object_type_id = sa.Column(UUIDType())

class RelationshipTypeName(db.Model):
    __tablename__ = 'relationship_type_names'
    __table_args__ = (
        sa.ForeignKeyConstraint(['relationship_type_id'], [RelationshipType.relationship_type_id]),
        )
    relationship_type_name = sa.Column(sa.String(45), primary_key=True)
    relationship_type_id = sa.Column(UUIDType())

RelationshipType.names = sa_orm.relationship(RelationshipTypeName, 
                                         backref='RelationshipType', 
                                         lazy='dynamic')

class Relationship(db.Model):
    __tablename__ = 'relationships'
    __table_args__ = (
        sa.ForeignKeyConstraint(['relationship_type_id'], [RelationshipType.relationship_type_id]),
        sa.ForeignKeyConstraint(['subject_id'], [Concept.concept_id]),
        sa.ForeignKeyConstraint(['object_id'], [Concept.concept_id])
        )
    relationship_id = sa.Column(UUIDType(), primary_key=True, default=UUIDType.new_uuid)
    relationship_type_id = sa.Column(UUIDType())
    subject_id = sa.Column(UUIDType())
    object_id = sa.Column(UUIDType())
    count = sa.Column(sa.Integer, default=None)
    fact_id = sa.Column(UUIDType())

Relationship.relationship_type = sa_orm.relationship(RelationshipType,
#                                                 backref='Relationship',
                                                 lazy=False)

class IncomingFact(db.Model, FactModel):
    __tablename__ = 'incoming_facts'
    fact_id = sa.Column(UUIDType(), primary_key=True, default=UUIDType.new_uuid)
    fact_text = sa.Column(sa.String(255), unique=True)
    deleted = sa.Column(sa.Boolean, default=False)

    @classmethod
    def select_by_id(cls, fact_id):
        return db.session.query(cls).get(fact_id)

    @classmethod
    def select_by_text(cls, text):
        return db.session.query(cls).filter_by(fact_text=text).first()
