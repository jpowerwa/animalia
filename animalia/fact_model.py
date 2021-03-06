#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from __future__ import unicode_literals

import datetime
import uuid

from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
import sqlalchemy.ext.associationproxy as sa_assoc_proxy
import sqlalchemy.orm as sa_orm
import sqlalchemy.types as sa_types

from animalia import app
from config import Config

__all__ = ('Concept',
           'IncomingFact',
           'Relationship',
           'RelationshipType',
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
        if value:
            value = uuid.UUID(hex=value)
        return value

    @staticmethod
    def new_uuid():
        return str(uuid.uuid4())


class Concept(db.Model):
    __tablename__ = 'concepts'
    concept_id = sa.Column(UUIDType(), primary_key=True, default=UUIDType.new_uuid)
    concept_name = sa.Column(sa.String(255), nullable=False, unique=True)

    @classmethod
    def select_by_name(cls, name):
        return db.session.query(cls).filter_by(concept_name=name).first()


class RelationshipType(db.Model):
    __tablename__ = 'relationship_types'
    relationship_type_name = sa.Column(sa.String(45), primary_key=True)
    relationship_type_id = sa.Column(UUIDType(), default=UUIDType.new_uuid, nullable=False)

    @classmethod
    def select_by_name(cls, name):
        return db.session.query(cls).filter_by(relationship_type_name=name).first()


class Relationship(db.Model):
    __tablename__ = 'relationships'
    __table_args__ = (
        sa.ForeignKeyConstraint(['relationship_type_id'], 
                                [RelationshipType.relationship_type_id]),
        sa.ForeignKeyConstraint(['subject_id'], [Concept.concept_id]),
        sa.ForeignKeyConstraint(['object_id'], [Concept.concept_id])
        )
    relationship_id = sa.Column(UUIDType(), primary_key=True, default=UUIDType.new_uuid)
    relationship_type_id = sa.Column(UUIDType(), nullable=False)
    subject_id = sa.Column(UUIDType(), nullable=False)
    object_id = sa.Column(UUIDType(), nullable=False)
    count = sa.Column(sa.Integer, default=None)
    fact_id = sa.Column(UUIDType(), nullable=True)

    @classmethod
    def select_by_fact_id(cls, fact_id):
        """Select Relationships associated with specified fact_id.

        :rtype: [py:class:`~fact_model.Relationship`]
        :return: list of matching relationship; empty list if no matches are found

        :type fact_id: uuid
        arg fact_id: fact_id identifying relationships to be selected
        
        """
        return db.session.query(cls).filter_by(fact_id=fact_id).all()

    @classmethod
    def select_by_foreign_keys(cls, subject_id=None, object_id=None, relationship_type_id=None):
        """Select Relationship with specified subject, object and relationship type.

        :rtype: py:class:`~fact_model.Relationship`
        :return: matching relationship; None if not found

        :type subject_id: uuid
        :type object_id: uuid
        :type relationship_type_id: uuid

        """
        filter_clause = sa.and_(
            sa.and_(cls.subject_id == subject_id, cls.object_id == object_id),
            cls.relationship_type_id == relationship_type_id)
        return db.session.query(cls).filter(filter_clause).first()

    @classmethod
    def select_by_values(cls, relationship_type_name=None, relationship_number=None,
                         subject_name=None, object_name=None):
        """Select Relationships with specified relationship_type, count, subject, and object.

        :rtype: [py:class:`~fact_model.Relationship`]
        :return: matching relationships; empty list if none are found

        :type relationship_type_name: unicode
        :arg relationship_type_name: name of relationship_type

        :type relationship_number: int
        :arg relationship_number: optional value of relationship 'count' attribute

        :type subject_name: unicode
        :arg subject_name: optional name of subject concept

        :type object_name: unicode
        :arg object_name: optional name of object concept

        """
        query = db.session.query(cls).\
            join(RelationshipType).\
            filter(RelationshipType.relationship_type_name==relationship_type_name)
        if relationship_number:
            query = query.filter(Relationship.count==relationship_number)
        if subject_name: 
            subject_concept = sa_orm.aliased(Concept)
            query = query.\
                join(subject_concept, Relationship.subject_id==subject_concept.concept_id).\
                filter(subject_concept.concept_name==subject_name)
        if object_name:
            object_concept = sa_orm.aliased(Concept)
            query = query.\
                join(object_concept, Relationship.object_id==object_concept.concept_id).\
                filter(object_concept.concept_name==object_name)
        return query.all()

Relationship.subject = sa_orm.relationship(
    Concept, primaryjoin=Concept.concept_id==Relationship.subject_id, lazy=False)
Relationship.object = sa_orm.relationship(
    Concept, primaryjoin=Concept.concept_id==Relationship.object_id, lazy=False)
Relationship.relationship_types = sa_orm.relationship(RelationshipType, uselist=True, lazy=False) 
Relationship.relationship_type_names = sa_assoc_proxy.association_proxy(
    'relationship_types', 'relationship_type_name')

Concept.concept_type_relationships = sa_orm.relationship(
    Relationship, 
    primaryjoin=(
        sa.and_(Relationship.subject_id==Concept.concept_id,
                sa.and_(Relationship.relationship_type_id==RelationshipType.relationship_type_id,
                        RelationshipType.relationship_type_name=='is'))),
    uselist=True, 
    lazy=True)
Concept.concept_types = sa_assoc_proxy.association_proxy(
    'concept_type_relationships', 'object.concept_name')

class IncomingFact(db.Model):
    __tablename__ = 'incoming_facts'
    fact_id = sa.Column(UUIDType(), primary_key=True, default=UUIDType.new_uuid)
    fact_text = sa.Column(sa.String(255), nullable=False, unique=True)
    parsed_fact = sa.Column(sa.Text, nullable=False)
    deleted = sa.Column(sa.Boolean, default=False)
    creation_date_utc = sa.Column(sa.TIMESTAMP, default=datetime.datetime.utcnow)

    @classmethod
    def select_by_id(cls, fact_id):
        return db.session.query(cls).get(fact_id)

    @classmethod
    def select_by_text(cls, text):
        return db.session.query(cls).filter_by(fact_text=text).first()
