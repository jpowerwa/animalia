-- MySQL dump 10.13  Distrib 5.5.46, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: animalia
-- ------------------------------------------------------
-- Server version       5.5.46-0ubuntu0.14.04.2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `concept_to_concept_type`
--

DROP TABLE IF EXISTS `concept_to_concept_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `concept_to_concept_type` (
  `concept_id` char(36) NOT NULL,
  `concept_type_id` char(36) NOT NULL,
  PRIMARY KEY (`concept_id`,`concept_type_id`),
  KEY `fk_concept_to_concept_type_concept_type_id_idx` (`concept_type_id`),
  CONSTRAINT `fk_concept_to_concept_type__concept_id` FOREIGN KEY (`concept_id`) REFERENCES `concepts` (`concept_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_concept_to_concept_type__concept_type_id` FOREIGN KEY (`concept_type_id`) REFERENCES `concept_types` (`concept_type_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `concept_types`
--

DROP TABLE IF EXISTS `concept_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `concept_types` (
  `concept_type_id` char(36) NOT NULL,
  `concept_type_name` varchar(255) NOT NULL,
  PRIMARY KEY (`concept_type_id`),
  UNIQUE KEY `concept_type_name_UNIQUE` (`concept_type_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `concepts`
--

DROP TABLE IF EXISTS `concepts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `concepts` (
  `concept_id` char(36) NOT NULL,
  `concept_name` varchar(255) NOT NULL,
  PRIMARY KEY (`concept_id`),
  UNIQUE KEY `concept_name_UNIQUE` (`concept_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `incoming_facts`
--

DROP TABLE IF EXISTS `incoming_facts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `incoming_facts` (
  `fact_id` char(36) NOT NULL,
  `fact_text` varchar(255) NOT NULL,
  `creation_date_utc` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `deleted` binary(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`fact_id`),
  UNIQUE KEY `fact_text_UNIQUE` (`fact_text`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `relationship_type_names`
--

DROP TABLE IF EXISTS `relationship_type_names`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `relationship_type_names` (
  `relationship_type_id` char(36) NOT NULL,
  `relationship_type_name` varchar(45) NOT NULL,
  PRIMARY KEY (`relationship_type_id`),
  UNIQUE KEY `relationship_type_name_UNIQUE` (`relationship_type_name`),
  CONSTRAINT `fk_relationship_type_names__relationship_type_id` FOREIGN KEY (`relationship_type_id`) REFERENCES `relationship_types` (`relationship_type_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `relationship_types`
--

DROP TABLE IF EXISTS `relationship_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `relationship_types` (
  `relationship_type_id` char(36) NOT NULL,
  `subject_type_id` char(36) NOT NULL,
  `object_type_id` char(36) NOT NULL,
  PRIMARY KEY (`relationship_type_id`),
  KEY `fk_relationship_types_subject_id_idx` (`subject_type_id`),
  KEY `fk_relationship_types_object_id_idx` (`object_type_id`),
  CONSTRAINT `fk_relationship_types_object_id` FOREIGN KEY (`object_type_id`) REFERENCES `concepts` (`concept_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_relationship_types_subject_id` FOREIGN KEY (`subject_type_id`) REFERENCES `concepts` (`concept_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `relationships`
--

DROP TABLE IF EXISTS `relationships`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `relationships` (
  `relationship_id` char(36) NOT NULL,
  `relationship_type_id` char(36) NOT NULL,
  `subject_id` char(36) NOT NULL,
  `object_id` char(36) NOT NULL,
  `count` int(11) DEFAULT NULL,
  `fact_id` char(36) DEFAULT NULL,
  PRIMARY KEY (`relationship_id`),
  KEY `fk_relationships_relationship_type_id_idx` (`relationship_type_id`),
  CONSTRAINT `fk_relationships__relationship_type_id` FOREIGN KEY (`relationship_type_id`) REFERENCES `relationship_types` (`relationship_type_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2015-12-26 15:04:40
