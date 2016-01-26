-- Create database for animalia app.
-- See fact_model.sql for table creation.

CREATE DATABASE IF NOT EXISTS animalia
default character set 'utf8' 
default collate 'utf8_general_ci';

create user 'animalia'@'localhost' identified by 'grrargh';
grant select, insert, delete, update on animalia.* to 'animalia'@'localhost';
