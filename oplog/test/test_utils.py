# Copyright (c) 2011, Shutterstock Images LLC.
# All rights reserved.
#
# This file is subject to the MIT License (see the LICENSE file).

from twisted.internet import defer
from oplog import utils
from oplog.test import helper

class TestMongify(helper.TestCase):

    def test_clean(self):
        data = utils.mongify.encode({
            '_id': None,
            '_date': None,
            '_type': None,
            '_user': None,
            'summary': None,
        }, clean=True)
        # cleaned
        self.assertTrue('_id' not in data)
        self.assertTrue('_user' not in data)
        # not cleaned
        self.assertTrue('_date' in data)
        self.assertTrue('_type' in data)
        self.assertTrue('summary' in data)
