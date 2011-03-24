# Copyright (c) 2011, Shutterstock Images LLC.
# All rights reserved.
#
# This file is subject to the MIT License (see the LICENSE file).

import os
from twisted.internet import defer
from twisted.trial import unittest
import txmongo

class Settings(object):

    class general(object):
        profile = schema = ''

class MongoTestCase(unittest.TestCase):

    mongo_host = os.environ.get('OPLOG_TEST_MONGO_HOST', 'localhost')
    mongo_port = int(os.environ.get('OPLOG_TEST_MONGO_PORT', 27017))
    mongo_name = os.environ.get('OPLOG_TEST_MONGO_NAME', 'oplog_tests')
    timeout = 5

    @defer.inlineCallbacks
    def setUp(self):
        self.connection = yield txmongo.MongoConnection(self.mongo_host, self.mongo_port)
        self.db = self.connection[self.mongo_name]
        self.user = 'testuser'
        yield self.db.entry.drop(safe=True)

    @defer.inlineCallbacks
    def tearDown(self):
        yield self.connection.disconnect()

    @defer.inlineCallbacks
    def check_count(self, number, spec=None):
        count = yield self.db.entry.count(spec)
        self.assertEqual(count, number)

    def init(self, call, **kwargs):
        kwargs['user'] = kwargs.get('user', self.user)
        if 'settings' not in kwargs:
            kwargs['settings'] = Settings()
        kwargs['db'] = kwargs.get('db', self.db)
        return call(**kwargs)
