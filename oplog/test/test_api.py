# Copyright (c) 2011, Shutterstock Images LLC.
# All rights reserved.
#
# This file is subject to the MIT License (see the LICENSE file).

from twisted.internet import defer
from oplog import api
from oplog.test import helper

class TestEntry(helper.MongoTestCase):

    @defer.inlineCallbacks
    def test_del(self):
        handler = self.init(api.EntryDel)

        yield self.check_count(0)
        _id = yield self.db.entry.insert({'summary': 'test'})
        yield self.check_count(1)

        response = yield handler({'_id': str(_id)})

        # No errors
        self.assertEqual(response['result']['ok'], 1.0)
        self.assertEqual(response['result']['err'], None)
        # Wrote to at least one server
        self.assertGreaterEqual(response['result']['n'], 1)

        yield self.check_count(0)

    @defer.inlineCallbacks
    def test_get(self):
        handler = self.init(api.EntryGet)

        yield self.check_count(0)
        yield self.db.entry.insert([
            {'summary': 'test 1', 'hello1': 'world'},
            {'summary': 'test 2', 'hello2': 'world'},
            {'summary': 'test 3', 'hello3': 'world'},
            {'summary': 'test 4', 'hello4': 'world'},
            {'summary': 'test 5', 'hello5': 'world'},
        ])
        yield self.check_count(5)

        response = yield handler({
            'find': {'hello3': {'$ne': 'world'}},
            'skip': 1,
            'limit': 2,
            'sort': [['summary', 1]],
            'fields': ['summary', 'hello2']
        })

        # Check limit
        self.assertEqual(len(response['result']), 2)

        result1, result2 = response['result']

        # Check find, sort and skip
        self.assertEqual(result1['summary'], 'test 2')
        self.assertEqual(result2['summary'], 'test 4')

        # Check fields
        self.assertEqual(len(result1), 3)
        self.assertTrue('_id' in result1)
        self.assertTrue('summary' in result1)
        self.assertTrue('hello2' in result1)
        self.assertEqual(len(result2), 2)
        self.assertTrue('_id' in result2)
        self.assertTrue('summary' in result2)

    @defer.inlineCallbacks
    def test_put(self):
        handler = self.init(api.EntryPut)

        yield self.check_count(0)
        response1 = yield handler({
            'summary': 'hello world',
            '_type': 'test',
        })
        yield self.check_count(1)

        _id = response1['result']

        # Check result is id
        self.assertTrue(isinstance(_id, basestring))

        # Update existing entry
        response2 = yield handler({'_id': _id, '$set': {'summary': 'hello world2'}})

        # No errors
        self.assertEqual(response2['result']['ok'], 1.0)
        self.assertEqual(response2['result']['err'], None)
        # Wrote to at least one server
        self.assertGreaterEqual(response2['result']['n'], 1)

        # Still only one entry
        yield self.check_count(1)

        entry = yield self.db.entry.find_one({})

        # Found updated entry
        self.assertTrue(entry)
        # Data actually got updated
        self.assertEqual(str(entry['_id']), _id)
        self.assertEqual(entry['summary'], 'hello world2')
