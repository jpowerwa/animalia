# animalia

Welcome to animalia, Rafa's at-home interview question. The purpose of this exercise is for you to demonstrate your software development competency by implementing a web API that we will specify below. The animalia web API allows clients to "teach" the animalia service about animals, their characteristcs and relationships and to then ask the animalia service questions about animals. The interaction with the service uses a constrained form of natural language.

You will use an external service called [wit.ai][wit] to parse natural language input to the API implementation. We have trainined an instance of [wit.ai][wit] to help you with this task. We have also provided you with a set of training data that you can use to teach your implementation about the domain of animals.

[wit]: http://wit.ai/

# Submitting your Implementation

We expect two deliverables in your submission.

1. The source code.
2. A deployed service OR thorough instructions for building and running the service on a modern Mac laptop.

Your job is to write an implementation that satisfies the API specification and verify your implementation. You may use any implementation language you prefer.

### Submitting source code

To submit the source code, the easiest way is to share a private Github or BitBucket repository with us (we will send you the appropriate usernames). Alternatively, we can accept compressed tarballs or zip archives. We cannot accept those over email, though, so we recommend a file sharing service like Google Drive, Dropbox, or similar.

### Deployed service

It is easiest for us to evaluate the implementation if you deploy it somewhere. If you haven't done this before, [Heroku][heroku], [Google AppEngine][gae], [OpenShift][openshift], [Azure][azure], and similar services provide easy ways to deploy web services to the cloud often with free tiers. You can then send us a link to your deployed app.

If you are uncomfortable deploying your app, we will accept thorough instructions on how to setup and run your service as an alternative. We are experienced developers, but we may not be familiar with the tools or languages you used, so please draft the instructions accordingly.

[heroku]: https://heroku.com/
[gae]: https://cloud.google.com/appengine/docs
[openshift]: https://www.openshift.com/
[azure]: https://azure.microsoft.com/en-us/

### External Services and Libraries

Feel free to use whatever external services and libraries you feel are best suited to solve the problem. It is not neccessary to write the code for your solution from the ground up. You can use databases, utility libraries, or external web services as you see fit.

# Assessment and Interview

After we receive your submission we will conduct a code review and execute our suite of integration tests that assert the correctness of the API. Through the course of our review and testing we will assess your implementation on several different critiera:

* _Correctness:_ Does your API adhere to the specification and does it return correct or otherwise reaosnable results through the course of training and querying?
* _Robustness:_ Does your implementation handle malformed, edge case, or fuzzed input without failing and while returning meaningful messages on the cause of the failure?
* _Readability:_ Can an engineer unfamiliar with your implementation read and understand what you wrote with sufficient depth to make modifications? This criteria speaks to style, naming conventions, organization, and comments.
* _Scalability:_ If we were to scale the training data from its current form to 10s of thousands of animal concepts will your implementation be able to support the larger number of concepts without become unusably slow or otherwise broken.

On the day of your on-site interview you will present your solution to 2-3 members of the engineering team. You should prepare to talk about your implementation approach, design trade offs and approach to testing and validation. We will also ask you to run your test suite.

Through the course of the one-on-one interviews we will ask you further questions about how you would extend your service implementation and how you would fix any issues we find in our own testing to improve your solution.

# API Specification

The API is a HTTP/REST API. The document format is JSON, with a Content Type of `application/json`.

## Training API

You "train" your service by sending sentences to the service in a particular format. The training sentences have the abstract form of: `article animal relationship concept`. For example: "the otter lives in rivers". In that example the article is "the", the animal is "otter", the semantic clause is "lives in", and the concept is "rivers".

Training is done by submitting a HTTP POST to the to the /animals/facts resource with a JSON encoded body that contains a single sentence in a JSON object with the field name of: "fact". An example JSON body would therefore look like this:

 `{
 "fact": "the otter lives in rivers"
}`    

If the POST completed succesfully the API will return a HTTP 200 status code with a JSON formatted body that contains an identifier for the newly created fact. The response document will look like this:


 `{
 "id": "0b3431e3-2351-46f1-ad90-fa022a60ba15"
}`

The id is a globaly unique identifier (GUID).

You can submit the exact same sentence repeatedly and the service will be trained in the exact same way as a result and will return the exact same identifier.

Sentences that cannot be parsed by the service because they do not follow the expected form will result in a HTTP 400 status code and a error message detailing that the parse attempt has failed. The error message will also be in a JSON format and will look as follows:

 `{
 "message": "Failed to parse your fact"
}`

## Fact Management API

Individidual facts can be retrieved using an HTTP GET on the '/animals/facts/' resource using the GUID to specify the target fact:

`
GET /animals/facts/0b3431e3-2351-46f1-ad90-fa022a60ba15  HTTP/1.1
`

