#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from __future__ import unicode_literals

import datetime
import unittest
import uuid

from animalia.fact_model import db, Concept, IncomingFact, Relationship, RelationshipType


class FactModelTestCase(unittest.TestCase):
    def tearDown(self):
        # Rollback transaction
        db.session.rollback()

    def reset_session(self):
        # Flush session and then clear it
        db.session.flush()
        db.session.expunge_all()


class ConceptTests(FactModelTestCase):
    """Verify Concept ORM.
    """
    def test_concept(self):
        """Verify creation with concept_name and concept_id.
        """
        concept_name = 'flower_{0}'.format(uuid.uuid4())
        concept_id = uuid.uuid4()
        concept = Concept(concept_name=concept_name, concept_id=concept_id)
        db.session.add(concept)
        self.reset_session()

        retrieved_concept = db.session.query(Concept).filter_by(concept_id=concept_id).first()
        self.assertIsNotNone(retrieved_concept, "Expected to find persisted Concept")
        self.assertEqual(concept_name, retrieved_concept.concept_name)
        self.assertEqual(concept_id, retrieved_concept.concept_id)

    def test_concept__default_id(self):
        """Verify that concept_id is assigned when Concept is persisted.
        """
        concept_name = 'flower_{0}'.format(uuid.uuid4())
        concept = Concept(concept_name=concept_name)
        db.session.add(concept)
        self.reset_session()

        retrieved_concept = db.session.query(Concept).filter_by(concept_name=concept_name).first()
        self.assertIsNotNone(retrieved_concept, "Expected to find persisted Concept")
        self.assertEqual(concept_name, retrieved_concept.concept_name)
        self.assertTrue(isinstance(retrieved_concept.concept_id, uuid.UUID))

    def test_select_by_name(self):
        """Verify select_by_name method.
        """
        concept_name = 'flower_{0}'.format(uuid.uuid4())
        concept = Concept(concept_name=concept_name)
        db.session.add(concept)
        self.reset_session()

        retrieved_concept = Concept.select_by_name(concept_name)
        self.assertIsNotNone(retrieved_concept, "Expected to find persisted Concept")
        self.assertEqual(concept_name, retrieved_concept.concept_name)

    def test_select_by_name__no_match(self):
        """Verify None return value if no match on concept_name.
        """
        concept_name = 'flower_{0}'.format(uuid.uuid4())
        concept = Concept(concept_name=concept_name)
        db.session.add(concept)
        self.reset_session()

        retrieved_concept = Concept.select_by_name('flower_123')
        self.assertIsNone(retrieved_concept, "Expected to find no persisted Concept")


class RelationshipTypeTests(FactModelTestCase):
    """Verify RelationshipType ORM.
    """
    def test_relationship_type(self):
        """Verify creation with relationship_type_name and relationship_type_id.
        """
        rel_type_name = 'eats_{0}'.format(uuid.uuid4())
        rel_type_id = uuid.uuid4()
        rel_type = RelationshipType(relationship_type_name=rel_type_name, 
                                             relationship_type_id=rel_type_id)
        db.session.add(rel_type)
        self.reset_session()

        retrieved_rel_type = db.session.query(RelationshipType).filter_by(
            relationship_type_id=rel_type_id).first()
        self.assertIsNotNone(retrieved_rel_type, "Expected to find persisted RelationshipType")
        self.assertEqual(rel_type_name, retrieved_rel_type.relationship_type_name)
        self.assertEqual(rel_type_id, retrieved_rel_type.relationship_type_id)

    def test_relationship_type__default_id(self):
        """Verify that relationship_type_id is assigned when RelationshipType is persisted.
        """
        rel_type_name = 'eats_{0}'.format(uuid.uuid4())
        rel_type = RelationshipType(relationship_type_name=rel_type_name)
        db.session.add(rel_type)
        self.reset_session()

        retrieved_rel_type = db.session.query(RelationshipType).filter_by(
            relationship_type_name=rel_type_name).first()
        self.assertIsNotNone(retrieved_rel_type, "Expected to find persisted RelationshipType")
        self.assertEqual(rel_type_name, retrieved_rel_type.relationship_type_name)
        self.assertTrue(isinstance(retrieved_rel_type.relationship_type_id, uuid.UUID))

    def test_select_by_name(self):
        """Verify select_by_name method.
        """
        rel_type_name = 'eats_{0}'.format(uuid.uuid4())
        rel_type = RelationshipType(relationship_type_name=rel_type_name)
        db.session.add(rel_type)
        self.reset_session()

        retrieved_rel_type = RelationshipType.select_by_name(rel_type_name)
        self.assertIsNotNone(retrieved_rel_type, "Expected to find persisted RelationshipType")
        self.assertEqual(rel_type_name, retrieved_rel_type.relationship_type_name)

    def test_select_by_name__no_match(self):
        """Verify None return value if no match on relationship_type_name.
        """
        rel_type_name = 'eats_{0}'.format(uuid.uuid4())
        rel_type = RelationshipType(relationship_type_name=rel_type_name)
        db.session.add(rel_type)
        self.reset_session()

        retrieved_rel_type = RelationshipType.select_by_name('eats_123')
        self.assertIsNone(retrieved_rel_type, "Expected to find no persisted RelationshipType")


