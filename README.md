# meditsvc

A RESTful service used for storing and finding entries in an openly shared journal.

## Install

Clone this project. Get your python and pip environment ready, and then just go to the project directory
and install flask and boto using:

```
pip install -r requirements.pip
```

## Configure Medit Service

By default, the meditsvc.ini file is used. New configurations are applied by setting the environment variable:

```
export MEDIT_INI = pathto/my.ini

```

## Configure AWS Credentials

The standard AWS config is used so if you haven't already done so, run the AWS client config or just set your environment variables or store your config as a text file:

```
cat ~/.aws/credentials
[default]
aws_access_key_id = <myid>
aws_secret_access_key = <mykey>
```

Or ...

```
aws configure
```

Or ...

```
export AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY
```

## Run

This is a flask application. It is started via the main method.

```
python meditsvc.py
```

## Data Anatomy

A post looks like this:

```json
{
"by": "luke",
"type": "pranhayana",
"head": "Great Day",
"body": "I had yet another good session!",
"at": 1420895424,
"date": "2015-01-10T13:10:24",
"id": "7079c392-8f40-40cc-b87b-89480d6b4a65"
}
```

Most properties are pretty easy to understand. Generated properties are not provided by the poster caller.

-by: the posts author
-type: a formal category
-head: subject
-body: content
-at: utc epoch when post was written (generated)
-date: human readable utc time post was written (generated)
-ctxt: data partition (generated)
-cliver: software that wrote message (generated)
-svcver: software that wrote message (generated)

# Data Validation

Any valid JSON posted with a body will be stored. Data that's too big won't be written:

-head: 512
-body: 4096
-by: 128
-type: 128
-total: 128

And the service will respond with a list of problems:

```
{"probs": ["big head", "big body"]}
```

## Get

You can get an existing post using its uuid. If you don't know the id of a post, you can find your post in a list (see below).

```
curl http://<host>:<port>/medit/<uuid>
```

And the service will return the post:

```
```

## List By Date

You can find posts by date using:

```
curl http://<host>:<port>/medits?beginat=utcepoch&endat=utcepoch
```

And the service will respond with an array of metadta about matching posts:

```
[{"id": "f306fb91-fb69-43bf-bcc1-aa1bbb97c871", "at": 1420848603}, {"id": "193a88be-82e8-47bf-a8d9-f829ec3cfc80", "at": 1420848786}]
```

## One-Step Find and Get

You can find posts by date using:

```
curl http://<host>:<port>/medits?beginat=utcepoch&endat=utcepoch&detail=true
```

And the service will respond with an array of complete posts:

```
[{"by": "luke", "type": "pranhayana", "head": "Great Day", "body": "I had yet another good session!", "at": 1420895424, "date": "2015-01-10T13:10:24", "id": "7079c392-8f40-40cc-b87b-89480d6b4a65"}]
```

## Post 

The restful service takes new messages via the following endpoint (where host and port match your environment).
A universal identifier (uuid) is assigned to posts as they're written. If you provide an identifier, it will be replaced.

```
curl -X POST -H 'Content-Type: application/json' -d '{"head":"and today","body":"I really had another good meditation!","by":"luke"}' http://localhost:5000/medit
```
And the service will respond with metadata about the post when it's been stored:
```
{"id": "7079c392-8f40-40cc-b87b-89480d6b4a65","at": 1420895424}
```
