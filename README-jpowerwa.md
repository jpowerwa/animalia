# Animalia Implementation

## Data model

My goal was to build the animalia implementation with as little domain-specific knowledge as possible. The primary elements of the data model are Concepts and Relationships. A concept is a noun. A relationship associates two concepts: one subject and one object. The type of a relationship defines the nature of the association. A single relationship type is associated with a variety of names. For example, "is", "are", "is a" are all forms of a single relationship type. In the data model, all of these relationship type names have the same relationship type id. 

The data model DDL is defined in sql/fact_schema.sql. The fact_schema.sql script bootstraps the relationship names needed for animalia. The relationship_type table could be built up dynamically by determing a common representation of an incoming relationship type name. (Word stemming, says Thomas.) The fourth table in the schema, incoming_facts, exists to meet the API requirements to remember the syntax of an incoming fact and connect it to the relationship it described.

The ORM uses SQLAlchemy and is defined in fact_model.py. The FactModel depends on both Flask SQLAlchemy and SQLAlchemy itself. My inclination was to remove the dependency on the Flask SQLAlchemy, since the data model should not have anything to do with a web framework, but since this is an encapsulated exercise that I was attempting to not spend too much time on, I did not remove the dependency.


## Request flow

An incoming HTTP request arrives at the appropriate Flask handler defined in '__init__.py'. Defining handles in '__init__.py' seems to be a common pattern for a Flask app. After some basic request verification, the API layer calls the appropriate FactManager method. 


### FactManager

FactManager directly backs the API layer. The FactManager knows nothing about Flask or web requests. It deals with incoming fact and query sentences, fact ids, and concepts. For simple get and delete fact actions, the FactManager connects directly to FactModel, the ORM layer. To interpret an incoming fact or query sentence, the FactManager makes an HTTP request to the external wit.ai API and delegates to ParsedSentence to process the response. To create a new fact from a wit.ai API response, the FactManager uses the FactModel to create new ORM objects from the processed response. To answer a query, the FactManager delegates to the FactQuery class.


### ParsedSentence

ParsedSentence encapsulates the logic required to process wit.ai API responses. These responses are not as predictable as one might hope. One complexity is that the concepts in the responses are not normalized. For example, the data response for a fact with the subject "otter" may have "otter" as an identified entity, or it may have "otters." To handle this, ParsedSentence transforms all concepts into plural nouns on the way in. Though transforming the nouns to the singular form seems more natural, the answer to a question like "What does a bear eat?" seemed more natural with plural nouns, i.e. "berries, insects, salmon" than with singular nouns, i.e. "berry, insect, salmon." 

Sometimes the response to a valid sentence has a very low confidence. At one point, ParsedSentence raised if the confidence level on an outcome was below a configurable threshold, but even with a threshold as low as 0.5, the training data set could not be successfully processed. For example, the wit.ai response to "The bee has a stinger" has a confidence of 0.465, and the response to "The bee has wings" has a confidence of 0.265. Both facts are derived from the provided training data. To handle this, I changed the raised exception to a warning. If the parsed data is not valid, an application exception will be raised later on.

Sometimes the wit.ai response to a valid sentence is confusing enough that the data is rejected by the application. For example, wit.ai identifies the sentence "The cheetah is an animal" as a **which_animal_question**. In order to preserve the correctness of the persisted data, the application only accepts new facts that wit.ai identifies as fact intents. Unfortunately, as in the case described here, this strictness can result in an inability of the application to learn about new concepts.


### FactQuery

FactQuery is the most interesting class in the implementation. It takes a ParsedSentence and uses the intent provided by wit.ai to determine how to query the FactModel to answer the question. The FactQuery class is the only animalia component that uses domain specific logic. 

There are three fundamental types of queries:

The simplest, the **animal attribute query**, answers the question "Are subject and object related via the specified relationship type?" For example, "Does a bear eat salmon?" The subject can be an animal or species, and the object can be an animal, species, food, place, or body part. Sometimes the relationship is constrained by a count; e.g. "Does a bear have two legs?"

The second type of query is the **animal values query**. This query answers the question "What are the objects of relationships of the specified type with the specified subject?" For example, "What do bears eat?" Like the animal attribute query, the subject is an animal or species. 

The most complicated type of query, the **which animal query**, answers the question "What are the subjects of relationships of the specified type with the specified object?" For example, "Which animals eat salmon?" The object can be an animal, species, food, place or body part. The relationship may be qualified by count. Sometimes the results must be filtered by membership in a group, i.e. species. Sometimes the question is "What are the members of a group that do not have relationships of the specified type with the specified object?" To answer such a question, the set of all possible subjects must be selected and those subjects with expressed relationships removed from the returned set.

Some of the complexity of the FactQuery logic is introduced by the need to handle subjects and objects that can be members of a group, e.g. "coyote" and "river", or a group itself, e.g. "mammals" and "places." For simplification, the data model provides the notion of a "concept type." The types of a concept are those concepts related to the original concept by an "is" relationship. For example, a coyote is an animal and a mammal, so animal and mammal are both concept types of coyote. A concept can have distinct types. For example, a herring is sometimes a subject concept, i.e. "fish," and sometimes an object concept, i.e. "food." 

The FactQuery logic must also deal with the fuzziness of wit.ai response data. Queries often come back labeled as facts. For example, "Do otters live in trees?" is labeled as an **animal_place_fact** by wit.ai. FactQuery treats such queries as **animal_attribute_queries**, as observation suggests that is typically the correct type of query. 