class RelationshipTests(FactModelTestCase):
    """Verify Relationship ORM.
    """
    def _get_concept(self, base_name):
        """Return Concept with concept_name=base_name_<uuid> and arbitrary concept_id.
        """
        return Concept(concept_name='{0}_{1}'.format(base_name, uuid.uuid4()),
                       concept_id=uuid.uuid4())
        
    def test_relationship(self):
        """Verify creation with all non-nullable data.
        """
        rel_id = uuid.uuid4()
        rel_type_id = uuid.uuid4()
        subject_id = uuid.uuid4()
        object_id = uuid.uuid4()
        relationship = Relationship(relationship_id=rel_id,
                                    relationship_type_id=rel_type_id,
                                    subject_id=subject_id,
                                    object_id=object_id)
        db.session.add(relationship)
        self.reset_session()

        retrieved_rel = db.session.query(Relationship).filter_by(relationship_id=rel_id).first()

        self.assertIsNotNone(retrieved_rel, "Expected to find persisted Relationship")
        self.assertEqual(rel_type_id, retrieved_rel.relationship_type_id)
        self.assertEqual(subject_id, retrieved_rel.subject_id)
        self.assertEqual(object_id, retrieved_rel.object_id)
        self.assertIsNone(retrieved_rel.count)
        self.assertIsNone(retrieved_rel.fact_id)

    def test_relationship__all_attributes(self):
        """Verify creation with all data.
        """
        rel_id = uuid.uuid4()
        count = 10
        fact_id = uuid.uuid4()
        relationship = Relationship(relationship_id=rel_id,
                                    relationship_type_id=uuid.uuid4(),
                                    subject_id=uuid.uuid4(),
                                    object_id=uuid.uuid4(),
                                    count=count,
                                    fact_id=fact_id)
        db.session.add(relationship)
        self.reset_session()

        retrieved_rel = db.session.query(Relationship).filter_by(relationship_id=rel_id).first()

        self.assertIsNotNone(retrieved_rel, "Expected to find persisted Relationship")
        self.assertEqual(count, retrieved_rel.count)
        self.assertEqual(fact_id, retrieved_rel.fact_id)

    def test_relationship_type__default_id(self):
        """Verify that relationship_id is assigned when Relationship is persisted.
        """
        rel_type_id = uuid.uuid4()
        subject_id = uuid.uuid4()
        object_id = uuid.uuid4()
        relationship = Relationship(relationship_type_id=rel_type_id,
                                    subject_id=subject_id,
                                    object_id=object_id)
        db.session.add(relationship)
        self.reset_session()

        retrieved_rel = db.session.query(Relationship).filter_by(
            relationship_type_id=rel_type_id).first()

        self.assertIsNotNone(retrieved_rel, "Expected to find persisted Relationship")
        self.assertEqual(rel_type_id, retrieved_rel.relationship_type_id)
        self.assertEqual(subject_id, retrieved_rel.subject_id)
        self.assertEqual(object_id, retrieved_rel.object_id)
        self.assertTrue(isinstance(retrieved_rel.relationship_id, uuid.UUID))

    def test_relationship__select_by_foreign_keys(self):
        """Verify select_by_foreign_keys method finds expected Relationship.
        """
        rel_type_id = uuid.uuid4()
        subject_id = uuid.uuid4()
        object_id = uuid.uuid4()

        fk_sets = [(rel_type_id, subject_id, object_id),
                   (uuid.uuid4(), subject_id, object_id),
                   (rel_type_id, uuid.uuid4(), object_id),
                   (rel_type_id, subject_id, uuid.uuid4())]

        for (rt_id, s_id, o_id) in fk_sets:
            db.session.add(Relationship(relationship_type_id=rt_id,
                                        subject_id=s_id,
                                        object_id=o_id))
        self.reset_session()

        all_rels = db.session.query(Relationship).all()
        self.assertEqual(4, len(all_rels))

        retrieved_rel = Relationship.select_by_foreign_keys(subject_id=subject_id, 
                                                            object_id=object_id,
                                                            relationship_type_id=rel_type_id)
        self.assertIsNotNone(retrieved_rel, "Expected to find persisted Relationship")
        self.assertEqual(rel_type_id, retrieved_rel.relationship_type_id)
        self.assertEqual(subject_id, retrieved_rel.subject_id)
        self.assertEqual(object_id, retrieved_rel.object_id)

    def test_relationship__subject_relation(self):
        """Verify subject relation on Relationship.
        """
        rel_id = uuid.uuid4()
        subject_concept = self._get_concept('flat')
        relationship = Relationship(relationship_id=rel_id,
                                    subject=subject_concept,
                                    object_id=uuid.uuid4(),
                                    relationship_type_id=uuid.uuid4())
        db.session.add(relationship)
        self.reset_session()

        # Verify Relationship was persisted
        retrieved_rel = db.session.query(Relationship).filter_by(relationship_id=rel_id).first()
        self.assertIsNotNone(retrieved_rel, "Expected to find persisted Relationship")
        self.assertEqual(subject_concept.concept_id, retrieved_rel.subject_id)
        self.assertEqual(subject_concept.concept_id, retrieved_rel.subject.concept_id)
        self.assertEqual(subject_concept.concept_name, retrieved_rel.subject.concept_name)
        self.reset_session()

        # Verify Concept was persisted as well
        retrieved_concept = db.session.query(Concept).filter_by(
            concept_id=subject_concept.concept_id).first()
        self.assertIsNotNone(retrieved_concept, "Expected to find persisted Concept")

    def test_relationship__object_relation(self):
        """Verify object relation on Relationship.
        """
        rel_id = uuid.uuid4()
        object_concept = self._get_concept('flat')
        relationship = Relationship(relationship_id=rel_id,
                                    subject_id=uuid.uuid4(),
                                    object=object_concept,
                                    relationship_type_id=uuid.uuid4())
        db.session.add(relationship)
        self.reset_session()

        # Verify Relationship was persisted
        retrieved_rel = db.session.query(Relationship).filter_by(relationship_id=rel_id).first()
        self.assertIsNotNone(retrieved_rel, "Expected to find persisted Relationship")
        self.assertEqual(object_concept.concept_id, retrieved_rel.object_id)
        self.assertEqual(object_concept.concept_id, retrieved_rel.object.concept_id)
        self.assertEqual(object_concept.concept_name, retrieved_rel.object.concept_name)
        self.reset_session()

        # Verify Concept was persisted as well
        retrieved_concept = db.session.query(Concept).filter_by(
            concept_id=object_concept.concept_id).first()
        self.assertIsNotNone(retrieved_concept, "Expected to find persisted Concept")

    def test_relationship__relationship_type_relation(self):
        """Verify relationship_type relation on Relationship.
        """
        rel_id = uuid.uuid4()
        rel_type = RelationshipType(relationship_type_id=uuid.uuid4(),
                                    relationship_type_name='is_{0}'.format(uuid.uuid4()))
        relationship = Relationship(relationship_id=rel_id,
                                    subject_id=uuid.uuid4(),
                                    object_id=uuid.uuid4(),
                                    relationship_type=rel_type)
        db.session.add(relationship)
        self.reset_session()

        # Verify Relationship was persisted
        retrieved_rel = db.session.query(Relationship).filter_by(relationship_id=rel_id).first()
        self.assertIsNotNone(retrieved_rel, "Expected to find persisted Relationship")
        self.assertEqual(rel_type.relationship_type_id, 
                         retrieved_rel.relationship_type_id)
        self.assertEqual(rel_type.relationship_type_id, 
                         retrieved_rel.relationship_type.relationship_type_id)
        self.assertEqual(rel_type.relationship_type_name,
                         retrieved_rel.relationship_type.relationship_type_name)
        self.reset_session()

        # Verify RelationshipType was persisted as well
        retrieved_rel_type = db.session.query(RelationshipType).filter_by(
            relationship_type_id=rel_type.relationship_type_id).first()
        self.assertIsNotNone(retrieved_rel_type, "Expected to find persisted RelationshipType")
        