If a fact with the specified id is known to the service it is returned with a 200 status code and a response document that looks like this:

 `{
 "fact": "the otter lives in rivers"
}` 

IF a fact with the specified id is not present then the response will have a 404 status code and response body will be empty.

Individual facts can also be deleted. To delete a fact the client can issue an HTTP DELETE and specify the GUID of the fact to delete like this:

`
DELETE /animals/facts/0b3431e3-2351-46f1-ad90-fa022a60ba15  HTTP/1.1
`

If a fact with the specified GUID exists then it will be deleted and the response will have a status code of 200 and have a response body with the id of the fact that was deleted. This response document should look as follows:

 `{
 "id": "0b3431e3-2351-46f1-ad90-fa022a60ba15"
}`

If a fact with the specifeid GUID could not be found then the service will return a response with a 404 status code and no response body.

When a fact is deleted then the information it represents about animals is no longer available to the service and the servie must stop answering questions with information from the fact.

## Query API

You query the API about the semantic relationships of animals. A query is submitted as a sentence in specific form that follows one of the following patterns:

* "Where does the otter live?"
* "How many legs does the otter have"?
* "Which animals have 4 legs?"
* "How many animals are mammals?"

A query is submitted by sending a HTTP GET to the /animals resource with a URL parameter with the key 'q'. For example:

`
GET /animals?q="where does the otter live?" HTTP/1.1
`

The service will respond with a 200 status code and the same JSON body as is used to train the API. For example:

`{
 "fact": "rivers"
}`

If the API cannot find information that is related to the query, it will return a 404 status code and a slighlty different JSON body:

`{
 "message": "I can't answer your question."
}`

If the request is malformed then the API will return a HTTP 400 status code.

# Training Data

We have provided training data for this project that comes in the form of a CSV file. The CSV has one row per trainable concept with the following columns:

* _concept:_ The name of the concept. For example: 'otter' or 'river'
* _type:_ The type of the concept. One of: `animal`,`place`,`number`,`body part`,`food`,`species`
* _lives:_ A semantic relationship that defines where the animal lives. The values can be empty or any concept that is a place type.
* _has body part:_ A semantic relationship that defines the body parts of the animal. The values can be empty any concept which has the body part type.
* _has fur:_ A semantic relationship that defines if the animal has fur or not. The values can be `true`, `false`, or empty.
* _has scales:_ A semantic relationship that defines if the animal has scales or not. The values can be `true`, `false`, or empty.
* _eats:_ A semantic relationship that defines what the animal eats. The values can be empty or any concept which is food.
* _parent species:_ A semantic relationship that defines the parent species of the animal or species. The values can be a species or empty.
* _leg count:_ A semantic relationship that defines if the number of legs an animal has. The values can be a number or empty.

# Example Queries

Your implementation will need to be able to handle queries that are simple lookups of attributes, aggregations of animals or counts with common features, and queries that require inference. Some example questions are:

* How many animals have fins?
* Which animals eat berries?
* Which animals eat mammals?
* How many animals do not eat berries?
* Does a bear have scales?
* Do mammals live in the ocean?

The responses are simple yes or no, numbers or lists. The responses do not need to be formed into sentences. So the responses to the above questions would be:

* How many animals have fins? 2
* Which animals eat berries? bears, coyotes, and deer.
* Which animals eat mammals? coyotes and bears
* How many animals do not eat berries? 5
* Does a bear have scales? no
* Do mammals live in the ocean? yes

# Use of [wit.ai][wit]

A succesful implementation will make use of [wit.ai][wit] to parse the training sentences and extract the parts required to populated the service's collection of facts so it can later answer questions. We have provided a trained [wit.ai][wit] application for you to use in your application. The trained [wit.ai][wit] instance will allow you to identify the intent of questions and of fact statements along with the features or entities in statements, including animals, semantic relationships and features. You can use an existing [wit.ai][wit] integration library or use their HTTP API directly. Be sure to handle error cases in your [wit.ai][wit] integration as a part of your implementation.

The wit API Key to use is `JZKCMFUAZKZ5FQZT3JXEZVJM2XVNNPXI` the app id is: `56300313-4dfd-4da3-a74d-2ae701d1cfbb`. The wit API key we provide will allow you to use a wit integration library or an integration your write yourself to extract the intents and entities on which we have trained so you can understand more about the set of possible values.

Our training of wit is not perfect. If you find that there are query or fact intents that we have not covered in our training let us know via e-mail. We will do our best to annotate the examples you sent to wit that have failed. Wit will record all of the facts questions you send to it, so we can find any queries that failed to parse and annotate them.

## Expectations

There are lots of intents defined in wit. We do not expect your solution to support all of them. We expect you to be able to talk about how you would support additional intents, however.
