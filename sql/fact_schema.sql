
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

-- 
-- insert known relationship type synonyms
--
INSERT INTO `relationship_types`
(`relationship_type_name`, `relationship_type_id`)
VALUES
-- is
('is',   'b93573ec-be70-4a2d-850b-4338ce75308f'),
('isa',  'b93573ec-be70-4a2d-850b-4338ce75308f'),
('is a', 'b93573ec-be70-4a2d-850b-4338ce75308f'),
('are', 'b93573ec-be70-4a2d-850b-4338ce75308f'),

-- eat
('eat',  'c1108ed8-fe18-4758-9d6e-4029de322407'),
('eats', 'c1108ed8-fe18-4758-9d6e-4029de322407'),

-- has
('has',    '17511629-f91b-4bcd-8c03-01ae1500c134'),
('hasa',   '17511629-f91b-4bcd-8c03-01ae1500c134'),
('has a',  '17511629-f91b-4bcd-8c03-01ae1500c134'),
('have',   '17511629-f91b-4bcd-8c03-01ae1500c134'),
('have a', '17511629-f91b-4bcd-8c03-01ae1500c134'),

-- lives
('lives',    '34d72b28-423c-4e7d-8a40-457031d5735b'),
('live',     '34d72b28-423c-4e7d-8a40-457031d5735b'),
('live in',  '34d72b28-423c-4e7d-8a40-457031d5735b'),
('lives in', '34d72b28-423c-4e7d-8a40-457031d5735b'),
('where', '34d72b28-423c-4e7d-8a40-457031d5735b')
;