class IncomingFactTests(FactModelTestCase):
    """Verify IncomingFact ORM.
    """
    def test_incoming_fact(self):
        """Verify creation with all non-nullable data.
        """
        utcnow = datetime.datetime.utcnow().replace(microsecond=0)
        fact_id = uuid.uuid4()
        fact_text = 'once upon a time {0}'.format(uuid.uuid4())
        parsed_fact = '{0} {1}'.format(fact_text, uuid.uuid4())
        incoming_fact = IncomingFact(fact_id=fact_id,
                                     fact_text=fact_text,
                                     parsed_fact=parsed_fact)
        db.session.add(incoming_fact)
        self.reset_session()

        retrieved_fact = db.session.query(IncomingFact).filter_by(fact_id=fact_id).first()

        self.assertIsNotNone(retrieved_fact, "Expected to find persisted IncomingFact")
        self.assertEqual(fact_id, retrieved_fact.fact_id)
        self.assertEqual(fact_text, retrieved_fact.fact_text)
        self.assertEqual(parsed_fact, retrieved_fact.parsed_fact)
        self.assertFalse(retrieved_fact.deleted)
        self.assertTrue(utcnow <= retrieved_fact.creation_date_utc)

    def test_incoming_fact__default_id(self):
        """Verify that fact_id is assigned when persisted.
        """
        fact_text = 'once upon a time {0}'.format(uuid.uuid4())
        incoming_fact = IncomingFact(fact_text=fact_text,
                                     parsed_fact=fact_text)
        db.session.add(incoming_fact)
        self.reset_session()

        retrieved_fact = db.session.query(IncomingFact).filter_by(fact_text=fact_text).first()

        self.assertIsNotNone(retrieved_fact, "Expected to find persisted IncomingFact")
        self.assertTrue(isinstance(retrieved_fact.fact_id, uuid.UUID))

    def test_incoming_fact__deleted(self):
        """Verify creation with deleted=True.
        """
        fact_id = uuid.uuid4()
        fact_text = 'once upon a time {0}'.format(uuid.uuid4())
        incoming_fact = IncomingFact(fact_id=fact_id,
                                     fact_text=fact_text,
                                     parsed_fact=fact_text,
                                     deleted=True)
        db.session.add(incoming_fact)
        self.reset_session()

        retrieved_fact = db.session.query(IncomingFact).filter_by(fact_id=fact_id).first()

        self.assertIsNotNone(retrieved_fact, "Expected to find persisted IncomingFact")
        self.assertTrue(retrieved_fact.deleted)

    def test_select_by_id(self):
        """Verify select_by_id method.
        """
        fact_id = uuid.uuid4()
        fact_text = 'once upon a time {0}'.format(uuid.uuid4())
        incoming_fact = IncomingFact(fact_id=fact_id,
                                     fact_text=fact_text,
                                     parsed_fact=fact_text)

        db.session.add(incoming_fact)
        self.reset_session()

        retrieved_fact = IncomingFact.select_by_id(fact_id)
        self.assertIsNotNone(retrieved_fact, "Expected to find persisted IncomingFact")
        self.assertEqual(fact_text, retrieved_fact.fact_text)

    def test_select_by_id__no_match(self):
        """Verify None returned if no match.
        """
        fact_id = uuid.uuid4()
        fact_text = 'once upon a time {0}'.format(uuid.uuid4())
        incoming_fact = IncomingFact(fact_id=fact_id,
                                     fact_text=fact_text,
                                     parsed_fact=fact_text)

        db.session.add(incoming_fact)
        self.reset_session()

        retrieved_fact = IncomingFact.select_by_id(uuid.uuid4())
        self.assertIsNone(retrieved_fact, "Expected not to find persisted IncomingFact")

    def test_select_by_text(self):
        """Verify select_by_text method.
        """
        fact_id = uuid.uuid4()
        fact_text = 'once upon a time {0}'.format(uuid.uuid4())
        incoming_fact = IncomingFact(fact_id=fact_id,
                                     fact_text=fact_text,
                                     parsed_fact=fact_text)

        db.session.add(incoming_fact)
        self.reset_session()

        retrieved_fact = IncomingFact.select_by_text(fact_text)
        self.assertIsNotNone(retrieved_fact, "Expected to find persisted IncomingFact")
        self.assertEqual(fact_id, retrieved_fact.fact_id)

    def test_select_by_text__no_match(self):
        """Verify None returned if no match.
        """
        fact_id = uuid.uuid4()
        fact_text = 'once upon a time {0}'.format(uuid.uuid4())
        incoming_fact = IncomingFact(fact_id=fact_id,
                                     fact_text=fact_text,
                                     parsed_fact=fact_text)

        db.session.add(incoming_fact)
        self.reset_session()

        retrieved_fact = IncomingFact.select_by_text('abracadabra')
        self.assertIsNone(retrieved_fact, "Expected not to find persisted IncomingFact")

