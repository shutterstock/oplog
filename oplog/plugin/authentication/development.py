# Copyright (c) 2011, Shutterstock Images LLC.
# All rights reserved.
#
# This file is subject to the MIT License (see the LICENSE file).

from twisted.internet import defer
from oplog.plugin import authentication

class Authentication(authentication.Base):

    def valid(self, username, password):
        return defer.succeed(username == password)

def register(settings, *args, **kwargs):
    return Authentication(settings)
