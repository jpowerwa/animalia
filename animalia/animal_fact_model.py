#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from __future__ import unicode_literals

import uuid

import flask.ext.mysql

# local 
from animalia import app
from config import Config


class AnimalFactModel(object):

    db = None
    
    @classmethod
    def init(cls):
        cls.db = flask.ext.mysql.MySQL()
        app.config['MYSQL_DATABASE_USER'] = Config.db_user
        app.config['MYSQL_DATABASE_PASSWORD'] = Config.db_password
        app.config['MYSQL_DATABASE_DB'] = Config.db_name
        app.config['MYSQL_DATABASE_HOST'] = Config.db_host
        cls.db.init_app(app)
        
    @classmethod
    def get_connection(cls):
        return cls.db.connect()

    @classmethod
    def add_concept(cls, concept_name):
        conn = cls.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "insert into concepts (concept_id, concept_name) values ('{0}', '{1}')".format(
                str(uuid.uuid4()), concept_name))
        conn.commit()



# def name_for_scalar_relationship(base, local_cls, referred_cls, constraint):
#     name = referred_cls.__name__.lower()
#     local_table = local_cls.__table__
#     if name in local_table.columns:
#         newname = name + "_"
#         return newname
#     return name

# def name_for_collection_relationship(base, local_cls, referred_cls, constraint):
#     name = referred_cls.__name__.lower() + '_collection'
#     for c in referred_cls.__table__.columns:
#         if c == name:
#             name += "_"
#     return name

# with app.app_context():
#     engine = create_engine(app.config['MAIN_DATABASE_URI'])
#     metadata = MetaData(engine)
#     session = Session(engine)
#     metadata.reflect(bind=engine, only=app.config['MAIN_DATABASE_MODEL_MAP'].keys())
#     Model = declarative_base(metadata=metadata, cls=(db.Model,), bind=engine)
#     Base = automap_base(metadata=metadata, declarative_base=Model)
#     Base.prepare(
#         name_for_scalar_relationship=name_for_scalar_relationship,
#         name_for_collection_relationship=name_for_collection_relationship
#         )

#     for cls in Base.classes:
#         cls.__table__.info = {'bind_key': 'main'}
#         if cls.__table__.name in app.config['MAIN_DATABASE_MODEL_MAP']:
#             globals()[app.config['MAIN_DATABASE_MODEL_MAP'][cls.__table__.name]] = cls
