
DROP TABLE IF EXISTS `concepts`;
CREATE TABLE `concepts` (
  `concept_id` char(36) NOT NULL,
  `concept_name` varchar(255) NOT NULL,
  PRIMARY KEY (`concept_id`),
  UNIQUE KEY `concept_name_UNIQUE` (`concept_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `relationships`;
CREATE TABLE `relationships` (
  `relationship_id` char(36) NOT NULL,
  `relationship_type_id` char(36) NOT NULL,
  `subject_id` char(36) NOT NULL,
  `object_id` char(36) NOT NULL,
  `count` int(11) DEFAULT NULL,
  `fact_id` char(36) DEFAULT NULL,
  PRIMARY KEY (`relationship_id`),
  UNIQUE KEY `relationship_foreign_keys_UNIQUE` (`subject_id`, `object_id`, `relationship_type_id`),
  INDEX `ix_relationship_fact_id` (`fact_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `relationship_types`;
CREATE TABLE `relationship_types` (
  `relationship_type_name` varchar(45) NOT NULL,
  `relationship_type_id` char(36) NOT NULL,
  PRIMARY KEY (`relationship_type_name`),
  INDEX `ix_relationship_types_relationship_type_id` (`relationship_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `incoming_facts`;
CREATE TABLE `incoming_facts` (
  `fact_id` char(36) NOT NULL,
  `fact_text` varchar(255) NOT NULL,
  `parsed_fact` text NOT NULL,
  `creation_date_utc` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, 
  `deleted` boolean NOT NULL DEFAULT False,
  PRIMARY KEY (`fact_id`),
  UNIQUE KEY `fact_text_UNIQUE` (`fact_text`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;