Sometimes the wit.ai response data is fuzzy enough to result in incorrect answers. For example, the sentence "What do otters eat?" is properly identified by wit.ai as an **animal_eat_query**. FactQuery uses this information to respond to the question with a set of concept names: "fish, herrings [sic], salmon." Unfortunately, the sentence "Does the otter eat berries?" is also identified as an **animal_eat_query**, resulting in an answer that is a set of concept names instead of "yes" or "no." The very similar sentence, "Do otters eat berries?" is properly identified as an **animal_attribute_question**. 


### Exceptions

The API spec requires that the implemention handle certain errors: **fact not found**, **incoming fact parse error**, and **malformed query**. The implementation groups the latter two errors as IncomingDataErrors, an application-specific exception with multiple subclasses. An IncomingDataError may be raised by FactManager.fact_from_sentence, which backs the Add Fact API, or by FactManager.query_facts, which backs the Query Facts API. The API layer handles an IncomingDataError by responding with 400 Bad Request and the message "Failed to parse your fact"or "Failed to parse your question" as appropriate. The response also includes a "details" attribute with specifics about the type of error. 

The definition of a parse error is fuzzy, since wit.ai never refuses to parse a supplied sentence. If it does not understand anything about the provided text, it returns a response with a low confidence. For example, asking the wit.ai animalia instance "Can you hear me now?" returns a response with an animal_fur_fact intent and a confidence of 0.158. Since the confidence threshold enforcement was removed after the difficulties encountered with the bootstrap data, the validity of an incoming fact must be determined by application logic. 


## Helper scripts

### ask-wit.py 

The ask-wit.py script submits the provided sentence to wit.ai for parsing and displays the raw response. Its intended purpose is for experimentation.

### train.py

The train.py script processes the provided csv file of concepts and relationships and submits concepts and facts to FactManager. This script does not need the animalia web application to be running. Note that adding the training data can be slow, depending on the responsiveness of the external wit.ai service. I ran into trouble processing all of the provided training data as fact sentences; the wit.ai animalia instance is not set up to handle fact sentences categorizing concepts other than animals. For example, submitting the fact "A meadow is a place" interprets meadow as an animal and place as a species. Understandable, but inconvenient. To avoid this issue, train.py uses the FactManager.add_concept method. This method was introduced solely to support the data bootstrapping process. It does not rely on wit.ai.


## Modifications

### animalia.csv

I made some modifications to the training data provided in animalia.csv in the process of bootstrapping the training data and building the suite of query logic tests. First, I removed the entry for cormorants because the wit.ai animalia instance appears to have a typo. The wit.ai response to the sentence "a cormorant is a bird" returns the misspelled "coromorant" as the animal concept.

Second, I edited the gecko entry to specify reptile instead of mammal as the species.

Third, I added "wings" as a body part for heron and bee.

Fourth, I edited the bear entry to specify "salmon" instead of "fish" as a food. I did this to provide data to test the "Which animals eat fish?" query, which requires the selection of subjects with "eat" relationships directly to the species "fish" and subjects with "eat" relationships to members of the species "fish."

### check_animalia.bash

The curl command as generated by check_animalia.bash was failing in my environment due to quote mark problems. As a work-around, I updated the curl command in the create_fact, get_fact and query functions so that it did not require the substitution of the command as a variable.


## Web UI

The clumsy web UI is derived from an html page using bootstrap.js that came along with the dummy flask app that I cribbed to get started. This UI code is not suitable for review. If you look at it, you might cry. Despite its limitations, I found it useful for testing and debugging, so I left it in place. 


# Running Animalia Locally

## Requirements

1. mysql (http://dev.mysql.com/downloads/mysql/)
2. python 2.7 (https://www.python.org/download/releases/2.7/)
3. git (https://git-scm.com/downloads)
4. virtualenv (https://virtualenv.readthedocs.org/en/latest/installation.html)


## Preparation

1. go to preferred workspace directory
2. virtualenv venvs/animalia
3. source venvs/animalia/bin/activate
4. git clone git@github.com:/jpowerwa/animalia
5. pip install -r animalia/requirements.txt
6. start mysql
7. source animalia/sql/create_database.sql
8. source animalia/sql/fact_schema.sql


## Run unittests

Successful unittests indicate that animalia is set up properly.

1. start virtualenv (source venvs/animalia/bin/activate)
2. go to animalia directory
3. python -m unittest discover -s test -v


## Bootstrap training data

1. start mysql
2. source animalia/sql/fact_schema.sql
3. start virtualenv (source venvs/animalia/bin/activate)
4. go to animalia directory
5. python train.py ./training_data/animalia.csv [-v]


## Run query logic tests (these tests make requests to external wit.ai)

The query logic tests exercise the animalia query API. They are not unittests, as they rely on the external wit.ai service. The query logic tests depend on the bootstrapped training data. Like the training script, the tests use the animalia python code directly and do not need the animalia web application to be running.

1. bootstrap training data as described above
2. start virtualenv (source venvs/animalia/bin/activate)
3. go to animalia directory
4. python -m unittest -v test_query_logic.test_query_logic

## Run animalia app

The animalia app needs to be running for the APIs to be accessed. It has a very simple web front-end that allows you to add and query facts. There are instructions below on how to bootstrap data into the database if you want to do that before experimenting with the APIs.

1. start virtualenv (source venvs/animalia/bin/activate)
2. go to animalia directory
3. python run.py [h] [-p <PORT>] [-v]
4. go to http://localhost:8080


