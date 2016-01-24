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
    def _get_concept(self, concept_name):
        """Return Concept with specified concept_name and, if new, arbitrary concept_id.
        """
        concept = db.session.query(Concept).filter_by(concept_name=concept_name).first()
        if not concept:
            concept = Concept(concept_name=concept_name, concept_id=uuid.uuid4())
        return concept
        
    def _get_relationship_type(self, relationship_type_name):
        """Return RelationshipType with specified name and, if new, arbitrary id.
        """
        rel_type = db.session.query(RelationshipType).filter_by(
            relationship_type_name=relationship_type_name).first()
        if not rel_type:
            rel_type = RelationshipType(relationship_type_id=uuid.uuid4(),
                                        relationship_type_name=relationship_type_name)
        return rel_type

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

    def test_relationship__default_id(self):
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

    def test_relationship__select_by_fact_id(self):
        """Verify select_by_fact_id method finds expected Relationships
        """
        rel_type_ids = [uuid.uuid4(), uuid.uuid4()]
        fact_id = uuid.uuid4()

        # Add two Relationships with fact_id
        for rel_type_id in rel_type_ids:
            db.session.add(Relationship(relationship_type_id=rel_type_id,
                                        subject_id=uuid.uuid4(),
                                        object_id=uuid.uuid4(),
                                        fact_id=fact_id))
            
        # Add another Relationship with a different fact_id
        db.session.add(Relationship(relationship_type_id=uuid.uuid4(),
                                    subject_id=uuid.uuid4(),
                                    object_id=uuid.uuid4(),
                                    fact_id=uuid.uuid4()))
        self.reset_session()

        retrieved_rels = Relationship.select_by_fact_id(fact_id)
        self.assertEqual(len(rel_type_ids), len(retrieved_rels))
        for rel in retrieved_rels:
            self.assertEqual(fact_id, rel.fact_id)

    def test_relationship__select_by_fact_id__no_match(self):
        """Verify select_by_fact_id method returns empty list if there is no match.
        """
        retrieved_rels = Relationship.select_by_fact_id(uuid.uuid4())
        self.assertEqual([], retrieved_rels)

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

        retrieved_rel = Relationship.select_by_foreign_keys(subject_id=subject_id, 
                                                            object_id=object_id,
                                                            relationship_type_id=rel_type_id)
        self.assertIsNotNone(retrieved_rel, "Expected to find persisted Relationship")
        self.assertEqual(rel_type_id, retrieved_rel.relationship_type_id)
        self.assertEqual(subject_id, retrieved_rel.subject_id)
        self.assertEqual(object_id, retrieved_rel.object_id)

    def test_relationship__select_by_foreign_keys__no_match(self):
        """Verify select_by_foreign_keys method returns None if there is no match.
        """
        retrieved_rel = Relationship.select_by_foreign_keys(subject_id=uuid.uuid4(),
                                                            object_id=uuid.uuid4(),
                                                            relationship_type_id=uuid.uuid4())
        self.assertIsNone(retrieved_rel, "Expected to not find persisted Relationship")

    def _setup_relationships(self):
        # Concepts and relationships
        high_heel = self._get_concept('high_heel')
        trainer = self._get_concept('trainer')
        shoe = self._get_concept('shoe')
        safety_hazard = self._get_concept('safety_hazard')
        is_relationship_type = self._get_relationship_type('is')
        kicks_relationship_type = self._get_relationship_type('kicks')

        # 'high_heel is shoe'
        high_heel_is_shoe_id = uuid.uuid4()
        relationship = Relationship(relationship_id=high_heel_is_shoe_id,
                                    subject=high_heel,
                                    object=shoe,
                                    relationship_types=[is_relationship_type])
        db.session.add(relationship)
        
        # 'high_heel is safety_hazard'
        high_heel_is_safety_hazard_id = uuid.uuid4()
        relationship = Relationship(relationship_id=high_heel_is_safety_hazard_id,
                                    subject=high_heel,
                                    object=safety_hazard,
                                    relationship_types=[is_relationship_type])
        db.session.add(relationship)

        # 'trainer is shoe'
        trainer_is_shoe_id = uuid.uuid4()
        relationship = Relationship(relationship_id=trainer_is_shoe_id,
                                    subject=trainer,
                                    object=shoe,
                                    relationship_types=[is_relationship_type])
        db.session.add(relationship)

        # 'high_heel kicks trainer'
        high_heel_kicks_trainer_id = uuid.uuid4()
        relationship = Relationship(relationship_id=high_heel_kicks_trainer_id,
                                    subject=high_heel,
                                    object=trainer,
                                    relationship_types=[kicks_relationship_type],
                                    count=3)
        db.session.add(relationship)
        self.reset_session()

    def test_relationship__select_by_values(self):
        """Verify select_by_values method.
        """
        self._setup_relationships()
        matches = Relationship.select_by_values(relationship_type_name='is',
                                                subject_name='high_heel',
                                                object_name='shoe')
        self.assertEqual(1, len(matches))
        rel = matches[0]
        self.assertTrue('is' in rel.relationship_type_names)
        self.assertEqual('high_heel', rel.subject.concept_name)
        self.assertEqual('shoe', rel.object.concept_name)

    def test_relationship__select_by_values__no_subject(self):
        """Verify select_by_values method with no subject name provided.
        """
        self._setup_relationships()
        matches = Relationship.select_by_values(relationship_type_name='is',
                                                object_name='shoe')
        self.assertEqual(2, len(matches))
        self.assertEqual(set(['high_heel', 'trainer']),
                         set([s.concept_name for s in [m.subject for m in matches]]))

    def test_relationship__select_by_values__no_object(self):
        """Verify select_by_values method with no object name provided.
        """
        self._setup_relationships()
        matches = Relationship.select_by_values(relationship_type_name='is',
                                                subject_name='high_heel')
        self.assertEqual(2, len(matches))
        self.assertEqual(set(['safety_hazard', 'shoe']), 
                         set([o.concept_name for o in [m.object for m in matches]]))

    def test_relationship__select_by_values__no_subject_or_object(self):
        """Verify select_by_values method with neither subject_name or object_name provided.
        """
        self._setup_relationships()
        matches = Relationship.select_by_values(relationship_type_name='is')
        self.assertTrue(len(matches) >= 3)
        subject_names = set([s.concept_name for s in [m.subject for m in matches]])
        object_names = set([o.concept_name for o in [m.object for m in matches]])
        self.assertTrue(subject_names.issuperset(set(['high_heel', 'trainer'])))
        self.assertTrue(object_names.issuperset(set(['safety_hazard', 'shoe'])))

    def test_relationship__select_by_values__relationship_number(self):
        """Verify select_by_values method when relationship_number is specified.
        """
        self._setup_relationships()
        matches = Relationship.select_by_values(relationship_type_name='kicks',
                                                relationship_number=3,
                                                subject_name='high_heel',
                                                object_name='trainer')
        self.assertEqual(1, len(matches))
        rel = matches[0]
        self.assertTrue('kicks' in rel.relationship_type_names)
        self.assertEqual(3, rel.count)
        self.assertEqual('high_heel', rel.subject.concept_name)
        self.assertEqual('trainer', rel.object.concept_name)

        # Verify that count is being matched by specifying different value
        matches = Relationship.select_by_values(relationship_type_name='kicks',
                                                relationship_number=13,
                                                subject_name='high_heel',
                                                object_name='trainer')
        self.assertEqual(0, len(matches))

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

    def test_relationship__relationship_types(self):
        """Verify relationship_types relation and relationship_type_names association proxy.
        """
        rel_id = uuid.uuid4()
        rel_type = RelationshipType(relationship_type_id=uuid.uuid4(),
                                    relationship_type_name='is_{0}'.format(uuid.uuid4()))
        relationship = Relationship(relationship_id=rel_id,
                                    subject_id=uuid.uuid4(),
                                    object_id=uuid.uuid4(),
                                    relationship_types=[rel_type])
        db.session.add(relationship)
        self.reset_session()

        # Verify Relationship was persisted
        retrieved_rel = db.session.query(Relationship).filter_by(relationship_id=rel_id).first()
        self.assertIsNotNone(retrieved_rel, "Expected to find persisted Relationship")
        self.assertEqual(rel_type.relationship_type_id, 
                         retrieved_rel.relationship_type_id)
        self.assertEqual(rel_type.relationship_type_id, 
                         retrieved_rel.relationship_types[0].relationship_type_id)
        self.assertEqual(rel_type.relationship_type_name,
                         retrieved_rel.relationship_types[0].relationship_type_name)
        self.assertEqual(rel_type.relationship_type_name, 
                         retrieved_rel.relationship_type_names[0])
        self.reset_session()

        # Verify RelationshipType was persisted as well
        retrieved_rel_type = db.session.query(RelationshipType).filter_by(
            relationship_type_id=rel_type.relationship_type_id).first()
        self.assertIsNotNone(retrieved_rel_type, "Expected to find persisted RelationshipType")

    def test_relationship__relationship_types__multiple(self):
        """Verify relationship_types and relationship_type_names with multiple matches.
        """
        rel_id = uuid.uuid4()
        rel_type_id = uuid.uuid4()
        rel_type_names = ['{0}_{1}'.format(n, uuid.uuid4()) 
                          for n in ['has', 'has a', 'hasa', 'have']]
        for name in rel_type_names:
            rel_type = RelationshipType(relationship_type_id=rel_type_id,
                                        relationship_type_name=name)
            db.session.add(rel_type)

        relationship = Relationship(relationship_id=rel_id,
                                    subject_id=uuid.uuid4(),
                                    object_id=uuid.uuid4(),
                                    relationship_type_id=rel_type_id)
        db.session.add(relationship)
        self.reset_session()

        # Verify RelationshipTypes were persisted
        retrieved_rel_types = db.session.query(RelationshipType).filter_by(
            relationship_type_id=rel_type_id).all()
        self.assertEqual(len(rel_type_names),
                         len(retrieved_rel_types), 
                         "Expected to find persisted RelationshipTypes")

        # Verify Relationship
        retrieved_rel = db.session.query(Relationship).filter_by(relationship_id=rel_id).first()
        self.assertEqual(len(retrieved_rel.relationship_types), len(rel_type_names))
        self.assertEqual(set(rel_type_names), set(retrieved_rel.relationship_type_names))

    def test_relationship__relationship_types__new_relationship_and_type(self):
        """Verify that new Relationship and RelationshipType does not delete existing match.
        """
        rel_id = uuid.uuid4()
        rel_type_id = uuid.uuid4()
        rel_type_names = ['{0}_{1}'.format(n, uuid.uuid4()) for n in ['is', 'isa']]
        relationship_types = [
            RelationshipType(relationship_type_id=rel_type_id,
                             relationship_type_name=name) for name in rel_type_names]

        # Save one RelationshipType and verify
        db.session.add(relationship_types[0])
        self.reset_session()
        rel_types = db.session.query(RelationshipType).filter_by(
            relationship_type_id=rel_type_id).all()
        self.assertEqual(1, len(rel_types))
        self.reset_session()

        # New Relationship with new RelationshipType with same relationship_type_id.
        relationship = Relationship(relationship_id=rel_id,
                                    subject_id=uuid.uuid4(),
                                    object_id=uuid.uuid4(),
                                    relationship_types=[relationship_types[1]])
        db.session.add(relationship)
        self.reset_session()

        # Verify both RelationshipTypes exist
        rel_types = db.session.query(RelationshipType).filter_by(
            relationship_type_id=rel_type_id).all()
        self.assertEqual(2, len(rel_types))
        self.reset_session()

        # Verify Relationship has both names
        retrieved_rel = db.session.query(Relationship).filter_by(relationship_id=rel_id).first()
        self.assertEqual(len(retrieved_rel.relationship_types), len(rel_type_names))
        self.assertEqual(set(rel_type_names), set(retrieved_rel.relationship_type_names))

    def test_delete_relationship(self):
        """Verify that deleting Relationship leaves Concepts and RelationshipType intact.
        """
        rel_id = uuid.uuid4()
        subject_concept = self._get_concept('flat')
        object_concept =  self._get_concept('shoe')
        rel_type = RelationshipType(relationship_type_id=uuid.uuid4(),
                                    relationship_type_name='is_{0}'.format(uuid.uuid4()))
        relationship = Relationship(relationship_id=rel_id,
                                    subject=subject_concept,
                                    object=object_concept,
                                    relationship_types=[rel_type])
        db.session.add(relationship)
        self.reset_session()

        # Verify Relationship, Concepts and RelationshipType
        retrieved_rel = db.session.query(Relationship).filter_by(relationship_id=rel_id).one()
        self.assertIsNotNone(retrieved_rel)
        self.assertIsNotNone(db.session.query(RelationshipType).filter_by(
                relationship_type_name=rel_type.relationship_type_name).one())
        self.assertIsNotNone(db.session.query(Concept).filter_by(
                concept_id=subject_concept.concept_id).one())
        self.assertIsNotNone(db.session.query(Concept).filter_by(
                concept_id=object_concept.concept_id).one())

        # Delete Relationship
        db.session.delete(retrieved_rel)
        self.reset_session()

        # Verify Relationship is gone
        self.assertIsNone(db.session.query(Relationship).filter_by(relationship_id=rel_id).first())

        # Verify Concepts and RelationshipType remain
        self.assertIsNotNone(db.session.query(RelationshipType).filter_by(
                relationship_type_name=rel_type.relationship_type_name).one())
        self.assertIsNotNone(db.session.query(Concept).filter_by(
                concept_id=subject_concept.concept_id).one())
        self.assertIsNotNone(db.session.query(Concept).filter_by(
                concept_id=object_concept.concept_id).one())

    def test_concept_types_relationship(self):
        """Test simple concept_types relationship: two concepts and one relationship.
        """
        rel_id = uuid.uuid4()
        subject_concept = self._get_concept('flat')
        object_concept =  self._get_concept('shoe')
        rel_type = self._get_relationship_type('is')
        relationship = Relationship(relationship_id=rel_id,
                                    subject=subject_concept,
                                    object=object_concept,
                                    relationship_types=[rel_type])
        db.session.add(relationship)
        self.reset_session()

        # select concept
        subject_concept = db.session.query(Concept).filter_by(
            concept_id=subject_concept.concept_id).first()
        self.assertIsNotNone(subject_concept)
        self.assertEqual(['shoe'], subject_concept.concept_types)
        self.assertEqual(object_concept.concept_id, 
                         subject_concept.concept_type_relationships[0].object.concept_id)

    def test_concept_types_relationship__multiple(self):
        """Test concept_types on one concept that is two different things.
        """
        high_heel = self._get_concept('high_heel')
        shoe =  self._get_concept('shoe')
        safety_hazard =  self._get_concept('safety_hazard')
        rel_type = self._get_relationship_type('is')
        relationship = Relationship(subject=high_heel,
                                    object=shoe,
                                    relationship_types=[rel_type])
        db.session.add(relationship)
        relationship = Relationship(subject=high_heel,
                                    object=safety_hazard,
                                    relationship_types=[rel_type])
        db.session.add(relationship)
        self.reset_session()

        # select concept
        high_heel = db.session.query(Concept).filter_by(concept_id=high_heel.concept_id).first()
        self.assertIsNotNone(high_heel)
        
        # check concept_types relationships
        self.assertEqual(set(['shoe', 'safety_hazard']), set(high_heel.concept_types))
        self.assertEqual(set([shoe.concept_id, safety_hazard.concept_id]),
                         set([r.object.concept_id for r in high_heel.concept_type_relationships]))


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


    
