oplog
=====

oplog is an operations log.

### API Requests and Responses

Entry get request:

    {
        "method": "entry.get",
        "params": {
            "find": {"_user": "ssewell"},
            "sort": [["_date, -1], ["summary", 1]],
            "skip": 20,
            "limit": 20,
            "fields": ["_id", "_date", "_type", "_user", "summary"]
        }
    }

Entry get response:

    {
        "result": [
            {
                "_id": "4d433c461f48517114000000",
                "_date": "2011-01-28T21:59:34Z",
                "_type": "user",
                "_user": "ssewell",
                "summary": "hello world 4"
            },
            {
                "_id": "4d433bf51f485170d3000000",
                "_date": "2011-01-28T21:58:13Z",
                "_type": "user",
                "_user": "ssewell",
                "summary": "hello world 3"
            },
            {
                "_id": "4d433b591f48517079000000",
                "_date": "2011-01-28T21:55:37Z",
                "_type": "user",
                "_user": "ssewell",
                "summary": "hello world 2"
            }
        ]
    }

Entry put request:

    {
        "method": "entry.put",
        "params": {
            "_date": "2011-02-01T20:55:13Z",
            "_type": "todo.deploy",
            "summary": "API test"
        }
    }

Entry put response:

    {
        "result": "4d482f9f1f48510c71000000"
    }

### Example Requests

    export API_URL='http://localhost:8000/api?app=mytest&key=783f9731-7a41-4422-b1f2-ad678dd8a5d3'

    # Get list of entries
    curl -d '{"method": "entry.get", "params": {"find": {}, "sort": [["_date", -1]], "skip": 2, "limit": 3}}' "$API_URL"

    # Add new entry
    curl -d '{"method": "entry.put", "params": {"summary": "API test"}}' "$API_URL"

### Requirements

* Python >= 2.6
* [huck](http://pypi.python.org/pypi/huck)
* [ops](http://pypi.python.org/pypi/ops)
* [txldap](http://pypi.python.org/pypi/txldap)
* [txmongo](http://pypi.python.org/pypi/txmongo)
* [txsetup](http://pypi.python.org/pypi/txsetup) (install)
* [validictory](http://pypi.python.org/pypi/validictory)

### Licenses

This work is licensed under the MIT License (see the LICENSE file).
