# animalia

## Thoughts about implementation

My goal was to build the animalia implementation with as little domain-specific knowledge as possible. Of the python code, only animalia.fact_query uses domain specific logic. The database schema and the animalia modules fact_manager and parsed_sentence are domain agnostic. 

The clumsy but useful UI is derived from an html page using bootstrap.js that came along with the dummy flask app that I cribbed to get started. This UI code is not suitable for review. If you look at it, you might cry. 


## How to run animalia locally

### Requirements

1. mysql (http://dev.mysql.com/downloads/mysql/)
2. python 2.7 (https://www.python.org/download/releases/2.7/)
3. git (https://git-scm.com/downloads)
4. virtualenv (https://virtualenv.readthedocs.org/en/latest/installation.html)


### Preparation

1. go to preferred workspace directory
2. virtualenv venvs/animalia
3. source venvs/animalia/bin/activate
4. git clone git@github.com:/jpowerwa/animalia
5. pip install -r animalia/requirements.txt
6. sudo apt-get install -y libsox-dev
7. start mysql
8. source animalia/sql/create_database.sql
9. source animalia/sql/fact_schema.sql


### To run unittests

Successful unittests indicate that animalia is set up properly.

1. start virtualenv (source venvs/animalia/bin/activate)
2. go to animalia directory
3. python -m unittest discover -s test -v


### To run animalia app

The animalia app needs to be running for the APIs to be accessed. It has a very simple web front-end that allows you to add and query facts. There are instructions below on how to bootstrap data into the database if you want to do that before experimenting with the APIs.

1. start virtualenv (source venvs/animalia/bin/activate)
2. go to animalia directory
3. python run.py [h] [-p <PORT>] [-v]
4. go to http://localhost:8080


### To bootstrap training data

There is a script that builds fact sentences from the animalia training data csv file and adds them to the animalia database. This script uses the animalia python code directly and does not need the animalia web application to be running. Note that adding the training data can be slow, depending on the responsiveness of the external wit.ai service.

1. start mysql
2. source animalia/sql/fact_schema.sql
3. start virtualenv (source venvs/animalia/bin/activate)
4. go to animalia directory
5. python train.py ./training_data/animalia.csv [-v]


### To run query logic tests (these tests make requests to external wit.ai)

The query logic tests exercise the animalia query API. They are not unittests, as they rely on the external wit.ai service. The query logic tests depend on the bootstrapped training data. Like the training script, the tests use the animalia python code directly and do not need the animalia web application to be running.

1. bootstrap training data as described above
2. start virtualenv (source venvs/animalia/bin/activate)
3. go to animalia directory
4. python -m unittest -v test_query_logic.test_query_logic

