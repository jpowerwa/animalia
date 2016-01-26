# animalia

## Thoughts about implementation

My goal was to build the animalia implementation with as little domain-specific knowledge as possible. Of the python code, only animalia.fact_query uses domain specific logic. The database schema and the animalia modules fact_manager and parsed_sentence are domain agnostic. 

One implementation detail that I do not like is handling of singular and plural versions of nouns. First off, the logic to generate a singular and plural version of a noun is clearly flawed, but it suffices for now. Moreover, I do not like needing to do multiple queries to handle the singular and plural versions of concept names, as this results in extra database trips and queries. I would prefer to transform the concept names before adding records to the database. Since that is how I would optimize the code, I did not make the fact_model.Relationship.select_by_values method take lists of subject and object names, which would at least push the work onto the database.

Fixing the above implementation detail would probably be required for this solution to be scalable.


## How to run animalia locally

### Preparation

1. create virtualenv
2. git clone 
3. start virtualenv
4. sudo apt-get install libsox-dev
5. pip install wit, flask, flask-mysql, flask-sqlalchemy, flask-api, mock
6. start virtualenv
7. if necessary, sudo apt-get install mysql-server, mysql-client
8. in mysql, source sql/create_database.sql and sql/fact_model.sql


### To run unittests

1. start virtualenv
2. change to animalia directory
3. python -m unittest discover -s test -v

### To bootstrap training data

1. start virtualenv
2. in mysql, source sql/fact_schema.sql to clear database
3. change to animalia directory
4. python train.py ./training_data/animalia.csv [-v]


### To run query logic tests (these tests make requests to external wit.ai)

1. start virtualenv
2. change to animalia directory
3. source sql/fact_schema.sql to clear database
4. bootstrap training data as described above
5. python -m unittest -v test_query_logic.test_query_logic


### To run animalia app

1. start virtualenv
2. change to animalia directory
3. python run.py [h] [-p <PORT>] [-v]


## The inelegant UI 

Once the animalia flask app is running, a very basic front-end for experimenting with the animalia API is available at http://localhost:8080.

This front-end is derived from an html page using bootstrap.js that came along with the dummy flask app that I cribbed to get started. This UI code is not suitable for review. If you look at it, you might cry. 


